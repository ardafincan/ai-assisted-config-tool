from flask import Flask, make_response
from argparse import ArgumentParser
import os.path
import json

# ADD PROPER LOGGING :ADD
# ADD UNIT TESTS :ADD
app = Flask(__name__)

@app.route("/<app_name>", methods=["GET"])
def retrieve_app_values(app_name: str):
    path = f"{app.config["SCHEMA_DIR"]}/{app_name}.value.json"

    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                schema = json.load(f)
            return make_response(schema, 200)
        except Exception:
            return make_response("Internal Server Error", 500)
    else:
        return make_response("No such file", 404)
    
if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--schema-dir", dest="schema_dir", default="data/values")
    parser.add_argument("--listen", default="0.0.0.0:5002")
    
    args = parser.parse_args()
    host, port = args.listen.split(":")
    app.config["SCHEMA_DIR"] = args.schema_dir
    
    app.run(host=host, port=port)