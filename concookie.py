import os
import json

# Starting directory
root_dir = os.path.expandvars(r"%APPDATA%\output\Browsers")

# Walk through all subfolders
for subdir, dirs, files in os.walk(root_dir):
    for file in files:
        if file.lower() == "cookies.json":  # case-insensitive check
            json_path = os.path.join(subdir, file)
            txt_path = os.path.join(subdir, "cookies.txt")

            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    cookies = json.load(f)

                lines = ["# Netscape HTTP Cookie File", "# Converted from JSON"]
                for cookie in cookies:
                    # Firefox uses "host", Chrome/Brave/Edge may use "domain"
                    domain = cookie.get("host") or cookie.get("domain") or ""
                    flag = "TRUE" if domain.startswith(".") else "FALSE"
                    path = cookie.get("path") or "/"
                    secure = "TRUE" if cookie.get("secure") else "FALSE"
                    expiration = str(cookie.get("expiry") or cookie.get("expirationDate") or 0)
                    name = cookie.get("name") or ""
                    value = cookie.get("value") or ""
                    lines.append(f"{domain}\t{flag}\t{path}\t{secure}\t{expiration}\t{name}\t{value}")

                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))

                print(f"Converted: {json_path} -> {txt_path}")
            except Exception as e:
                print(f"Failed to convert {json_path}: {e}")
