# Logs Analyzer

## Setup Instructions

    git clone https://github.com/ritk20/log-reporter

### Frontend

    cd frontend
    npm install
    npm run dev

### Backend

    cd backend
    # Setup virtual env (recommended)
    pip install -r requirements.txt
    uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
