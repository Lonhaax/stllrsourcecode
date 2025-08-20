import os
import json

# Base output folder
temp_folder = os.path.join(os.getenv("TEMP"), "output", "Browsers")

# List to store all cookies
all_cookies = []

# Loop through each browser folder
for browser_name in os.listdir(temp_folder):
    browser_folder = os.path.join(temp_folder, browser_name)
    cookie_file = os.path.join(browser_folder, "cookies.json")
    
    if os.path.isfile(cookie_file):
        try:
            with open(cookie_file, "r") as f:
                cookies = json.load(f)
                all_cookies.extend(cookies)
        except Exception as e:
            print(f"Failed to load {cookie_file}: {e}")

# Convert to Netscape format
netscape_lines = []
for cookie in all_cookies:
    domain = cookie.get("domain", "")
    include_subdomains = "TRUE" if cookie.get("hostOnly", False) == False else "FALSE"
    path = cookie.get("path", "/")
    secure = "TRUE" if cookie.get("secure", False) else "FALSE"
    expiry = str(cookie.get("expirationDate", 0))
    name = cookie.get("name", "")
    value = cookie.get("value", "")
    netscape_lines.append(f"{domain}\t{include_subdomains}\t{path}\t{secure}\t{expiry}\t{name}\t{value}")

# Write to cookies.txt
with open(os.path.join(temp_folder, "cookies.txt"), "w") as f:
    f.write("\n".join(netscape_lines))

print("Netscape cookies.txt generated successfully.")
