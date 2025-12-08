#!/usr/bin/env python3
"""
File Organizer Web Server
Launches the FastAPI backend for browser access.

Usage:
    python3 run_server.py
    
Then open: http://localhost:8765 in your browser
"""
import uvicorn
import os
import sys

# Add backend to path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    print("=" * 60)
    print("File Organizer Web Server")
    print("=" * 60)
    print()
    print("Server starting on http://localhost:8765")
    print()
    print("Open your browser and navigate to:")
    print("  → http://localhost:8765")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    print()
    
    uvicorn.run(
        "backend.api:app",
        host="127.0.0.1",
        port=8765,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
