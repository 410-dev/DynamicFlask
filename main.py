import os
import importlib.util
import json
import fnmatch
import uuid
from flask import Flask, request, session, jsonify, send_from_directory
from pathlib import Path

def getConfig(key: str) -> any:
    with open("config.json", "r") as file:
        data = json.load(file)
        return data[key]

app = Flask(__name__)
app.secret_key = getConfig("httpSessionSecretKey")

fileBlacklisted = ["__init__.py", ".DS_Store", "config.json", "*.pyc", "main.py", "root.json"]

def find_and_register_routes(base_dir):
    for root, dirs, files in os.walk(base_dir):
        if "root.json" in files:
            continue

        for file in files:
            full_path = os.path.join(root, file)
            relative_path = os.path.relpath(full_path, base_dir)
            uri_path = '/' + Path(relative_path).as_posix()

            if any([fnmatch.fnmatch(file, pattern) for pattern in fileBlacklisted]):
                continue

            if file.endswith('.py') and file != 'main.py':
                python_uri_path = '/' + Path(relative_path).with_suffix('').as_posix()
                print(f"Registering Python route: {python_uri_path} -> {full_path}")
                register_python_route(python_uri_path, full_path)

            else:
                print(f"Registering static file route: {uri_path} -> {full_path}")
                register_static_route(uri_path, full_path, root)


def register_python_route(uri_path, full_path):
    unique_func_name = f"dynamic_route_{uuid.uuid4().hex}"

    def dynamic_route():
        try:
            spec = importlib.util.spec_from_file_location("dynamic_module", full_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, 'flaskMain'):
                return module.flaskMain(request, session)
            else:
                return jsonify({"error": f"No flaskMain function in {full_path}"}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    app.add_url_rule(uri_path, view_func=dynamic_route, methods=['GET', 'POST'], endpoint=unique_func_name)
    app.add_url_rule(uri_path + '/', view_func=dynamic_route, methods=['GET', 'POST'], endpoint=f"{unique_func_name}_slash")

    if uri_path.endswith("/index"):
        new_uri_path = uri_path[:-6]
        print(f"    Registering index route: {new_uri_path}")
        if len(new_uri_path) == 0:
            new_uri_path = "/"
        app.add_url_rule(new_uri_path, view_func=dynamic_route, methods=['GET', 'POST'], endpoint=f"{unique_func_name}_index")

    extension = Path(full_path).suffix
    if extension in getConfig("skipExtension"):
        print(f"    Registering route without extension: {uri_path[:-len(extension)]}")
        app.add_url_rule(uri_path[:-len(extension)], view_func=dynamic_route, methods=['GET', 'POST'], endpoint=f"{unique_func_name}_noext")

def register_static_route(uri_path, full_path, root):
    unique_endpoint = f"static_file_route_{uuid.uuid4().hex}"

    @app.route(uri_path, methods=['GET'], endpoint=unique_endpoint)
    def static_file():
        try:
            return send_from_directory(root, os.path.basename(full_path))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    allowedIndex: list = getConfig("indexAllowed")
    for index in allowedIndex:
        currentFullPath = full_path.replace("\\", "/")
        if currentFullPath.endswith(f"/index{index}"):
            new_uri_path = uri_path[:-(len(index) + 6)]
            if len(new_uri_path) == 0:
                new_uri_path = "/"
            print(f"    Registering index route: {new_uri_path}")
            app.add_url_rule(new_uri_path, view_func=static_file, methods=['GET', 'POST'], endpoint=f"{unique_endpoint}_index")
            app.add_url_rule(new_uri_path + '/', view_func=static_file, methods=['GET', 'POST'], endpoint=f"{unique_endpoint}_index_slash")

    extension = Path(full_path).suffix
    if extension in getConfig("skipExtension"):
        print(f"    Registering route without extension: {uri_path[:-len(extension)]}")
        app.add_url_rule(uri_path[:-len(extension)], view_func=static_file, methods=['GET', 'POST'], endpoint=f"{unique_endpoint}_noext")

find_and_register_routes(getConfig("serverRoot"))

def main():
    app.run(host=getConfig("host"), port=getConfig("port"), debug=getConfig("debug"))

if __name__ == "__main__":
    main()
