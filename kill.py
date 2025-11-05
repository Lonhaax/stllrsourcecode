import os
import psutil

def kill_task(process_name):
    """Kill all processes matching process_name (case-insensitive)."""
    for proc in psutil.process_iter(['pid', 'name']):
        if process_name.lower() in proc.info['name'].lower():
            try:
                psutil.Process(proc.info['pid']).terminate()
                print(f"Killed: {proc.info['name']} (PID: {proc.info['pid']})")
            except Exception as e:
                print(f"Could not kill {proc.info['name']}: {e}")

# Example: kill Telegram or Chrome
kill_task("Telegram.exe")
kill_task("chrome.exe")
kill_task("firefox.exe")
kill_task("steam.exe")
kill_task("opera.exe")
