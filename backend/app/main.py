from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.log_parser import parser_log_file_from_content,combine_logs
import os
import logging
import json

# configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Allow frontend on localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload-log/")
async def upload_log_file(file: UploadFile = File(...)):
    try:
        content_bytes = await file.read()
        logger.info(f"Received file: {file.filename}")
        logger.info(f"File size: {len(content_bytes)} bytes")

        content = content_bytes.decode("utf-8")
        parsed_logs = parser_log_file_from_content(content)  # No need for log_parser module if in same file
        df = combine_logs(parsed_logs)

        # Convert DataFrame to JSON with ISO date format
        return JSONResponse(content=json.loads(df.to_json(orient="records", date_format="iso")), status_code=200)

    except UnicodeDecodeError as ude:
        logger.exception("File is not a valid UTF-8 text file")
        return JSONResponse(content={"error": "File must be a UTF-8 encoded text file"}, status_code=400)

    except Exception as e:
        logger.exception("Unexpected error during log file processing")
        return JSONResponse(content={"error": f"Failed to process log file: {str(e)}"}, status_code=400)