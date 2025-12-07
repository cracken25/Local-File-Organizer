#!/usr/bin/env python3
"""
Simple HTTP server for running the Taxonomy Editor locally.
This is needed because browsers block file:// fetch requests.

Usage:
    python3 run_taxonomy_editor.py

Then open: http://localhost:8080/taxonomy-editor.html
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

PORT = 8080

# Get the directory of this script
DIRECTORY = Path(__file__).parent

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)

print(f"Starting Taxonomy Editor server on port {PORT}...")
print(f"Serving files from: {DIRECTORY}")
print(f"\nOpen in browser: http://localhost:{PORT}/taxonomy-editor.html")
print("\nPress Ctrl+C to stop the server\n")

# Open browser automatically
webbrowser.open(f"http://localhost:{PORT}/taxonomy-editor.html")

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        httpd.shutdown()
