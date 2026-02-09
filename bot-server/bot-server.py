from flask import Flask, make_response, request, jsonify, current_app
from argparse import ArgumentParser
from jsonschema import validate, ValidationError
import json
import requests

app = Flask(__name__)
app.logger.setLevel("INFO")


@app.route("/message", methods=["POST"])
def response_request():
    try:
        data = request.get_json()
        message = data.get("input")

        app_name = find_app(message)
        new_values = get_updated_values(message, app_name)

        return make_response(jsonify(new_values), 200)
    except Exception as e:
        current_app.logger.error(f"Request failed: {e}", exc_info=True)
        return make_response(jsonify({"response": str(e)}), 500)


def find_app(input_message: str):
    try: 
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
                "think": False
            },
        )
    except Exception as e:
        current_app.logger.error(f"Couldn't take response from Ollama: {e}", exc_info=True)
        raise
    response.encoding = "utf-8"
    result = response.json()
    app_name = result["response"]
    app_name = app_name.strip()

    return app_name


def get_updated_values(input_message: str, app_name: str):
    try:
        schema_response = requests.get(f"http://schema_service:5001/{app_name}")
        schema_response = schema_response.json()
    except Exception as e:
        current_app.logger.error(f"Schema couldn't retrieved: {e}", exc_info=True)
        raise

    try:
        values_response = requests.get(f"http://values_service:5002/{app_name}")
        values_response = values_response.json()
    except Exception as e:
        current_app.logger.error(f"Values couldn't retrived: {e}", exc_info=True)
        raise

    try: 
        llm_response = requests.post(
            "http://ollama_service:11434/api/generate",
            json={
                "model": "llama3.1:8b",
                "system": """You are a configuration update assistant that ACTIVELY MODIFIES configuration values based on user requests.

                    ## Your Task

                    1. **READ** the input message to understand what changes are requested
                    2. **APPLY** those changes to the current values JSON
                    3. **RETURN** the updated JSON (not the original)

                    ## Critical Rules

                    **YOU MUST MODIFY THE VALUES** - Do not return unchanged values unless the request is invalid or unclear.

                    ### JSON Formatting (STRICTLY REQUIRED)

                    1. Use double quotes (") for all strings and keys - NEVER single quotes (')
                    2. Use JSON literals: `true`, `false`, `null` - NEVER `True`, `False`, `None`
                    3. Return the object directly - Do NOT wrap in "values" key
                    4. Output ONLY valid JSON - no markdown, no explanations

                    ## Input Format

                    You will receive:
                    - **Input message**: What to change
                    - **Current values**: Starting configuration JSON

                    ## Processing Steps

                    1. Identify which fields need to change from the input message
                    2. Apply the requested changes to those fields
                    3. Keep all other fields from current values unchanged
                    4. Ensure the result matches the schema
                    5. Output the complete updated JSON

                    ## Examples

                    **Example 1:**
                    Input message: "Set timeout to 30"
                    Current values: `{"timeout": 10, "debug": false, "api_key": "xyz"}`
                    Output: `{"timeout": 30, "debug": false, "api_key": "xyz"}`

                    **Example 2:**
                    Input message: "Enable debug mode and change api_key to abc123"
                    Current values: `{"timeout": 10, "debug": false, "api_key": "xyz"}`
                    Output: `{"timeout": 10, "debug": true, "api_key": "abc123"}`

                    **Example 3:**
                    Input message: "Set retries to 5 and add endpoint as https://api.example.com"
                    Current values: `{"retries": 3, "timeout": 30}`
                    Schema allows "endpoint" field
                    Output: `{"retries": 5, "timeout": 30, "endpoint": "https://api.example.com"}`

                    ## Important

                    - **ALWAYS apply the requested changes** unless they violate the schema
                    - **NEVER return unchanged values** when a valid change is requested
                    - **PRESERVE all fields** not mentioned in the input message
                    - **OUTPUT ONLY THE JSON** with no additional text`
                """,
                "format": schema_response,
                "prompt": f"""Input message: \"{input_message}\"
                            Current values: `{values_response}`""",
                "stream": False,
            },
        )
    except Exception as e:
        current_app.logger.error(f"Couldn't take response from Ollama: {e}", exc_info=True)
        raise

    llm_response.encoding = "utf-8"
    llm_response = llm_response.json()
    llm_response = llm_response["response"]
    try:
        result = json.loads(llm_response)
    except json.JSONDecodeError:
        current_app.logger.error("Invalid JSON response from LLM")
        raise

    try:
        validate(result, schema_response)
    except ValidationError as e:
        current_app.logger.error(f"Validation error: {e}")
        raise

    current_app.logger.info(llm_response)

    return result


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--listen", default="0.0.0.0:5003")

    args = parser.parse_args()
    host, port = args.listen.split(":")

    app.run(host=host, port=port)
