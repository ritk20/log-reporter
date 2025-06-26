import uuid, logging
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from datetime import datetime
from app.api.auth_jwt import verify_token
from app.services.file_saver import save_large_upload
from app.services.task_manager import create_task, get_task
from app.services.zip_processor import process_zip_file
from app.utils.thread_pool_processing import run_in_thread_pool
from app.core.config import settings
import re
from app.utils.performance_monitor import performance_monitor


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/upload", tags=["Upload"])

FILENAME_REGEX = re.compile(settings.FILENAME_REGEX)

def validate_filename(filename: str):
    match = FILENAME_REGEX.fullmatch(filename)
    if not match:
        return False, "Filename must be in format transactions_YYYYMMDD.zip"
    try:
        datetime.strptime(match.group(1), "%Y%m%d").date()
    except ValueError:
        return False, "Date in filename is invalid"
    
    return True, None

@performance_monitor
@router.post("/upload")
async def upload_file(file: UploadFile = File(...), current_user: dict = Depends(verify_token)):
    logger.info(f"Upload request from user: {current_user.get('username', 'unknown')}")

    valid, error_message = validate_filename(file.filename)
    if not valid:
        logger.warning(f"Validation failed: {error_message}")
        raise HTTPException(400, error_message)

    if not file.filename.endswith(".zip"):
        raise HTTPException(400, "The file is not in Zip format")

    try:
        task_id = str(uuid.uuid4())
        upload_dir = Path("upload")
        upload_dir.mkdir(parents=True, exist_ok=True)
        save_path = upload_dir / file.filename

        # file_size = await save_large_upload(file, save_path)
        with open(save_path, "wb") as outfile:
            outfile.write(await file.read())
        logger.info(f"Received ZIP: {file.filename}")

        create_task(task_id, current_user.get('username'))
        run_in_thread_pool(process_zip_file, task_id, str(save_path), current_user)

        return {
            "task_id": task_id,
            "status": "processing",
            "user": current_user.get('username'),
            "authenticated": True,
            "message": "Upload accepted"
        }

    except Exception as e:
        logger.exception("Upload failed")
        raise HTTPException(status_code=500, detail={"error": str(e)})

@router.get("/task/{task_id}")
def check_task_status(task_id: str, current_user: dict = Depends(verify_token)):
    task = get_task(task_id)
    if not task:
        return {
            "error": "Task not found",
            "authenticated": True,
            "user": current_user.get('username')
        }

    return {
        "task_id": task_id,
        "status": task.get("status"),
        "requested_by": current_user.get('username'),
        "task_owner": task.get("user"),
        "is_owner": current_user.get('username') == task.get("user"),
        "authenticated": True
    }

@router.get("/verify-auth")
async def verify_authentication(current_user: dict = Depends(verify_token)):
    return {
        "authenticated": True,
        "user_info": current_user,
        "token_valid": True,
        "timestamp": datetime.utcnow().isoformat()
    }
