"""
File Organizer Desktop GUI - Main Entry Point
PyWebView wrapper for the React + FastAPI application.
"""
import os
import sys
import time
import threading
import webview
import uvicorn
from pathlib import Path

# Add backend to Python path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

# Import FastAPI app
from backend.api import app

# Configuration
API_PORT = 8765
API_HOST = "127.0.0.1"
FRONTEND_URL = f"http://{API_HOST}:{API_PORT}"


class Api:
    """API bridge between Python and JavaScript."""
    
    def __init__(self):
        self.window = None
    
    def set_window(self, window):
        """Set the webview window reference."""
        self.window = window
    
    def select_folder(self, title="Select Folder"):
        """Open native directory picker and return selected path."""
        try:
            if self.window:
                result = self.window.create_file_dialog(
                    webview.FOLDER_DIALOG,
                    directory='',
                    allow_multiple=False
                )
                if result and len(result) > 0:
                    print(f"Folder selected: {result[0]}")
                    return result[0]
                else:
                    print("No folder selected")
            else:
                print("Window not available")
        except Exception as e:
            print(f"Error opening folder dialog: {e}")
            import traceback
            traceback.print_exc()
        return None


def start_api_server():
    """Start FastAPI server in background thread."""
    try:
        uvicorn.run(
            app,
            host=API_HOST,
            port=API_PORT,
            log_level="error",
            access_log=False
        )
    except Exception as e:
        print(f"Error starting API server: {e}")


def wait_for_server(max_wait=10):
    """Wait for the API server to be ready."""
    import socket
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((API_HOST, API_PORT))
            sock.close()
            
            if result == 0:
                print(f"API server is ready at {FRONTEND_URL}")
                return True
        except:
            pass
        
        time.sleep(0.5)
    
    return False


def serve_frontend():
    """
    Serve the frontend. In development, proxy to Vite.
    In production, serve built files.
    """
    frontend_dist = os.path.join(os.path.dirname(__file__), 'frontend', 'dist')
    
    # Check if we have a production build
    if os.path.exists(os.path.join(frontend_dist, 'index.html')):
        # Serve production build
        print(f"Serving frontend from: {frontend_dist}")
        return FRONTEND_URL
    else:
        # Development mode - frontend should be running separately
        print("No production build found. Make sure to run 'npm run dev' in frontend/ directory")
        print("Or build the frontend with 'npm run build' first")
        return FRONTEND_URL


def create_window(api_instance):
    """Create and configure the webview window."""
    url = serve_frontend()
    
    window = webview.create_window(
        title='File Organizer',
        url=url,
        width=1400,
        height=900,
        resizable=True,
        min_size=(1024, 768),
        background_color='#FFFFFF',
        js_api=api_instance
    )
    
    # Set window reference immediately
    api_instance.set_window(window)
    
    # Also set it on window loaded event
    def on_loaded():
        print("Window loaded, API bridge ready")
        api_instance.set_window(window)
    
    window.events.loaded += on_loaded
    
    return window


def main():
    """Main entry point for the desktop application."""
    print("=" * 60)
    print("File Organizer - Desktop Application")
    print("=" * 60)
    
    # Start API server in background thread
    print("Starting API server...")
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()
    
    # Wait for server to be ready
    if not wait_for_server():
        print("ERROR: Could not start API server!")
        sys.exit(1)
    
    # Give the server a bit more time to fully initialize
    time.sleep(1)
    
    # Create API bridge
    api_instance = Api()
    
    # Create and start window
    print("Starting GUI...")
    print(f"Opening window at: {FRONTEND_URL}")
    window = create_window(api_instance)
    
    # Start webview (this blocks until window is closed)
    # Enable debug mode to see console logs
    webview.start(debug=True)
    
    print("\nFile Organizer closed. Goodbye!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

