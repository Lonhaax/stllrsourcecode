import os
import json

# Starting directory (expand %APPDATA%)
root_dir = os.path.join(os.environ['APPDATA'], "output", "Browsers")

# Walk through all folders recursively
for subdir, dirs, files in os.walk(root_dir):
    for file in files:
        if file.lower() == "cookies.json":  # case-insensitive match
            json_path = os.path.join(subdir, file)
            txt_path = os.path.join(subdir, "cookies.txt")
            
            try:
                # Load JSON
                with open(json_path, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                
                # Prepare Netscape lines
                lines = ["# Netscape HTTP Cookie File", "# Generated from JSON"]
                for cookie in cookies:
                    domain = cookie.get("host", "")
                    flag = "TRUE" if domain.startswith(".") else "FALSE"
                    path = cookie.get("path", "/")  # use JSON path if exists
                    secure = "TRUE" if cookie.get("secure", False) else "FALSE"
                    expiration = str(cookie.get("expirationDate", 0))
                    name = cookie.get("name", "")
                    value = cookie.get("value", "")
                    lines.append(f"{domain}\t{flag}\t{path}\t{secure}\t{expiration}\t{name}\t{value}")
                
                # Write cookies.txt in same folder
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))
                
                print(f"Converted: {json_path} -> {txt_path}")
            except Exception as e:
                print(f"Failed to convert {json_path}: {e}")
