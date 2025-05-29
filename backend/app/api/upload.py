import os
import logging
from datetime import datetime
import re
from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from app.utils.log_storage import LogStorageService
from fastapi import APIRouter, File, UploadFile,HTTPException
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.utils.log_parser import parser_log_file_from_content, combine_logs
import json
import zipfile
import tempfile
from pathlib import Path
import uuid
from app.utils.thread_pool_processing import run_in_thread_pool

task_status = {}

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = settings.UPLOAD_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)

FILENAME_REGEX = re.compile(settings.FILENAME_REGEX)

def validate_filename(filename: str):
    match = FILENAME_REGEX.fullmatch(filename)
    if not match:
        return False, "Filename must be in format transactions_YYYYMMDD.zip"
    try:
        file_date = datetime.strptime(match.group(1), "%Y%m%d").date()
    except ValueError:
        return False, "Date in filename is invalid"
    if file_date != datetime.now().date():
        return False, f"File date {file_date} is not today's date"
    return True, None

@router.post("/upload", tags=["File Operations"])
async def upload_file(file: UploadFile = File(...),background_task:BackgroundTasks=None):
    if not file.filename.endswith(".zip"):
        raise HTTPException(400, "The file is not in Zip format")
    
    # TODO: validate filename pattern and date 
    try:
        task_id = str(uuid.uuid4())
        upload_file = Path("upload")
        
        upload_file.mkdir(parents=True, exist_ok=True)
        save_path = upload_file / f"{file.filename}"
        existing_files = list(upload_file.glob(f"*_{file.filename}"))
        if existing_files:
             return {"error": "File with the same name already exists"}

        # Save large upload in chunks and get file size
        file_size = await save_large_upload(file, save_path)

        logger.info(f"Received ZIP file: {file.filename}")
        logger.info(f"File saved to: {save_path}")
        logger.info(f"File size: {file_size} bytes")

        task_status[task_id] = "processing"

        # Spawn background task to process the saved ZIP file
        run_in_thread_pool(process_zip_file, task_id, str(save_path))

        # Return task_id immediately
        return {"task_id": task_id, "status": "processing"}

    except Exception as e:
        logger.exception("Failed to handle uploaded file")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

def process_zip_file(task_id: str, file_path: str):
    try:
        logger.info(f"[{task_id}] Starting zip file processing: {file_path}")
        temp_dir = tempfile.mkdtemp()
        extracted_files = []

        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            for zip_info in zip_ref.infolist():
                if not zip_info.is_dir():
                    zip_ref.extract(zip_info, temp_dir)
                    extracted_files.append(zip_info.filename)

        logger.info(f"[{task_id}] Extracted files: {extracted_files}")

        all_parsed_logs = []
        for extracted_file in extracted_files:
            full_path = os.path.join(temp_dir, extracted_file)
            if os.path.isdir(full_path):
                continue
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    parsed_logs = parser_log_file_from_content(content)
                    all_parsed_logs.extend(parsed_logs)
            except UnicodeDecodeError:
                logger.warning(f"[{task_id}] Skipping non-text file: {extracted_file}")
            except Exception as e:
                logger.error(f"[{task_id}] Error parsing file {extracted_file}: {e}")

        if all_parsed_logs:
            logger.info(f"[{task_id}] Parsed {len(all_parsed_logs)} logs")
            df = combine_logs(all_parsed_logs)
            log_records = df.to_dict("records")

            logger.info(f"[{task_id}] Storing logs in MongoDB...")
            result = LogStorageService.store_logs_batch(log_records)
            logger.info(f"[{task_id}] MongoDB store result: {result}")

            output_path = f"{file_path}_{task_id}_output.json"
            df.to_json(output_path, orient="records", date_format="iso")
            logger.info(f"[{task_id}] Output written to {output_path}")

        task_status[task_id] = "completed"

    except Exception as e:
        logger.exception(f"[{task_id}] Task failed with exception: {str(e)}")
        task_status[task_id] = {
            "status": "failed",
            "error": str(e)
        }


@router.get("/task/{task_id}")
def check_task_status(task_id: str):
    return {"task_id": task_id, "status": task_status.get(task_id, "not_found")}

async def save_large_upload(upload_file: UploadFile, save_path: Path) -> int:
    total_size = 0
    with open(save_path, "wb") as outfile:
        while True:
            chunk = await upload_file.read(1024 * 1024)  # Read 1 MB at a time
            if not chunk:
                break
            outfile.write(chunk)
            total_size += len(chunk)
    return total_size
