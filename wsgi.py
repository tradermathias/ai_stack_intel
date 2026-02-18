cat > wsgi.py << 'EOF'
"""
WSGI wrapper for Render deployment.
This allows Render to find the app object easily.
"""

from agentic_trust_dashboard import app

if __name__ == "__main__":
    app.run(debug=False)
EOF
