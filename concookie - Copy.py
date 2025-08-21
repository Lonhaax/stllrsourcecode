import os
import json

# Expand %APPDATA% and set root directory
root_dir = os.path.join(os.environ['APPDATA'], "output", "Browsers")

# Walk through all folders
for subdir, dirs, files in os.walk(root_dir):
    if "cookies.json" in files:
        json_path = os.path.join(subdir, "cookies.json")
        txt_path = os.path.join(subdir, "cookies.txt")
        
        # Load JSON
        with open(json_path, "r", encoding="utf-8") as f:
            cookies = json.load(f)
        
        # Prepare Netscape lines
        lines = []
        for cookie in cookies:
            domain = cookie.get("host", "")
            flag = "TRUE" if domain.startswith(".") else "FALSE"
            path = "/"
            secure = "FALSE"
            expiration = "0"
            name = cookie.get("name", "")
            value = cookie.get("value", "")
            lines.append(f"{domain}\t{flag}\t{path}\t{secure}\t{expiration}\t{name}\t{value}")
        
        # Write cookies.txt in same folder
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        print(f"Converted: {json_path} -> {txt_path}")
