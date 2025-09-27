# ChatSystem — Auto Deploy System

This repository contains a small automation service that analyzes a repository and generates/apply Terraform templates to deploy simple web apps (EC2, ECS/ECR, Cloud Run, App Service, or Lambda+API Gateway). See the `app/` folder for the core code and `app/tf_templates/` for Terraform templates.

Getting started (short)
1. Install system tools:
   - Terraform: https://www.terraform.io/downloads
   - AWS CLI (if using AWS): https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
2. Create a Python venv and install requirements:
   - python -m venv .venv
   - .venv\Scripts\activate
   - pip install -r requirements.txt
3. Add the respective credentionals for AWS, GCP and Azure in your CLI before running this API
4. Run the FastAPI server (dev):
   - uvicorn app.main:app --reload
5. Use the UI or API to analyze a repo and generate/apply Terraform. See `app/tf_templates/` for the templates used.

Sources & dependencies (proper citations)
- Terraform
  - HashiCorp Terraform — https://www.terraform.io/ (required to run generated templates)
- AWS
  - AWS CLI — https://docs.aws.amazon.com/cli/
  - AWS SSM / IAM / EC2 / ECR / ECS docs where applicable — https://docs.aws.amazon.com/
- Python packages (listed in `requirements.txt`)
  - FastAPI — https://fastapi.tiangolo.com/ (API framework)
  - Uvicorn — https://www.uvicorn.org/ (ASGI server)
  - boto3 — https://boto3.amazonaws.com/v1/documentation/api/latest/index.html (AWS SDK for Python)
  - GitPython — https://gitpython.readthedocs.io/ (git operations)
  - requests — https://docs.python-requests.org/ (HTTP client)
- Templates & examples
  - AWS Lambda + API Gateway patterns — AWS docs and examples (see Terraform AWS provider docs) — https://registry.terraform.io/providers/hashicorp/aws/latest/docs
  - GCP Cloud Run / Google provider docs — https://registry.terraform.io/providers/hashicorp/google/latest/docs
  - Azure App Service / Azurerm docs — https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs


Files of interest
- app/analyzer.py — clones/unzips repositories and extracts metadata (language, port, dockerfile presence).
- app/infra_generator.py — selects templates and returns Terraform HCL plus UI prompts (variables).
- app/deployer.py — writes terraform files, optionally packages/upload workspace artifact, runs `terraform init` / `apply`, and returns outputs/diagnostics.
- app/tf_templates/ — reusable Terraform templates (EC2, ECS/ECR, Lambda+API Gateway, Azure, GCP).

