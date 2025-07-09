import tempfile, zipfile, shutil, logging
from pathlib import Path
from datetime import datetime, timezone
from app.utils.log_parser import parser_log_file_from_content, combine_logs
from app.utils.log_storage import LogStorageService
from .task_manager import update_task
from app.api.analytics import generate_summary_report
from app.utils.performance_monitor import performance_monitor
import time


logger = logging.getLogger(__name__)

@performance_monitor
def process_zip_file(task_id: str, file_path: str, user_info: dict):
    try:

        temp_dir = tempfile.mkdtemp()
        extracted_files = []
        # Update status to extraction
        logger.info("Starting file extraction")
        update_task(task_id, {
            "status": "extracting files",
            "progress": {"current": 0, "total": 0}
        })

        unzipping_start = time.perf_counter()
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            total_files = len([f for f in zip_ref.filelist if not f.is_dir()])
            processed_files = 0
            
            for zip_info in zip_ref.infolist():
                if zip_info.is_dir():
                    continue
                extracted_path = zip_ref.extract(zip_info, temp_dir)
                extracted_files.append(extracted_path)
                processed_files += 1

                update_task(task_id, {
                    "status": "extracting_files",
                    "progress": {
                        "current": processed_files,
                        "total": total_files,
                        "message": f"Extracting file {processed_files} of {total_files}"
                    }
                })
        
        unzipping_time = time.perf_counter() - unzipping_start
        print(f"Unzipping: {unzipping_time:.6f} seconds")

        # Update status to parsing
        logger.info("Starting log parsing")
        update_task(task_id, {
            "status": "parsing_logs",
            "progress": {"current": 0, "total": len(extracted_files)}
        })

        parsing_start = time.perf_counter()
        all_parsed_logs = []
        for file in extracted_files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()
                    logs = parser_log_file_from_content(content)
                    all_parsed_logs.extend(logs)
            except Exception as e:
                logger.warning(f"Failed to parse file {file}: {e}")
        logger.info(f"Parsed {len(all_parsed_logs)} logs from {len(extracted_files)} files.")
        parsing_time = time.perf_counter() - parsing_start
        print(f"Parsing: {parsing_time:.6f} seconds")

        logger.info("Starting logs to dataframe conversion")
        if all_parsed_logs:
            update_task(task_id, {
                "status": "processing_records"
            })
            df = combine_logs(all_parsed_logs)
            records = df.to_dict("records")

            logger.info("Storing data in mongodb")
            update_task(task_id, {
                "status": "storing_data"
            })
            info = LogStorageService.store_logs_batch(records, task_id)
            df.to_json(f"{file_path}_{task_id}_output.json", orient="records")

            logger.info("Starting Analysis")
            update_task(task_id, {
                "status": "Analysing data"
            })
            generate_summary_report()

        update_task(task_id, {
            "status": "completed",
            "user": user_info.get('username', 'unknown'),
            "filename": Path(file_path).name,
            "end_time": datetime.now(timezone.utc).isoformat()
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
