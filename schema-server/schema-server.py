from flask import Flask, make_response
from argparse import ArgumentParser
import os.path
import json

# ADD PROPER LOGGING TOO :ADD
app = Flask(__name__)
schema_dir = ''

@app.route("/<app_name>", methods=['GET'])
def retrieve_app_schema(app_name: str):
    print(f"{schema_dir}/{app_name}.schema.json")
    if os.path.exists(f"{schema_dir}/{app_name}.schema.json"):
        try:
            with open(f"{schema_dir}/{app_name}.schema.json", "r") as f:
                schema = json.load(f)
            return schema
        except Exception:
            return make_response("Internal Server Error", 500)
    else:
        return make_response("No such file", 404)

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('--schema', default='data/schemas') # file says /data/schemas but data/schemas is the working one :CHANGE
    parser.add_argument('--listen', default='0.0.0.0:5001')
    
    args = parser.parse_args()
    host, port = args.listen.split(':')
    schema_dir = args.schema

    app.run(host=host, port=port)
    