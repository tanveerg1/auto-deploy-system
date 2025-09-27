import re

def parse_intent(description: str) -> dict:
    description = description.lower()

    cloud_provider = None
    if "aws" in description:
        cloud_provider = "aws"
    elif "gcp" in description or "google cloud" in description:
        cloud_provider = "gcp"
    elif "azure" in description:
        cloud_provider = "azure"

    runtime = None
    if "node.js" in description or "node" in description:
        runtime = "nodejs"
    elif "python" in description or "flask" in description or "django" in description:
        runtime = "python"
    elif "java" in description or "spring" in description:
        runtime = "java"

    database = None
    if "mongodb" in description:
        database = "mongodb"
    elif "postgres" in description or "postgresql" in description:
        database = "postgres"
    elif "mysql" in description:
        database = "mysql"

    containerized = "docker" in description or "container" in description
    
    if "serverless" in description:
        strategy = "serverless"

    return {
        "cloud_provider": cloud_provider,
        "strategy": strategy,
        "runtime": runtime,
        "database": database,
        "containerized": containerized
    }