from flask import request, session, jsonify
import storageapi as storage
import json
import hashlib
import socket
import struct

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

        mac = deviceData.get("mac")
        ip = deviceData.get("ip")
        macsplit = mac.split("-")

        addrs = struct.pack("BBBBBB", int(macsplit[0], 16),
            int(macsplit[1], 16),
            int(macsplit[2], 16),
            int(macsplit[3], 16),
            int(macsplit[4], 16),
            int(macsplit[5], 16)
        )

        magic = b"\xFF" * 6 + addrs * 16

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(magic, (ip, 9))
        sock.close()

        return jsonify({"message": "Magic packet sent", "ip": ip, "name": name})

    else:
        return jsonify({"error": "Invalid request method"}), 405
