import platform
import subprocess
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

        mac = deviceData.get("mac")
        ip = deviceData.get("ip")

        system_name = platform.system()
        ping_command = []

        # Linux or macOS
        if system_name == "Linux" or system_name == "Darwin":  # macOS also uses Unix-like ping
            ping_command = ["ping", "-c", "1", "-W", "1", ip]

        # Windows
        elif system_name == "Windows":
            ping_command = ["ping", "-n", "1", "-w", "1000", ip]  # Timeout in milliseconds (1000 ms = 1 second)

        try:
            output = subprocess.check_output(ping_command, stderr=subprocess.STDOUT)
            return jsonify({"message": f"Machine seems to be online: {output}", "ip": ip, "name": name}), 200
        except subprocess.CalledProcessError:
            return jsonify({"error": "Machine seems to be offline"}), 400

    else:
        return jsonify({"error": "Invalid request method"}), 405
