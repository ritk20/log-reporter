import os
import logging
from datetime import datetime
import re
from fastapi import APIRouter, File, UploadFile,HTTPException,BackgroundTasks
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.utils.log_parser import parser_log_file_from_content, combine_logs
import json
import zipfile
import tempfile
from pathlib import Path
import uuid
task_status={}

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
        raise HTTPException(400, "The file is not in Zip format")\
    # write the file to the disk
    # spawn the background task to process the file
    # create the new task Id for the file processing and return it to the user
    # task_id  = str(uuid.uuid4())
    # # store the file in heelo_ther
    # file_path = "hello_ther.zip"
    # # store the task id and file path in a database or in-memory store if needed [task_id: file_path]
    # run_in_thread_pool(task_id)
    # return task_id
    try:
        task_id=str(uuid.uuid4())
        upload_file=Path("upload")
        upload_file.mkdir(parents=True,exist_ok=True)
        save_path = upload_file / f"{task_id}_{file.filename}"
        
        # Create temporary directory for extraction
    
        content_bytes = await file.read()
            
        with open(save_path, "wb") as f:
                f.write(content_bytes)
            
        logger.info(f"Received ZIP file: {file.filename}")
        logger.info(f"File size: {len(content_bytes)} bytes")

            
        task_status[task_id] = "processing"

        # 4. Spawn background task
        background_task.add_task(process_zip_file, task_id, str(save_path))

        # 5. Return the task ID immediately
        return {"task_id": task_id, "status": "processing"}

    except Exception as e:
        logger.exception("Failed to handle uploaded file")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
def process_zip_file(task_id: str, file_path: str):
    try:
        temp_dir = tempfile.mkdtemp()
        # Extract ZIP file
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            extracted_files = []
            for zip_info in zip_ref.infolist():
                if not zip_info.is_dir():
                    zip_ref.extract(zip_info, temp_dir)
                    extracted_files.append(zip_info.filename)

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
                logger.warning(f"Skipping non-text file: {extracted_file}")
            except Exception as e:
                logger.error(f"Error processing {extracted_file}: {str(e)}")

        if all_parsed_logs:
            df = combine_logs(all_parsed_logs)
            df.to_json(f"{file_path}_{task_id}_output.json", orient="records", date_format="iso")

        # Optionally update task status somewhere
        task_status[task_id] = "completed"
    except Exception as e:
        logger.exception(f"Task {task_id} failed: {str(e)}")
        task_status[task_id] = "failed"

@router.get("/task/{task_id}")
def check_task_status(task_id: str):
    return {"task_id": task_id, "status": task_status.get(task_id, "not_found")}
