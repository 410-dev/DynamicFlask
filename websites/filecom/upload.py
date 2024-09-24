from flask import request, session, jsonify
import storageapi

# Define the entry point that handles the HTTP request
# Request is made as such:
# http://0.0.0.0/filecom/upload
def flaskMain(request, session):
    # Check if the request contains the file
    if 'file' not in request.files:
        return jsonify({"error": 400, "message": "No file part in the request"}), 400

    file = request.files['file']

    # If no file is selected or the filename is empty
    if file.filename == '':
        return jsonify({"error": 400, "message": "No selected file"}), 400

    try:
        # Read the file's bytes directly from the request
        file_data = file.read()

        # Pass the file's bytes directly to the storage API
        storageapi.writeBytes(f"files/{file.filename}", file_data)

        return jsonify({"message": f"File '{file.filename}' uploaded successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500