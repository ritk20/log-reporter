
import logging
import hashlib
from datetime import datetime
import re
import zipfile
import tempfile
from pathlib import Path
import uuid
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.utils.log_parser import parser_log_file_from_content, combine_logs
from app.utils.log_storage import LogStorageService
from app.utils.thread_pool_processing import run_in_thread_pool
from app.api.auth_jwt import verify_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upload", tags=["Upload"])

FILENAME_REGEX = re.compile(settings.FILENAME_REGEX)

task_status = {}
processed_zip_hashes = set()
processed_file_hashes = set()

def calculate_file_hash(file_path: Path) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

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

@router.post("/upload", tags=["File Operations"])

async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(verify_token)  # This verifies authentication
):
    # Log authentication info immediately
    logger.info(f"Upload request from user: {current_user.get('username', 'unknown')}")
    logger.info(f"User roles: {current_user.get('roles', [])}")
    logger.info(f"Authentication method: {current_user.get('auth_method', 'unknown')}")

    if not file.filename.endswith(".zip"):
        raise HTTPException(400, "The file is not in Zip format")

    try:
        task_id = str(uuid.uuid4())
        upload_file_dir = Path("upload")
        upload_file_dir.mkdir(parents=True, exist_ok=True)
        save_path = upload_file_dir / f"{file.filename}"

        file_size = await save_large_upload(file, save_path)
        file_hash = calculate_file_hash(save_path)

        # Include user info in the duplicate check message
        if file_hash in processed_zip_hashes:
            logger.warning(f"Duplicate ZIP upload attempted by {current_user.get('username')}: {file.filename}")
            return JSONResponse(
                status_code=200,
                content={
                    "message": "This ZIP file has already been uploaded and processed",
                    "user": current_user.get('username'),
                    "authenticated": True
                }
            )

        processed_zip_hashes.add(file_hash)
        logger.info(f"Received ZIP file from authenticated user {current_user.get('username')}: {file.filename}, Size: {file_size} bytes")
        
        # store the file locally - path : os.getcwd() + "file_tmp_path"
        task_status[task_id] = {
            "status": "processing",
            "user": current_user.get('username'),
            "authenticated": True,
            "auth_time": datetime.utcnow().isoformat()
        }

        run_in_thread_pool(process_zip_file, task_id, str(save_path), current_user)
        
        return {
            "task_id": task_id,
            "status": "processing",
            "user": current_user.get('username'),
            "authenticated": True,
            "message": "Upload accepted"
        }

    except Exception as e:
        logger.exception(f"Upload failed for user {current_user.get('username')}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "authenticated": True,
                "user": current_user.get('username')
            }
        )
def process_zip_file(task_id: str, file_path: str, user_info: dict):
    import shutil
    try:
        temp_dir = tempfile.mkdtemp()
        extracted_files = []

        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            for zip_info in zip_ref.infolist():
                if zip_info.is_dir():
                    continue
                extracted_path = zip_ref.extract(zip_info, temp_dir)

                nested_hash = calculate_file_hash(Path(extracted_path))
                if nested_hash in processed_file_hashes:
                    continue
                processed_file_hashes.add(nested_hash)
                extracted_files.append(extracted_path)

        all_parsed_logs = []
        for file in extracted_files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()
                    logs = parser_log_file_from_content(content)
                    # Add user information to each log entry
                    for log in logs:
                        log['uploaded_by'] = user_info.get('username', 'unknown')
                        log['user_id'] = user_info.get('user_id', 'unknown')
                    all_parsed_logs.extend(logs)
            except Exception as e:
                logger.warning(f"Failed to parse file {file}: {e}")

        if all_parsed_logs:
            df = combine_logs(all_parsed_logs)
            records = df.to_dict("records")
            LogStorageService.store_logs_batch(records)
            df.to_json(f"{file_path}_{task_id}_output.json", orient="records")

        task_status[task_id] = {
            "status": "completed",
            "user": user_info.get('username', 'unknown'),
            "filename": Path(file_path).name,
            "end_time": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.exception(f"Failed to process zip: {e}")
        task_status[task_id] = {
            "status": "failed", 
            "error": str(e),
            "user": user_info.get('username', 'unknown'),
            "filename": Path(file_path).name
        }
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
@router.get("/task/{task_id}")
def check_task_status(task_id: str, current_user: dict = Depends(verify_token)):
    task = task_status.get(task_id)
    if not task:
        return {
            "error": "Task not found",
            "authenticated": True,
            "user": current_user.get('username')
        }
    
    # Add authentication verification to the response
    response = {
        "task_id": task_id,
        "status": task.get("status"),
        "requested_by": current_user.get('username'),
        "task_owner": task.get("user"),
        "is_owner": current_user.get('username') == task.get("user"),
        "authenticated": True
    }
    
    # Only show full details to task owner or admins
    if current_user.get('username') == task.get("user") or "admin" in current_user.get('roles', []):
        response.update({
            "filename": task.get("filename"),
            "start_time": task.get("start_time"),
            "details": task  # Include all task details
        })
    else:
        response["message"] = "Limited view: only task owners can see full details"
    
    return response
@router.get("/verify-auth")
async def verify_authentication(current_user: dict = Depends(verify_token)):
    return {
        "authenticated": True,
        "user_info": current_user,
        "token_valid": True,
        "timestamp": datetime.utcnow().isoformat()
    }