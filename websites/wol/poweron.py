from flask import request, session, jsonify
import storageapi as storage
import json
import hashlib
import socket
import struct
from wakeonlan import send_magic_packet

# Define the entry point that handles the HTTP request
# Request is made as such:
# http://0.0.0.0/wol/poweron?name=Test&authstr=abcdef
def flaskMain(request, session):
    # Handle GET and POST methods
    if request.method == 'GET':

        name = request.args.get('name')

        if storage.has(f"/devices/{name}") is False:
            return jsonify({"error": 1, "message": "Device not found"}), 404
        deviceData: dict = json.loads(storage.readStr(f"/devices/{name}"))

        authstr = request.args.get('authstr')
        authstr = hashlib.sha256(authstr.encode()).hexdigest()

        if authstr != deviceData.get("authstr"):
            return jsonify({"error": 2, "message": "Invalid authentication string"}), 401

        mac = deviceData.get("mac")
        ip = deviceData.get("ip")

        send_magic_packet(mac)

        return jsonify({"message": "Power signal sent. PC should now start up.", "ip": ip, "name": name})

    else:
        return jsonify({"error": 4, "message": "Invalid request method"}), 405
