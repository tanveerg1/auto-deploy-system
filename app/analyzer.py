import os
import sys
import re
import tempfile
import zipfile
import git
import shutil
import asyncio
import io
import stat
from pathlib import Path
from uuid import uuid4

# Fixes the PermissionError: [WinError 5] Access is denied on Windows
def _on_rm_error(func, path, exc_info):
    # Attempt to make file writable and retry (fixes WinError 5 on Windows)
    try:
        os.chmod(path, stat.S_IWRITE)
    except Exception:
        pass
    try:
        func(path)
    except Exception:
        pass

# Clones or unzips the project
async def clone_or_unzip(repo_url=None, zip_file=None) -> str:
    print(f'[INFO] REPOSITORY URL {repo_url}')
    temp_dir = tempfile.mkdtemp()
    print(f'[INFO] TEMP DIR {temp_dir}')
    if repo_url:
        print(f'[INFO] trying to clone {repo_url} into {temp_dir}')
        try:
            git.Repo.clone_from(repo_url, temp_dir)
        except Exception as e:
            print('[ERROR] did not clone')
    elif zip_file:
        print(f'[DEBUG] IN ZIPFILE {zip_file.filename}')
        
        zip_data = await zip_file.read()
        byte_data = io.BytesIO(zip_data)

        with zipfile.ZipFile(byte_data, 'r') as zip:
            zip.printdir()
            zip.extractall(temp_dir)
        await zip_file.close()
        # try:
        #     zip_file.file.seek(0)
        #     # data = zip_file.file.read()
        #     # bio = io.BytesIO(data)
        #     bio = zip_file.file
        #     print(bio)
        #     with zipfile.ZipFile(bio, 'r') as zip_ref:
        #         # zip_ref.printdir()
        #         zip_ref.extractall(temp_dir)
        # except Exception as e:
        #     print(e)
            # shutil.rmtree(temp_dir, onerror=_on_rm_error)
            # raise RuntimeError("Failed to read uploaded zip file") from e
        # bio = zip_file.file
        
    return temp_dir

# async def clone_or_unzip(repo_url=None, zip_file=None) -> str:
#     # return await asyncio.to_thread(_clone_or_unzip_sync, repo_url, zip_file)
#     loop = asyncio.get_running_loop()
#     return await loop.run_in_executor(None, _clone_or_unzip_sync, repo_url, zip_file)


# Analysis of the repo or zip file
async def analyze_repo(repo_url=None, zip_file=None):
    repo_path = await clone_or_unzip(repo_url, zip_file)
    print(f'[INFO] REPOSITORY PATH {repo_path}')

    # copy repo to a persistent workspace so terraform/local-exec can read/write Dockerfile, etc.
    keep_workspace = os.getenv("KEEP_WORKSPACE", "1") == "1"
    workspace_root = Path(__file__).resolve().parent.parent / "workspaces"
    workspace_root.mkdir(parents=True, exist_ok=True)
    workspace_dest = workspace_root / uuid4().hex
    try:
        shutil.copytree(repo_path, workspace_dest)
        print(f"[INFO] copied repo to workspace {workspace_dest}")
    except Exception as e:
        print(f"[WARN] copying repo to workspace failed: {e!r}")
        # continue — workspace won't be available
        workspace_dest = None

    metadata = {
        "repo_url": None,
        "language": None,
        "start_command": None,
        "exposed_port": None,
        "env_vars": [],
        "dockerfile": False,
        "workspace_dest": str(workspace_dest)
    }

    try:
        metadata["repo_url"] = f"{repo_url}"
        search_root = str(workspace_dest) if workspace_dest else repo_path

        for root, _, files in os.walk(search_root):
            for file in files:
                full_path = os.path.join(root, file)

                # Language Detection
                if file == "package.json" and metadata["language"] is None:
                    metadata["language"] = "nodejs"
                    metadata["start_command"] = "npm start"
                elif file == "requirements.txt" and metadata["language"] is None:
                    metadata["language"] = "python"
                    metadata["start_command"] = "python app.py"
                elif file == "pom.xml" and metadata["language"] is None:
                    metadata["language"] = "java"
                    metadata["start_command"] = "mvn spring-boot:run"
                
                # Check for Dockerfile
                if file == "Dockerfile":
                    metadata["dockerfile"] = True
                
                # collect .env lines
                if file == ".env":
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            metadata["env_vars"].extend([line.strip() for line in f if "=" in line])
                    except Exception:
                        pass

                if file.endswith(".js") or file.endswith(".py"):
                    with open(full_path) as f:
                        content = f.read()

                        # Detect exposed port
                        if "port" in content:
                            match = re.search(r"port\s*=\s*(\d+)", content)
                            if match:
                                metadata["exposed_port"] = match.group(1)
        return metadata
    except Exception as e:
        print(e)
    finally:
        # remove the original temp repo copy (repo_path). keep the workspace copy if KEEP_WORKSPACE=1
        try:
            shutil.rmtree(repo_path, onerror=_on_rm_error)
        except Exception:
            pass

        if not keep_workspace and workspace_dest:
            try:
                shutil.rmtree(workspace_dest, onerror=_on_rm_error)
            except Exception:
                pass
        # print('done')