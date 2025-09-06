from fastapi import APIRouter
from .database import SessionLocal
from .models import LogEntry, AbnormalQuery
import csv
from fastapi.responses import StreamingResponse
from io import StringIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from fastapi.responses import Response
import datetime

router = APIRouter(prefix="/report", tags=["report"])

@router.get("/summary")
def get_summary():
    db = SessionLocal()
    total_queries = db.query(LogEntry).count()
    abnormal_count = db.query(AbnormalQuery).count()
    return {
        "total_queries": total_queries,
        "abnormal_count": abnormal_count,
    }

@router.get("/export/csv")
def export_csv():
    db = SessionLocal()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["DB", "SQL", "ExecTime", "ExecCount", "Status", "Suggestion"])
    for q in db.query(AbnormalQuery).all():
        writer.writerow([q.db_name, q.sql_query, q.exec_time_ms, q.exec_count, q.status, q.suggestion])
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=report.csv"})

@router.get("/export/pdf")
def export_pdf():
    db = SessionLocal()
    buffer = StringIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(100, 750, "Báo cáo truy vấn bất thường")
    c.drawString(100, 735, f"Timestamp: {datetime.datetime.now()}")
    y = 700
    for q in db.query(AbnormalQuery).all():
        c.drawString(100, y, f"DB: {q.db_name}, SQL: {q.sql_query[:50]}, Time: {q.exec_time_ms}, Count: {q.exec_count}, Status: {q.status}")
        y -= 15
        if y < 50:
            c.showPage()
            y = 750
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return Response(content=pdf, media_type="application/pdf")
