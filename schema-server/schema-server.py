from flask import Flask, make_response, jsonify
from argparse import ArgumentParser
import os.path
import json

app = Flask(__name__)
app.logger.setLevel("INFO")

@app.route('/health')
def health():
    return make_response('OK', 200)

@app.route("/<app_name>", methods=["GET"])
def retrieve_app_schemas(app_name: str):
    path = f"{app.config['SCHEMA_DIR']}/{app_name}.schema.json"

    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                schema = json.load(f)
            app.logger.info(f"Serving schema: {app_name}")
            return make_response(jsonify(schema), 200)
        except Exception as e:
            app.logger.error(f"Error loading {app_name}: {str(e)}", exc_info=True)
            return make_response(jsonify({"response": "Internal Server Error"}), 500)
    else:
        app.logger.warning(f"Schema not found: {app_name}")
        return make_response(jsonify({"response": "No such file"}), 404)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--schema-dir", dest="schema_dir", default="data/schemas")
    parser.add_argument("--listen", default="0.0.0.0:5001")

    args = parser.parse_args()
    host, port = args.listen.split(":")
    app.config["SCHEMA_DIR"] = args.schema_dir

    app.run(host=host, port=port)
