from flask import request, session, jsonify
import storageapi as storage
import json
import hashlib

# Define the entry point that handles the HTTP request
# Request is made as such:
# http://0.0.0.0/wol/register?mac=00:00:00:00:00:00&ip=111.111.111.111&name=Test&testport=65000&authstr=abcdef
def flaskMain(request, session):
    # Handle GET and POST methods
    if request.method == 'GET':
        # Access GET data, e.g., request.args['name']
        mac = request.args.get('mac')
        ip = request.args.get('ip')
        name = request.args.get('name')
        testport = request.args.get('testport')
        authstr = request.args.get('authstr')
        authstr = hashlib.sha256(authstr.encode()).hexdigest()

        if storage.has(f"/devices/{name}") is True:
            return jsonify({"error": "Device already exists"}), 409

        if "-" not in mac:
            return jsonify({"error": "Invalid MAC address! Use '-' to separate each octet"}), 400

        deviceData = {
            "mac": mac,
            "ip": ip,
            "name": name,
            "testport": testport,
            "authstr": authstr
        }

        # Indent 4 spaces for pretty printing
        deviceDataJson = json.dumps(deviceData, indent=4)

        storage.writeStr(f"/devices/{name}", deviceDataJson)

        return jsonify({"message": "Machine registered", "name": name})

    else:
        return jsonify({"error": "Invalid request method"}), 405
