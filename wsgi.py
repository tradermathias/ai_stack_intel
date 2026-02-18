"""
WSGI wrapper for Render deployment.
Dash apps need to use app.server for gunicorn.
"""

from agentic_trust_dashboard import app

# For Dash apps, gunicorn needs the Flask server object
# Not the Dash app object
server = app.server

if __name__ == "__main__":
    app.run_server(debug=False)
