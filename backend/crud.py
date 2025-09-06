from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import LogEntry, AbnormalQuery
from typing import List


router = APIRouter(prefix="/crud", tags=["crud"])


# API phát hiện truy vấn bất thường
@router.get("/scan_abnormal")
def scan_abnormal():
    db = SessionLocal()
    abnormal = db.query(LogEntry).filter(LogEntry.exec_time_ms > 500, LogEntry.exec_count > 100).all()
    result = []
    for q in abnormal:
        result.append({
            "db_name": q.db_name,
            "sql_query": q.sql_query,
            "exec_time_ms": q.exec_time_ms,
            "exec_count": q.exec_count,
            "status": "Bất thường"
        })
    db.close()
    return {
        "total": len(result),
        "abnormal_queries": result,
        "message": "Không phát hiện truy vấn bất thường nào" if not result else "Đã phát hiện truy vấn bất thường"
    }
@router.get("/log_entries")
def get_log_entries():
    db = SessionLocal()
    logs = db.query(LogEntry).all()
    db.close()
    return logs

@router.get("/databases")
def get_databases():
    db = SessionLocal()
    db_names = db.query(LogEntry.db_name).distinct().all()
    return [db[0] for db in db_names]

@router.get("/queries/{db_name}")
def get_queries_by_db(db_name: str):
    db = SessionLocal()
    queries = db.query(LogEntry).filter(LogEntry.db_name == db_name).all()
    if not queries:
        return {"message": "Không tìm thấy truy vấn nào cho DB này"}
    return queries
