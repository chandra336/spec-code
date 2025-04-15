from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Environment, FileSystemLoader
import uvicorn
import os
import json

app = FastAPI()

env = Environment(loader=FileSystemLoader("templates"))

# Allow cross-origin (optional, for frontend integration)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/generate-code/")
async def generate_code(ast: dict):
    output = {
        "angular": [],
        "springboot": []
    }

    # Angular Generation
    if "frontend" in ast and ast["frontend"]["framework"] == "Angular":
        for component in ast["frontend"]["components"]:
            ts_code = env.get_template("angular/component.ts.j2").render(component=component)
            html_code = env.get_template("angular/component.html.j2").render(component=component)
            service_code = env.get_template("angular/service.ts.j2").render(component=component)

            output["angular"].append({
                "component.ts": ts_code,
                "component.html": html_code,
                "service.ts": service_code
            })

    # Spring Boot Generation
    if "backend" in ast and ast["backend"]["framework"] == "SpringBoot":
        for controller in ast["backend"]["controllers"]:
            ctrl_code = env.get_template("springboot/controller.java.j2").render(controller=controller, base_path=ast["backend"].get("basePath", "/api"))
            output["springboot"].append({
                f"{controller['name']}.java": ctrl_code
            })

        if "database" in ast["backend"]:
            for model in ast["backend"]["database"].get("models", []):
                model_code = env.get_template("springboot/model.java.j2").render(model=model)
                output["springboot"].append({
                    f"{model['name']}.java": model_code
                })

    return JSONResponse(content=output)
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5001)