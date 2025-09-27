import subprocess
import tempfile
import os
import json
import boto3
import zipfile
from typing import Dict, Any, Optional

def _on_rm_error(func, path, exc_info):
    try:
        os.chmod(path, stat.S_IWRITE)
    except Exception:
        pass
    try:
        func(path)
    except Exception:
        pass

def generate_tfvars(prompts, tf_dir, output_path="terraform.tfvars.json"):
    tfvars = {}

    for prompt in prompts:
        name = prompt.get("name")
        default = prompt.get("default")

        if isinstance(default, bool):
            default = str(default).lower()

        tfvars[name] = default
    tfvars_path = os.path.join(tf_dir, output_path)
    with open(tfvars_path, "w") as f:
        json.dump(tfvars, f, indent=2)

    print(f"Terraform variables written to {output_path}")

def deploy_app(infra_data: dict) -> dict:

    tf_dir = tempfile.mkdtemp(prefix="prj-tf-")

    try:
        
        main_tf = infra_data.get("terraform", "")
        with open(os.path.join(tf_dir, "main.tf"), "w", encoding="utf-8") as file:
            file.write(main_tf)
    
        # write terraform.tfvars.json
        generate_tfvars(infra_data.get("prompts"), tf_dir)

        # run terraform init/apply capturing output
        try:
            subprocess.run(["terraform", "init"], cwd=tf_dir, check=True)
        except FileNotFoundError:
            return {"success": False, "message": "terraform executable not found on PATH", "terraform_dir": tf_dir}
        except subprocess.CalledProcessError as e:
            return {"success": False, "message": "terraform init failed", "error": e.stderr or e.stdout or str(e), "terraform_dir": tf_dir}

        try:
            subprocess.run(["terraform", "apply", "-auto-approve"], cwd=tf_dir, check=True)
        except subprocess.CalledProcessError as e:
            return {"success": False, "message": "terraform apply failed", "error": e.stderr or e.stdout or str(e), "terraform_dir": tf_dir}
        
        

        # Extract public IP
        output = subprocess.check_output(["terraform", "output", "-json"], cwd=tf_dir)
        # public_ip = eval(output.decode())["public_ip"]["value"]
        try:
            outputs = json.loads(output.decode())
        except Exception:
            outputs = {}
        print("[DEBUG] terraform outputs:", outputs)

        public_ip = None
        possible_keys = ("public_ip", "instance_public_ip", "instance_ip", "app_instance_public_ip")
        for key in possible_keys:
            if key in outputs:
                v = outputs[key]
                public_ip = v.get("value") if isinstance(v, dict) and "value" in v else v
                break

        # normalize simple dict values to plain strings
        if isinstance(public_ip, dict) and "value" in public_ip:
            public_ip = public_ip["value"]
 
        return {
            "message": "Deployment successful",
            "public_ip": public_ip,
            "outputs": outputs
        }

    except subprocess.CalledProcessError as e:
        return {
            "message": "Deployment failed",
            "error": str(e)
        }