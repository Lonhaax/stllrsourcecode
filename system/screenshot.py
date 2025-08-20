import os
import pyautogui
from datetime import datetime

# Get APPDATA path
appdata = os.environ.get("APPDATA", os.path.expanduser("~"))

# Define output folder
output_folder = os.path.join(appdata, "output")
os.makedirs(output_folder, exist_ok=True)

# Create a timestamped filename
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
screenshot_file = os.path.join(output_folder, f"screenshot_{timestamp}.png")

# Take screenshot and save
screenshot = pyautogui.screenshot()
screenshot.save(screenshot_file)

print(f"Screenshot saved to {screenshot_file}")
