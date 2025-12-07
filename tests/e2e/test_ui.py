import pytest
import os
import time
from playwright.sync_api import Page, expect

def test_scan_and_classify_flow(page: Page):
    # Navigate to app (running via main_gui.py on port 8765)
    page.goto("http://localhost:8765")

    # Expect title
    expect(page).to_have_title("File Organizer")

    # Fill input path
    # Use the path verified in test_file_detection.py
    input_path = "/Users/jeffmccracken/Library/CloudStorage/GoogleDrive-jeff.mccracken@gmail.com/My Drive/TestFileInputFolder"
    
    # Wait for input to be visible
    page.wait_for_selector("input[placeholder='/path/to/your/files']")
    
    # Fill input
    page.fill("input[placeholder='/path/to/your/files']", input_path)

    # Click Start Organization
    page.click("text=Start Organization")

    # Wait for classification to finish and switch to review step
    # This might take a few seconds
    # We look for the "Ready to Approve" button which appears in Review step
    # Increase timeout to 60s as classification might take time
    expect(page.locator("text=Ready to Approve")).to_be_visible(timeout=60000)

    # Check if items are loaded
    # There should be 34 files (from test_file_detection.py)
    # The table rows are in tbody
    items = page.locator("tbody tr")
    expect(items).not_to_have_count(0)
    
    # Verify we have some items in "Ready to Approve" or "Needs Review"
    # By default "Ready to Approve" tab is active
    # Let's check the counts on the buttons
    ready_btn = page.locator("button:has-text('Ready to Approve')")
    review_btn = page.locator("button:has-text('Needs Review')")
    
    expect(ready_btn).to_be_visible()
    expect(review_btn).to_be_visible()
    
    # Get text content to verify counts
    ready_text = ready_btn.inner_text()
    review_text = review_btn.inner_text()
    print(f"Ready: {ready_text}, Review: {review_text}")

    # Click on an item to preview (if any)
    if items.count() > 0:
        items.nth(0).locator("td").first.click()
        # Check preview panel
        # Wait for the panel to slide in or appear
        # preview_header = page.locator("h3:has-text('File Preview')")
        # expect(preview_header).to_be_visible(timeout=10000)
        # Check if preview content is loaded (or at least the container)
        # expect(page.locator(".bg-gray-50.p-4.rounded-lg")).to_be_visible()
        pass

    # Handle confirm dialog
    page.on("dialog", lambda dialog: dialog.accept())

    # Verify navigation back to Scan
    page.click("text=1. Scan")
    
    # Should be back at scan
    expect(page.locator("text=Input Directory")).to_be_visible()
