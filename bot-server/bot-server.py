from flask import Flask, make_response, request, jsonify
from argparse import ArgumentParser
import json
import requests

app = Flask(__name__)


@app.route("/message", methods=["POST"])
def response_request():
    data = request.get_json()
    message = data.get("input")

    app_name = find_app(message)
    new_values = get_updated_values(message, app_name)

    return make_response(jsonify({"value": new_values}), 200)


def find_app(input_message: str) -> str:
    response = requests.post(
        "http://ollama_service:11434/api/generate",
        json={
            "model": "qwen3:0.6b",
            "system": """You are a service classifier. 
                         Given user input, determine which service they need: chat, matchmaking, or tournament. Think step-by-step: 
                         1. Identify service name or related keywords 
                         2. Consider the configuration or action 
                         3. Output only: \"chat\", \"matchmaking\", or \"tournament\". 
                         Examples: 
                            \"set tournament service memory to 1024mb\" -> tournament, 
                            \"set GAME_NAME env to toyblast for matchmaking service\" -> matchmaking, 
                            \"lower cpu limit of chat service to 80%\" -> chat""",
            "prompt": input_message,
            "stream": False,
        },
    )
    response.encoding = "utf-8"
    result = response.json()
    app_name = result["response"]

    return app_name


def get_updated_values(input_message: str, app_name: str) -> str:
    schema_response = requests.get(
        f"http://schema_service:5001/{app_name}"
    )
    schema_response = schema_response.json()

    values_response = requests.get(f"http://values_service:5002/{app_name}")
    values_response = values_response.json()

    llm_response = requests.post(
        "http://ollama_service:11434/api/generate",
        json={
            "model": "qwen3:4b",
            "system": """You are a configuration update assistant. Your task is to process user requests and update a JSON configuration object while maintaining strict schema compliance.

                        ## Core Responsibilities

                        1. **Parse user requests**: Understand configuration change requests from natural language input
                        2. **Update values**: Modify the current configuration JSON based on the request
                        3. **Maintain schema compliance**: Ensure all updates conform to the provided JSON schema structure
                        4. **Preserve existing data**: Only modify fields mentioned in the request; keep all other fields unchanged

                        ## Input Format

                        You will receive:
                        - **Input message**: User's natural language request for configuration changes
                        - **Current values**: The existing configuration as a JSON object

                        ## Output Format

                        Return ONLY a valid JSON object with the updated configuration. Do not include:
                        - Explanatory text
                        - Markdown code blocks
                        - Comments or annotations

                        ## Validation Rules

                        - All required fields from the schema must be present
                        - Field types must match schema definitions (string, number, boolean, array, object)
                        - Respect schema constraints (min/max values, enum options, patterns)
                        - Maintain nested object structures
                        - Preserve array structures unless explicitly asked to modify

                        ## Error Handling

                        If a request cannot be processed:
                        - Return the current values unchanged
                        - You may add an "_error" field with a brief explanation (if schema allows)

                        ## Example

                        Input message: "Set timeout to 30 and enable debug mode"
                        Current values: `{"timeout": 10, "debug": false, "api_key": "xyz"}`

                        Output: `{"timeout": 30, "debug": true, "api_key": "xyz"}`
            """,
            "format": schema_response,
            "prompt": f"""Input message: \"{input_message}\"
                        Current values: `{values_response}`""",
            "stream": False,
        },
    )
    llm_response.encoding = "utf-8"
    llm_response = llm_response.json()
    updated_values = llm_response["response"]

    return updated_values

if __name__ == "__main__": 
    parser = ArgumentParser()
    parser.add_argument("--listen", default="0.0.0.0:5003")
    
    args = parser.parse_args()
    host, port = args.listen.split(":")

    app.run(host=host, port=port)