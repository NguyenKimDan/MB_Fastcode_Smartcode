from fastapi import APIRouter, UploadFile, File
from .database import SessionLocal
from .models import LogEntry
import re

router = APIRouter(prefix="/log", tags=["log"])

@router.post("/parse")
def parse_log(file: UploadFile = File(...)):
    db = SessionLocal()
    content = file.file.read().decode("utf-8")
    lines = content.splitlines()
    for line in lines:
        try:
            # Giả sử định dạng: DB|SQL|ExecTime|ExecCount
            parts = line.split("|")
            db_name, sql_query, exec_time_ms, exec_count = parts
            entry = LogEntry(db_name=db_name, sql_query=sql_query, exec_time_ms=int(exec_time_ms), exec_count=int(exec_count))
            db.add(entry)
        except Exception:
            # Ghi log lỗi phân tích
            continue
    db.commit()
    return {"message": "Đã phân tích xong file log"}
