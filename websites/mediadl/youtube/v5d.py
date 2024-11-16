import os

import websites.mediadl.youtube.v5backend as Backend

from flask import request, session, jsonify, send_file, Response

# def asyncTask(task, cacheID):
#     threading.Thread(target=task).start()
#     return jsonify({"message": "Conversion started", "progress": f"/mediadl/youtube/v5d?id={cacheID}"}), 202

def flaskMain(request, session):
    try:
        # Support both GET and POST methods
        if request.method in ['GET', 'POST']:
            # Extract parameters from args or form
            # id: Cache file id
            cacheID = request.args.get('id') or request.form.get('id')

            if not cacheID:
                return jsonify({"error": 1, "message": "Missing 'id' parameter"}), 400
            
            # Get the cache location
            cacheLocation = Backend.getTemporaryFileLocation(fixedRandom=cacheID, updateAccessTime=False)
            progressfile = f"{cacheLocation}/_progress"
            downloadfile = f"{cacheLocation}/_download"

            if not os.path.exists(progressfile):
                return jsonify({"error": 2, "message": "Progress file not found"}), 404
            
            progresscontent = None
            with open(progressfile, "r") as f:
                progresscontent = f.read()

            if progresscontent == "Error":
                return jsonify({"error": 3, "message": "Error during download/conversion"}), 500
            
            if progresscontent == "100.00:END":
                with open(downloadfile, "r") as f:
                    downloadPath = f.read()
                return send_file(downloadPath, as_attachment=True)
            
            return jsonify({"message": "Conversion in progress", "progress": progresscontent}), 200
        
        return jsonify({"error": 4, "message": "Method not allowed"}), 405
    except Exception as e:
        return jsonify({"error": 5, "message": str(e)}), 500
    