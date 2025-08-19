#!/usr/bin/env python3
import ctypes as ct
import json
import os
import sys
import sqlite3
import logging
import platform
import configparser
from base64 import b64decode
import datetime

# -- Để copy db tránh lock --
import tempfile
import shutil

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)
DEFAULT_ENCODING = "utf-8"


class NSSProxy:
    class SECItem(ct.Structure):
        _fields_ = [
            ("type", ct.c_uint),
            ("data", ct.c_char_p),
            ("len", ct.c_uint),
        ]
        def decode_data(self):
            return ct.string_at(self.data, self.len).decode(DEFAULT_ENCODING)

    class PK11SlotInfo(ct.Structure):
        pass

    def __init__(self):
        self.libnss = self._load_nss()
        SlotInfoPtr = ct.POINTER(self.PK11SlotInfo)
        SECItemPtr = ct.POINTER(self.SECItem)

        # Định nghĩa các hàm cần thiết từ NSS
        self._set_ctypes(ct.c_int, "NSS_Init", ct.c_char_p)
        self._set_ctypes(None,    "NSS_Shutdown")
        self._set_ctypes(SlotInfoPtr, "PK11_GetInternalKeySlot")
        self._set_ctypes(None,    "PK11_FreeSlot", SlotInfoPtr)
        self._set_ctypes(ct.c_int, "PK11SDR_Decrypt", SECItemPtr, SECItemPtr, ct.c_void_p)
        self._set_ctypes(None,    "SECITEM_ZfreeItem", SECItemPtr, ct.c_int)

    def _set_ctypes(self, restype, name, *argtypes):
        fn = getattr(self.libnss, name)
        fn.restype  = restype
        fn.argtypes = argtypes
        setattr(self, "_" + name, fn)

    def _load_nss(self):
        if platform.system() == "Windows":
            candidates = [
                (r"C:\Program Files\Mozilla Firefox\nss3.dll",
                 r"C:\Program Files\Mozilla Firefox"),
                (r"C:\Program Files (x86)\Mozilla Firefox\nss3.dll",
                 r"C:\Program Files (x86)\Mozilla Firefox"),
            ]
            for dll, dir_ in candidates:
                if os.path.exists(dll):
                    try:
                        os.add_dll_directory(dir_)
                        return ct.CDLL(dll)
                    except OSError:
                        continue
            LOG.error("Không load được nss3.dll trên Windows")
            sys.exit(1)
        else:
            so = "/usr/lib/x86_64-linux-gnu/libnss3.so"
            try:
                return ct.CDLL(so)
            except OSError:
                LOG.error("Không load được libnss3.so trên Linux")
                sys.exit(1)

    def initialize(self, profile_path):
        rv = self._NSS_Init(f"sql:{profile_path}".encode(DEFAULT_ENCODING))
        if rv:
            LOG.error("NSS_Init thất bại với profile %s", profile_path)
            sys.exit(1)

    def decrypt(self, data64: str) -> str:
        raw = b64decode(data64)
        inp = self.SECItem(0, raw, len(raw))
        out = self.SECItem(0, None, 0)
        if self._PK11SDR_Decrypt(ct.byref(inp), ct.byref(out), None):
            LOG.error("PK11SDR_Decrypt thất bại")
            return ""
        try:
            return out.decode_data()
        finally:
            self._SECITEM_ZfreeItem(ct.byref(out), 0)

    def shutdown(self):
        self._NSS_Shutdown()


def get_default_firefox_profile_path() -> str:
    if platform.system() == "Windows":
        base = os.path.join(os.environ["USERPROFILE"], "AppData", "Roaming", "Mozilla", "Firefox")
        ini  = os.path.join(base, "profiles.ini")
    else:
        home = os.environ["HOME"]
        snap_ini = os.path.join(home, "snap", "firefox", "common", ".mozilla", "firefox", "profiles.ini")
        if os.path.exists(snap_ini):
            base = os.path.join(home, "snap", "firefox", "common", ".mozilla", "firefox")
            ini  = snap_ini
        else:
            base = os.path.join(home, ".mozilla", "firefox")
            ini  = os.path.join(base, "profiles.ini")

    if not os.path.exists(ini):
        LOG.error("Không tìm thấy profiles.ini: %s", ini)
        sys.exit(1)

    cfg = configparser.ConfigParser()
    cfg.read(ini)
    # ưu tiên *.default-release
    for section in cfg.sections():
        if cfg.has_option(section, "Path") and ".default-release" in cfg.get(section, "Path"):
            p = cfg.get(section, "Path")
            rel = cfg.getboolean(section, "IsRelative", fallback=True)
            return os.path.join(base, p) if rel else p
    # fallback profile mặc định
    for section in cfg.sections():
        if cfg.get(section, "Default", fallback="0") == "1":
            p = cfg.get(section, "Path")
            rel = cfg.getboolean(section, "IsRelative", fallback=True)
            return os.path.join(base, p) if rel else p

    LOG.error("Không tìm thấy profile Firefox phù hợp")
    sys.exit(1)


