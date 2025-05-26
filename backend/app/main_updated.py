from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import logging
from datetime import datetime
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

FILENAME_REGEX = re.compile(r"transactions_(\d{8})\.zip")

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

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    logger.info(f"Received file: {file.filename}")
    
    valid, error_message = validate_filename(file.filename)
    if not valid:
        logger.warning(f"Validation failed: {error_message}")
        return JSONResponse(status_code=400, content={"detail": error_message})
    
    try:
        file_location = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_location, "wb") as f:
            content = await file.read()
            f.write(content)
        logger.info(f"File saved to {file_location}")
        return JSONResponse(content={"detail": f"File '{file.filename}' uploaded successfully!"})
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error during upload"}
        )
