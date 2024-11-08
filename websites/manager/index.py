from flask import request, session, jsonify
import storageapi as storage
import adminauthapi

# Define the entry point that handles the HTTP request
# Request is made as such:
# http://0.0.0.0/manager?authorization=abcdef
def flaskMain(request, session):
    # Handle GET and POST methods
    if not adminauthapi.checkAdminAuthV1(request, anyOf=["manager.list"]):
        return jsonify({"error": 2, "message": "Unauthorized"}), 401

    authorizationString = request.args.get('authorization')

    # Available options: list, delete, update, upload
    html = f"""
    <html>
    <head>
        <title>Manager</title>
        </head>
        <body>
            <h1>Manager</h1>
            <p>Available options:</p>
            <ul>
                <li><a href="/manager/list?authorization={authorizationString}">List</a></li>
                <li><a href="/manager/delete?authorization={authorizationString}">Delete</a></li>
                <li><a href="/manager/update?authorization={authorizationString}">Update</a></li>
                <li><a href="/manager/upload?authorization={authorizationString}">Upload</a></li>
            </ul>
        </body>
    </html>
    """
    return html
