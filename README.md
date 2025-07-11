# Logs Reporter
This is a full-stack web application to display analytics of log files 

# 🚀 Technology Stack
- Frontend: React with Vite  
- Backend: FastAPI (Python)  
- Database: MongoDB

# 📁 Project Structure

```
project-root/
│
├── backend/              # FastAPI app
│   ├── app/
│   │   ├── main.py
│   └── requirements.txt
│
├── frontend/             # React + Vite app
│   ├── index.html
│   ├── src/
│   └── package.json
│
├── docker-compose.yml
└── README.md
```

## 🧑‍💻 1. Running Locally (without Docker)
🔧 Prerequisites
- Python 3.9+
- Node.js + npm
- MongoDB running locally (default port: 27017)

#### 📦 Backend Setup (FastAPI)

```
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 🌐 Frontend Setup (React + Vite)
```
cd frontend
npm install
npm run dev
```
#### ⚙️ Environment Configuration
Refer to `env.txt` for environment configuration details.

Create a `.env` file in the root directory based on this template.

## 🐳 2. Running with Docker

#### ▶️ Run with Docker
> Ensure `.env` file is set properly, refer to `env.txt` for changes

Run the following command from the project root:
```
docker-compose up --build -d
```
access frontend at `https://localhost:3000`

access backend at `https://localhost:8000`

## ☁️ 3. Deploying on Google Cloud Platform (GCP)

#### 📝 Notes
> Ensure `.env` file is set properly for production (avoid localhost), refer to `env.txt` for changes

#### 🚀 Deployment Steps
After setting up your GCP VM and transferring the project files:

- SSH into your VM.

- Navigate to the project root.

- Run the following command:

```
docker-compose up --build -d
```
access frontend at `http://34.100.235.138:5044`

access backend at `http://34.100.235.138:5044/backend`

>Note: These URLs assume a reverse proxy (NGINX) is routing frontend through port 5044 and the backend is routed through NGINX under the /backend path. 
 Adjust your NGINX configuration as needed for production readiness.
