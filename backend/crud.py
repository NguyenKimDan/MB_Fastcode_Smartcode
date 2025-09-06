from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import LogEntry, AbnormalQuery
from typing import List

router = APIRouter(prefix="/crud", tags=["crud"])

@router.get("/log_entries")
def get_log_entries():
    db = SessionLocal()
    logs = db.query(LogEntry).all()
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
