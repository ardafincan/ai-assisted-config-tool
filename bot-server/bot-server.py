from flask import Flask, make_response, request, jsonify
from argparse import ArgumentParser
import json 

app = Flask(__name__)

@app.route("/message", methods=["POST"])
def response_request():
    data = request.get_json()
    message = data.get("input")
    
    app = find_app(message)
    new_values = get_updated_values(message, app)

    return make_response(jsonify({'value': new_values}), 200)
    
def find_app(input_message: str) -> str:
    #ollama request will be send 
    #probably qwen3:0.6b
    return input_message

def get_updated_values(input_message: str, app: str) -> str:
    #ollama request #2 will be send here
    return input_message 