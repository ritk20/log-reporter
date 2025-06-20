# backend/Dockerfile
FROM python:3.10-slim

# set workdir
WORKDIR /app

# copy and install dependencies
COPY backend/requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# copy your backend code
COPY backend/ .

# expose FastAPI port
EXPOSE 8000

# start Uvicorn, pointing at your FastAPI app in backend/app/main.py
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]