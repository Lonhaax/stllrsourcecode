import os
import json

# Correctly expand %APPDATA%
root_dir = os.path.expandvars(r"%APPDATA%\output\Browsers")

if not os.path.exists(root_dir):
    print(f"Error: Root folder does not exist: {root_dir}")
    exit()

found_any = False

# Walk all subdirectories
for subdir, dirs, files in os.walk(root_dir):
    for file in files:
        if file.lower() == "cookies.json":  # match regardless of case
            found_any = True
            json_path = os.path.join(subdir, file)
            txt_path = os.path.join(subdir, "cookies.txt")
            
            print(f"Found cookies.json: {json_path}")

            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
            except Exception as e:
                print(f"  Failed to load JSON: {e}")
                continue

            # Make sure it’s a list of cookies
            if not isinstance(cookies, list):
                print(f"  Skipping {json_path}: not a list")
                continue

            # Prepare Netscape lines
            lines = [""]
            for cookie in cookies:
                domain = cookie.get("host") or cookie.get("domain") or ""
                flag = "TRUE" if domain.startswith(".") else "FALSE"
                path = cookie.get("path", "/")
                secure = "TRUE" if cookie.get("secure", False) else "FALSE"
                expiration = str(cookie.get("expirationDate") or 0)
                name = cookie.get("name", "")
                value = cookie.get("value", "")
                lines.append(f"{domain}\t{flag}\t{path}\t{secure}\t{expiration}\t{name}\t{value}")

            try:
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))
                print(f"  Converted to: {txt_path}")
            except Exception as e:
                print(f"  Failed to write TXT: {e}")

if not found_any:
    print("No cookies.json files found in any subfolders.")

