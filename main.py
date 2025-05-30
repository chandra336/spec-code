from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Environment, FileSystemLoader
import uvicorn
import os
import json
from antlr4 import *
from HelloWorldAppLexer import HelloWorldAppLexer
from HelloWorldAppParser import HelloWorldAppParser
from antlr4.tree.Tree import TerminalNodeImpl, ErrorNodeImpl

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
async def generate_code():
    output = {
        "angular": [],
        "springboot": []
    }
    ast = main()
    ast_dict = convert_ast_to_dict(ast)
    
    # Angular Generation
    if "frontend" in ast_dict and ast_dict["frontend"].get("framework") == "Angular":
        for component in ast_dict["frontend"].get("components", []):
            ts_code = env.get_template("angular/component.ts.j2").render(component=component)
            html_code = env.get_template("angular/component.html.j2").render(component=component)
            service_code = env.get_template("angular/service.ts.j2").render(component=component)

            output["angular"].append({
                "component.ts": ts_code,
                "component.html": html_code,
                "service.ts": service_code
            })

    # Spring Boot Generation
    if "backend" in ast_dict and ast_dict["backend"].get("framework") == "SpringBoot":
        for controller in ast_dict["backend"].get("controllers", []):
            ctrl_code = env.get_template("springboot/controller.java.j2").render(controller=controller, base_path=ast_dict["backend"].get("basePath", "/api"))
            output["springboot"].append({
                f"{controller['name']}.java": ctrl_code
            })

        if "database" in ast_dict["backend"]:
            for model in ast_dict["backend"]["database"].get("models", []):
                model_code = env.get_template("springboot/model.java.j2").render(model=model)
                output["springboot"].append({
                    f"{model['name']}.java": model_code
                })

    return JSONResponse(content=output)


def main():
    # Sample document content
    document_content = """Application Name:HelloWorldApp
Version:1.0
Description:Good App

Frontend (Angular):
Technology:Angular
Page/Component Name: HelloWorldComponent
Route/Path: /hello
What it does:
Displays a welcome message from the backend.
UI Elements:
Text field to display the message
Frontend Behavior:
OnInit fetch call to backend API

Backend (Spring Boot):
Technology:Springboot
Base API Path: /api
Controller Name: HelloWorldController
Endpoint:
Path: /hello
Method: GET
What it returns: Hello, World!
Security: None

            """

    # Create a lexer and parser
    input_stream = InputStream(document_content)
    lexer = HelloWorldAppLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = HelloWorldAppParser(stream)

    # Parse the document
    tree = parser.app()

    # Print the AST
    print(tree.toStringTree(recog=parser))
    return tree

def convert_ast_to_dict(tree):
    def extract_text(node):
        if not node:
            return ""
        if isinstance(node, TerminalNodeImpl):
            return node.getText()
        elif isinstance(node, ErrorNodeImpl):
            return "<error>"
        if not hasattr(node, 'children') or not node.children:
            return ""
        return " ".join(extract_text(child) for child in node.children)


    def extract_section(node):
        section = {}
        for i in range(node.getChildCount()):
            child = node.getChild(i)
            if isinstance(child, TerminalNodeImpl) or isinstance(child, ErrorNodeImpl):
                continue
            rule_name = HelloWorldAppParser.ruleNames[child.getRuleIndex()]
            section[rule_name] = extract_text(child)
        return section

    ast_dict = {}
    for i in range(tree.getChildCount()):
        child = tree.getChild(i)
        if isinstance(child, ErrorNodeImpl):
            continue
        if isinstance(child, TerminalNodeImpl):
            rule_name = child.getText()
        else:
            rule_name = HelloWorldAppParser.ruleNames[child.getRuleIndex()]
        if rule_name == "frontend":
            ast_dict["frontend"] = extract_section(child)
        elif rule_name == "backend":
            ast_dict["backend"] = extract_section(child)
        else:
            ast_dict[rule_name] = extract_text(child)
    
    return ast_dict

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5001)
