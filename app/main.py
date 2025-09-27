from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import FileResponse, StreamingResponse
from pathlib import Path
from app.parser import parse_intent
from app.analyzer import analyze_repo
from app.infra_generator import generate_infra
from app.deployer import deploy_app
import json
import asyncio

app = FastAPI()

@app.get("/")
async def chat_ui():
    html_path = Path(__file__).resolve().parent / "static" / "chatui.html"
    return FileResponse(html_path)

@app.post("/deploy")
async def deploy(description: str = Form(...), repo_url: str = Form(None), zip_file: UploadFile = None):
    print(description)
    intent = parse_intent(description)
    print('Analyzing the repo......')

    async def event_stream():
        try:
            yield (json.dumps({"type": "info", "text": "Request received"}) + "\n").encode()
            yield (json.dumps({"type": "info", "text": "Analyzing the repository..."}) + "\n").encode()
            repo_data = await analyze_repo(repo_url, zip_file)
            # print(repo_data)
            yield (json.dumps({"type": "success", "text": "Repository analysis complete", "data": repo_data}) + "\n").encode()

            yield (json.dumps({"type": "info", "text": "Generating Terraform infrastructure..."}) + "\n").encode()
            # If generate_infra is CPU/blocking, run it in executor
            # infra_code = await asyncio.get_running_loop().run_in_executor(None, generate_infra, intent, repo_data)
            infra_code = generate_infra(intent, repo_data)
            yield (json.dumps({"type": "success", "text": "Infrastructure generation complete"}) + "\n").encode()
            # print(infra_code)
            yield (json.dumps({"type": "info", "text": "Deploying application..."}) + "\n").encode()
            # deploy_app may be blocking; run in executor
            result = deploy_app(infra_code)
            yield (json.dumps({"type": "success", "text": f"Deployment finished. and the Public IP is {result}", "result": result}) + "\n").encode()
        except Exception as e:
            yield (json.dumps({"type": "error", "text": f"Error: {str(e)}"}) + "\n").encode()

    return StreamingResponse(event_stream(), media_type="text/event-stream")
