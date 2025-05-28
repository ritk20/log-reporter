import os
import logging
from datetime import datetime
import re
from fastapi import APIRouter, File, UploadFile,HTTPException
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.log_parser import parser_log_file_from_content, combine_logs
import json
import zipfile
import tempfile
from pathlib import Path

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
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".zip"):
        raise HTTPException(400, "The file is not in Zip format")
    
    try:
        # Create temporary directory for extraction
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save the uploaded zip file
            filename=Path(file.filename).name
            zip_path = os.path.join(temp_dir, filename)
            content_bytes = await file.read()
            
            with open(zip_path, "wb") as f:
                f.write(content_bytes)
            
            logger.info(f"Received ZIP file: {file.filename}")
            logger.info(f"File size: {len(content_bytes)} bytes")

            # Extract the zip file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                extracted_files=[]
                for zip_info in zip_ref.infolist():
                    if not zip_info.is_dir():
                        zip_ref.extract(zip_info, temp_dir)
                        extracted_files.append(zip_info.filename)
            
            logger.info(f"Extracted files: {extracted_files}")

            # Process each extracted file
            all_parsed_logs = []
            for extracted_file in extracted_files:
                file_path = os.path.join(temp_dir, extracted_file)
                
                # Skip directories and non-text files if needed
                if os.path.isdir(file_path):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        parsed_logs = parser_log_file_from_content(content)
                        all_parsed_logs.extend(parsed_logs)
                except UnicodeDecodeError:
                    logger.warning(f"Skipping non-text file: {extracted_file}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing {extracted_file}: {str(e)}")
                    continue

            # Combine all logs
            if not all_parsed_logs:
                raise HTTPException(400, "No valid log files found in the ZIP archive")
            
            df = combine_logs(all_parsed_logs)

            # Convert DataFrame to JSON with ISO date format
            return JSONResponse(
                content=json.loads(df.to_json(orient="records", date_format="iso")),
                status_code=200
            )

    except zipfile.BadZipFile:
        logger.exception("Invalid ZIP file format")
        return JSONResponse(
            content={"error": "Invalid ZIP file format"},
            status_code=400
        )
    except Exception as e:
        logger.exception("Unexpected error during ZIP file processing")
        return JSONResponse(
            content={"error": f"Failed to process ZIP file: {str(e)}"},
            status_code=500
        )