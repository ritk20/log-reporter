from typing import Dict

task_status: Dict[str, dict] = {}

def create_task(task_id: str, user: str):
    from datetime import datetime, timezone
    task_status[task_id] = {
        "status": "processing",
        "user": user,
        "authenticated": True,
        "auth_time": datetime.now(timezone.utc).isoformat()
    }

def update_task(task_id: str, data: dict):
    task_status[task_id].update(data)

def get_task(task_id: str):
    return task_status.get(task_id)