def extract_cookies(nss: NSSProxy, profile: str, out_path: str):
    src_db = os.path.join(profile, "cookies.sqlite")
    if not os.path.isfile(src_db):
        LOG.warning("Không tìm thấy cookies.sqlite trong %s", profile)
        return

    # copy tạm database để tránh lock
    tmpdir = tempfile.mkdtemp(prefix="ff_cookies_")
    tmp_db = os.path.join(tmpdir, "cookies.sqlite")
    shutil.copy2(src_db, tmp_db)

    conn = sqlite3.connect(tmp_db)
    conn.execute("PRAGMA busy_timeout = 5000")
    cur = conn.cursor()

    # kiểm tra cột encryptedValue
    cur.execute("PRAGMA table_info(moz_cookies)")
    cols = [row[1] for row in cur.fetchall()]
    has_enc = "encryptedValue" in cols

    if has_enc:
        cur.execute("""
            SELECT host, name, value, encryptedValue, path, expiry, isSecure, isHttpOnly
            FROM moz_cookies
        """)
    else:
        cur.execute("""
            SELECT host, name, value, path, expiry, isSecure, isHttpOnly
            FROM moz_cookies
        """)

    cookies = []
    for row in cur.fetchall():
        host, name = row[0], row[1]
        if has_enc:
            enc_val = row[3]
            val = enc_val and nss.decrypt(enc_val) or row[2]
            path, exp, sec, httponly = row[4], row[5], bool(row[6]), bool(row[7])
        else:
            val = row[2]
            path, exp, sec, httponly = row[3], row[4], bool(row[5]), bool(row[6])

        cookies.append({
            "host": host,
            "name": name,
            "value": val,
            "path": path,
            "expiry": exp,
            "secure": sec,
            "httpOnly": httponly
        })

    with open(out_path, "w", encoding=DEFAULT_ENCODING) as f:
        json.dump(cookies, f, indent=4)
    LOG.info("Đã lưu %d cookies vào %s", len(cookies), out_path)

    conn.close()
    # nếu muốn xóa tmp folder sau:
    # shutil.rmtree(tmpdir)


def extract_history(profile: str, out_path: str):
    src = os.path.join(profile, "places.sqlite")
    if not os.path.isfile(src):
        LOG.warning("Không tìm thấy places.sqlite trong %s", profile)
        return

    tmpdir = tempfile.mkdtemp(prefix="ff_history_")
    tmp_db = os.path.join(tmpdir, "places.sqlite")
    shutil.copy2(src, tmp_db)

    conn = sqlite3.connect(tmp_db)
    conn.execute("PRAGMA busy_timeout = 5000")
    cur = conn.cursor()

    cur.execute("""
        SELECT p.url, p.title, h.visit_date
        FROM moz_places p
        JOIN moz_historyvisits h ON p.id = h.place_id
        ORDER BY h.visit_date
    """)

    history = []
    for url, title, visit_date in cur.fetchall():
        try:
            ts = visit_date / 1_000_000
            dt = datetime.datetime.fromtimestamp(ts)
            visit_time = dt.isoformat()
        except Exception:
            visit_time = str(visit_date)
        history.append({
            "url": url,
            "title": title,
            "visit_date": visit_time
        })

    with open(out_path, "w", encoding=DEFAULT_ENCODING) as f:
        json.dump(history, f, indent=4)
    LOG.info("Đã lưu %d mục lịch sử vào %s", len(history), out_path)

    conn.close()
    # nếu muốn xóa tmp folder sau:
    # shutil.rmtree(tmpdir)


def main():
    profile = get_default_firefox_profile_path()
    nss = NSSProxy()
    nss.initialize(profile)

    # Define your fixed temp output folder
    tmp_dir = os.path.join(os.environ.get("TEMP", tempfile.gettempdir()), "Output", "Firefox")
    os.makedirs(tmp_dir, exist_ok=True)

    cookies_path = os.path.join(tmp_dir, "Cookies.json")
    history_path = os.path.join(tmp_dir, "History.json")

    extract_cookies(nss, profile, cookies_path)
    extract_history(profile, history_path)

    LOG.info("Cookies saved to %s", cookies_path)
    LOG.info("History saved to %s", history_path)

    nss.shutdown()
    sys.exit(0)
if __name__ == "__main__":
    main()
