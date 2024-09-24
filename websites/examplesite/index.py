from flask import request, session, jsonify


# Define the entry point that handles the HTTP request
def flaskMain(request, session):
    # Handle GET and POST methods
    if request.method == 'POST':
        # Access POST data, e.g., request.form['name']
        data = request.form.to_dict()
        # You can also use the session object for maintaining state
        session['data'] = data
        return jsonify({"message": "POST request received", "data": data})

    elif request.method == 'GET':
        # Retrieve session data if available
        # session_data = session.get('data', {})
        # return jsonify({"message": "GET request received", "session_data": session_data})
        # Return HTML
        return """
        <html>
        <head>
            <title>Flask Example</title>
        </head>
        <body>
            <h1>Flask Example</h1>
            <form method="POST">
                <label for="name">Name:</label>
                <input type="text" name="name" id="name">
                <button type="submit">Submit</button>
            </form>
            </body>
        </html>
        """
