from flask import request, session, jsonify
import storageapi
import os
import json
import instancemgmtapi
import adminauthapi

# Define the entry point that handles the HTTP request
# Request is made as such:
# http://0.0.0.0/list?authorization=abcdef
def flaskMain(request, session):
    # Handle GET and POST methods
    if not adminauthapi.checkAdminAuthV1(request, anyOf=["manager.list"]):
        return jsonify({"error": 2, "message": "Unauthorized"}), 401

    # List files in /websites directory
    instances: dict[str, dict] = instancemgmtapi.listInstances()
    return jsonify(instances)
