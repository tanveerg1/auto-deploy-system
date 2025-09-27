import textwrap
import os
import zipfile
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parent / "tf_templates"

def _load_template(fname: str) -> str:
    path = TEMPLATES_DIR / fname
    if path.exists():
        return path.read_text(encoding="utf-8")
    # fallback minimal inline template
    return f"# missing template {fname}\n"

def _render_from_file(template_name: str, tf_name: str, port: int) -> str:
    tpl = _load_template(template_name)
    return tpl.replace("__TF_NAME__", tf_name).replace("__PORT__", str(port))

def _render_aws_ec2(tf_name, port):
    return _render_from_file("aws_flask_template.tf", tf_name, port)

def _render_aws_serverless(tf_name, port):
    return _render_from_file("aws_lambda_template.tf", tf_name, port)

def _render_aws_ecs(tf_name, port):
    return _render_from_file("aws_ecr_template.tf", tf_name, port)

def _render_gcp(tf_name, port):
    return _render_from_file("gcp_flask_template.tf", tf_name, port)

def _render_azure(tf_name, port):
    return _render_from_file("azure_flask_template.tf", tf_name, port)


# def choose_template(intent, repo_data):
#     runtime = intent.get("runtime")
#     containerized = intent.get("containerized")
#     cloud_provider = intent.get("cloud_provider")
#     database = intent.get("database")

#     if repo_data.get("dockerfile") is True and cloud_provider is "aws":
#         return "aws_ecr_template.tf"
#     if cloud_provider is "aws":
#         return "aws_flask_template.tf"
#     if cloud_provider is "gcp":
#         return "gcp_flask_template.tf"
#     if cloud_provider is "azure":
#         return "azure_flask_template.tf"
#     return "aws_flask_template.tf"
def zip_workspace(workspace_dest, output_zip="archive.zip"):
    output_zip_path = os.path.abspath(output_zip)
    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(workspace_dest):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, workspace_dest)
                zipf.write(file_path, arcname)
    print(f"Zipped workspace to {output_zip_path}")
    return output_zip_path

def generate_infra(intent: dict, repo_data: dict) -> dict:
    tf_name = intent.get("name", "app").replace(" ", "-").lower()
    port = repo_data.get("exposed_port") or intent.get("port") or 80
    repo_url = repo_data.get("repo_url")
    cloud_provider = intent.get("cloud_provider")
    strategy = intent.get("strategy")
    workspace_dest = repo_data.get("workspace_dest")
    description = f"Suggested provider: {cloud_provider.upper()}. Will deploy a web service exposing port {port}."

    if cloud_provider == "aws":
        prefer_ec2 = (repo_data.get("language") or "").lower() == "python" and not repo_data.get("dockerfile") and strategy is not "serverless"
        if prefer_ec2:
            tf = _render_aws_ec2(tf_name, port)
            prompts = [
                {"name": "aws_region", "label": "AWS region", "default": "us-east-1", "type": "string"},
                {"name": "instance_type", "label": "EC2 instance type", "default": "t3.micro", "type": "string"},
                {"name": "repo_url", "label": "Git repo URL (optional — EC2 will clone and run)", "default": f"{repo_url}", "type": "string"}
            ]
        elif strategy == "serverless":
            tf = _render_aws_serverless(tf_name, port)
            zip_path = zip_workspace(workspace_dest)

            prompts = [
                {"name": "aws_region", "label": "AWS region", "default": "us-east-1", "type": "string"},
                {"name": "lambda_zip_path", "label": "lambda_zip_path", "default": f"{zip_path}", "type": "string"},
            ]
        else:
            tf = _render_aws_ecs(tf_name, port)
            prompts = [
                {"name": "aws_region", "label": "AWS region", "default": "us-east-1", "type": "string"},
            ]
    elif cloud_provider == "gcp":
        tf = _render_gcp(tf_name, port)
        prompts = [
            {"name": "gcp_project", "label": "GCP project id", "default": "", "type": "string"},
            {"name": "gcp_region", "label": "GCP region", "default": "us-central1", "type": "string"},
        ]
    else:
        tf = _render_azure(tf_name, port)
        prompts = [
            {"name": "location", "label": "Azure location", "default": "East US", "type": "string"},
        ]

    return {
        "provider": cloud_provider,
        "description": description,
        "terraform": tf,
        "prompts": prompts,
    }