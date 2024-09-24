from flask import request, session, jsonify
import storageapi as storage
import json
import hashlib

# Define the entry point that handles the HTTP request
# Request is made as such:
# http://0.0.0.0/wol/poweron?name=Test&authstr=abcdef
def flaskMain(request, session):
    # Handle GET and POST methods
    if request.method == 'GET':

        name = request.args.get('name')

        if storage.has(f"/devices/{name}") is False:
            return jsonify({"error": "Device not found"}), 404
        deviceData: dict = json.loads(storage.readStr(f"/devices/{name}"))

        authstr = request.args.get('authstr')
        authstr = hashlib.sha256(authstr.encode()).hexdigest()

        if authstr != deviceData.get("authstr"):
            return jsonify({"error": "Invalid authentication string"}), 401

        if storage.remove(f"/devices/{name}"):
            return jsonify({"message": "Machine unregistered", "name": name})
        else:
            return jsonify({"error": "Failed to unregister machine"}), 500

    else:
        return jsonify({"error": "Invalid request method"}), 405
