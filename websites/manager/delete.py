from flask import request, session, jsonify
import shutil
import instancemgmtapi
import adminauthapi

# Define the entry point that handles the HTTP request
# Request is made as such:
# http://0.0.0.0/delete?authorization=name$password&instance=<instanceName>
def flaskMain(request, session):
    # Handle GET and POST methods
    if not adminauthapi.checkAdminAuthV1(request, anyOf=["manager.delete"]):
        return jsonify({"error": 2, "message": "Unauthorized"}), 401

    # Get the instance name from the request
    instanceName = request.args.get('instance')

    # List files in /websites directory
    instances: dict[str, dict] = instancemgmtapi.listInstances()


    # Check if the instance exists
    if instanceName not in instances:
        return jsonify({"error": 3, "message": "Instance not found"}), 404

    # Delete the instance
    try:
        shutil.rmtree(instances[instanceName]["installedPath"])
        return jsonify({"success": True, "message": f"Instance '{instanceName}' deleted successfully"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500