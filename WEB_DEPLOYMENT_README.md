# File Organizer - Quick Start Guide

## Web-Based Access

The File Organizer is now a web application that runs in your browser.

### Launch Instructions

1. **Start the server:**

   ```bash
   cd Local-File-Organizer
   python3 run_server.py
   ```

2. **Open in browser:**
   Navigate to: <http://localhost:8765>

3. **Stop the server:**
   Press `Ctrl+C` in the terminal

### Using the Application

1. **Enter folder paths manually** in the input fields (no Browse buttons)
2. **Scan & Classify**: Enter your input directory path and click "Start Organization"
3. **Review**: Check classifications and approve/reject items
4. **Migrate**: Move approved files to their organized locations

### Admin Tools

- **Taxonomy Editor**: <http://localhost:8080/taxonomy-editor.html>
  - Requires running the taxonomy editor server first:

    ```bash
    python3 run_taxonomy_editor.py
    ```

## What Changed

Previously, File Organizer was a desktop application using PyWebView. The application has been converted to web-only:

- ✅ Removed `main_gui.py` desktop wrapper
- ✅ Removed PyWebView browse buttons
- ✅ Created `run_server.py` web launcher
- ✅ All features now accessible via browser

## Requirements

- Python 3.12+
- All dependencies in `requirements.txt`
- Modern web browser (Chrome, Firefox, Safari, Edge)
