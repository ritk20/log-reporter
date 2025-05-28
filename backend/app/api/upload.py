import os
import logging
from datetime import datetime
import re
from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.log_parser import parser_log_file_from_content, combine_logs
import json

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
    try:
        content_bytes = await file.read()
        logger.info(f"Received file: {file.filename}")
        logger.info(f"File size: {len(content_bytes)} bytes")

        content = content_bytes.decode("utf-8")
        parsed_logs = parser_log_file_from_content(content)  # No need for log_parser module if in same file
        df = combine_logs(parsed_logs)

        # Create a JSON response
        json_response = df.to_json(orient="records", date_format="iso")
        
        # Create output directory if it doesn't exist
        output_dir = os.path.join(UPLOAD_DIR, 'processed')
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate output filename based on input filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"processed_{timestamp}.json"
        output_path = os.path.join(output_dir, output_filename)
        
        # Save JSON to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json.loads(json_response), f, indent=2)
            
        logger.info(f"Processed data saved to: {output_path}")

        # Return response to client
        return JSONResponse(
            content={
                "message": "File processed successfully",
                "output_file": output_filename,
                "data": json.loads(json_response)
            }, 
            status_code=200
        )

    except UnicodeDecodeError as ude:
        logger.exception("File is not a valid UTF-8 text file")
        return JSONResponse(content={"error": "File must be a UTF-8 encoded text file"}, status_code=400)

    except Exception as e:
        logger.exception("Unexpected error during log file processing")
        return JSONResponse(content={"error": f"Failed to process log file: {str(e)}"}, status_code=400)
    
    #TODO: Validate filename and save file to UPLOAD_DIR
    # logger.info(f"Received file: {file.filename}")
    
    # valid, error_message = validate_filename(file.filename)
    # if not valid:
    #     logger.warning(f"Validation failed: {error_message}")
    #     return JSONResponse(status_code=400, content={"detail": error_message})
    
    # try:
    #     file_location = os.path.join(UPLOAD_DIR, file.filename)
    #     with open(file_location, "wb") as f:
    #         content = await file.read()
    #         f.write(content)
    #     logger.info(f"File saved to {file_location}")
    #     return JSONResponse(content={"detail": f"File '{file.filename}' uploaded successfully!"})
    # except Exception as e:
    #     logger.error(f"Error uploading file: {str(e)}")
    #     return JSONResponse(
    #         status_code=500,
    #         content={"detail": "Internal server error during upload"}
    #     )
    