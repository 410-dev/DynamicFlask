
from flask import request, session, jsonify
import shutil
import json
import os
import zipfile
import storageapi
import adminauthapi
import instancemgmtapi

# Define the entry point that handles the HTTP request
# Request is made as such:
# http://0.0.0.0/filecom/upload?authorization=name$password&mode=<update/install>
def flaskMain(request, session):

    # Get mode from the request
    mode = request.args.get('mode')
    if not mode == "update" and not mode == "install":
        return jsonify({"error": 400, "message": "Invalid mode"}), 400

    if not adminauthapi.checkAdminAuthV1(request, anyOf=[f"manager.{mode}"]):
        return jsonify({"error": 2, "message": "Unauthorized"}), 401

    # Check if the request contains the file
    file = request.files['file']

    # If no file is selected or the filename is empty
    if file.filename == '':
        return jsonify({"error": 400, "message": "No selected file"}), 400

    # Save file
    try:
        file_data = file.read()
        storageapi.writeBytes(f"manager/packages/{file.filename}", file_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Check if zip file
    if not file.filename.endswith(".zip"):
        return jsonify({"error": 400, "message": "Invalid file type"}), 400

    # Check if the file is a valid zip file
    try:
        extractionPath: str = storageapi.getRawPathToStorage(f"manager/extraction/{file.filename}")
        with zipfile.ZipFile(file) as zip_ref:
            zip_ref.extractall(extractionPath)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Check if "instance.json" exists
    if not os.path.exists(f"{extractionPath}/instance.json"):
        return jsonify({"error": 400, "message": "Missing instance.json"}), 400

    # Read instance.json
    try:
        with open(f"{extractionPath}/instance.json", "r") as f:
            instanceData = json.load(f)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Check if the instance name is valid
    requiredFields: list[str] = ["name", "version"]
    for field in requiredFields:
        if field not in instanceData:
            return jsonify({"error": 400, "message": f"Missing '{field}' in instance.json"}), 400

    # Check if instance already exists
    instances: dict[str, dict] = instancemgmtapi.listInstances()
    if instanceData["name"] in instances and mode == "install":
        return jsonify({"error": 400, "message": "Instance already exists"}), 400

    # Disallow any special characters except for dash and underscore
    if not instanceData["name"].replace("-", "").replace("_", "").isalnum():
        return jsonify({"error": 400, "message": "Invalid instance name"}), 400

    # Move the instance to preferred location
    try:
        if "preferredPath" in instanceData:
            instancePath: str = storageapi.getConfig("serverRoot") + f"/{instanceData['preferredPath']}"
        else:
            instancePath: str = storageapi.getConfig("serverRoot") + f"/{instanceData['name']}"
        shutil.rmtree(instancePath, ignore_errors=True)
        shutil.move(extractionPath, instancePath)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Return success
    return jsonify({"success": True, "message": f"Instance '{instanceData['name']}' {mode}ed successfully"}), 200