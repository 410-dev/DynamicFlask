import time
from flask import jsonify

def flaskMain(request, session):
    # Simulate a long-running task
    time.sleep(100)
    return jsonify({"message": "Completed after delay"})
