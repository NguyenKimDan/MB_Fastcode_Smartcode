
from fastapi import APIRouter, UploadFile, File
from .database import SessionLocal
from .models import LogEntry
import re

router = APIRouter(prefix="/log", tags=["log"])

# API này tương thích với UI và PostgreSQL
@router.post("/parse")
def parse_log(file: UploadFile = File(...)):
    db = SessionLocal()
    content = file.file.read().decode("utf-8")
    lines = content.splitlines()
    pattern = re.compile(r"DB:(?P<db>[^,]+),sql:(?P<sql>.*?),exec_time_ms:(?P<time>\d+),exec_count:(?P<count>\d+)")
    imported = 0
    errors = 0
    for line in lines:
        match = pattern.match(line.strip())
        if match:
            db_name = match.group("db")
            sql_query = match.group("sql")
            exec_time_ms = int(match.group("time"))
            exec_count = int(match.group("count"))
            entry = LogEntry(db_name=db_name, sql_query=sql_query, exec_time_ms=exec_time_ms, exec_count=exec_count)
            db.add(entry)
            imported += 1
        else:
            errors += 1
    db.commit()
    db.close()
    return {"message": f"Đã phân tích xong file log. Thành công: {imported}, lỗi: {errors}"}
