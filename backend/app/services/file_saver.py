from pathlib import Path
from fastapi import UploadFile

async def save_large_upload(upload_file: UploadFile, save_path: Path) -> int:
    total_size = 0
    with open(save_path, "wb") as outfile:
        while True:
            chunk = await upload_file.read(1024 * 1024)  # 1 MB chunks
            if not chunk:
                break
            outfile.write(chunk)
            total_size += len(chunk)
    return total_size
