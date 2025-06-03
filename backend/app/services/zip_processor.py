import tempfile, zipfile, shutil, logging
from pathlib import Path
from datetime import datetime
from app.utils.log_parser import parser_log_file_from_content, combine_logs
from app.utils.log_storage import LogStorageService
from .task_manager import update_task

logger = logging.getLogger(__name__)

def process_zip_file(task_id: str, file_path: str, user_info: dict):
    try:
        temp_dir = tempfile.mkdtemp()
        extracted_files = []

        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            for zip_info in zip_ref.infolist():
                if zip_info.is_dir():
                    continue
                extracted_path = zip_ref.extract(zip_info, temp_dir)
                extracted_files.append(extracted_path)

        all_parsed_logs = []
        for file in extracted_files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()
                    logs = parser_log_file_from_content(content)
                    all_parsed_logs.extend(logs)
            except Exception as e:
                logger.warning(f"Failed to parse file {file}: {e}")

        if all_parsed_logs:
            df = combine_logs(all_parsed_logs)
            records = df.to_dict("records")
            LogStorageService.store_logs_batch(records)
            df.to_json(f"{file_path}_{task_id}_output.json", orient="records")

        update_task(task_id, {
            "status": "completed",
            "user": user_info.get('username', 'unknown'),
            "filename": Path(file_path).name,
            "end_time": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.exception(f"Failed to process zip: {e}")
        update_task(task_id, {
            "status": "failed", 
            "error": str(e),
            "user": user_info.get('username', 'unknown'),
            "filename": Path(file_path).name
        })
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
