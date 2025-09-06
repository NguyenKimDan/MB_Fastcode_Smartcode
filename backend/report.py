
from fastapi import APIRouter, HTTPException
from .database import SessionLocal
from .models import LogEntry
import csv
from fastapi.responses import StreamingResponse, Response
from io import StringIO, BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import datetime

router = APIRouter(prefix="/report", tags=["report"])

def get_abnormal_and_suggestion():
    db = SessionLocal()
    logs = db.query(LogEntry).all()
    abnormal = []
    for q in logs:
        is_abnormal = q.exec_time_ms > 500 and q.exec_count > 100
        suggestion = ""  # Gợi ý tối ưu hóa
        # Phân tích mệnh đề WHERE để gợi ý index
        if "WHERE" in q.sql_query.upper():
            where_clause = q.sql_query.upper().split("WHERE", 1)[1]
            fields = [f.strip().split()[0] for f in where_clause.split("AND")]
            if fields:
                suggestion = ", ".join([f"Thêm index trên {field}" for field in fields])
        if is_abnormal:
            abnormal.append({
                "db_name": q.db_name,
                "sql_query": q.sql_query,
                "exec_time_ms": q.exec_time_ms,
                "exec_count": q.exec_count,
                "status": "Bất thường",
                "suggestion": suggestion
            })
    db.close()
    return abnormal

@router.get("/summary")
def get_summary():
    db = SessionLocal()
    total_queries = db.query(LogEntry).count()
    abnormal = get_abnormal_and_suggestion()
    abnormal_count = len(abnormal)
    suggestion_count = sum(1 for q in abnormal if q["suggestion"])
    db.close()
    return {
        "total_queries": total_queries,
        "abnormal_count": abnormal_count,
        "suggestion_count": suggestion_count,
        "abnormal_queries": abnormal
    }

@router.get("/export/csv")
def export_csv():
    try:
        abnormal = get_abnormal_and_suggestion()
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["DB", "SQL", "ExecTime", "ExecCount", "Status", "Suggestion"])
        for q in abnormal:
            writer.writerow([q["db_name"], q["sql_query"], q["exec_time_ms"], q["exec_count"], q["status"], q["suggestion"]])
        output.seek(0)
        return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=report.csv"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Xuất file CSV thất bại: {str(e)}")

@router.get("/export/pdf")
def export_pdf():
    try:
        abnormal = get_abnormal_and_suggestion()
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, 750, "BÁO CÁO TRUY VẤN BẤT THƯỜNG")
        c.setFont("Helvetica", 10)
        c.drawString(100, 735, f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        y = 710
        c.setFont("Helvetica-Bold", 10)
        c.drawString(100, y, "DB | SQL | Time(ms) | Count | Status | Suggestion")
        y -= 15
        c.setFont("Helvetica", 9)
        for q in abnormal:
            line = f"{q['db_name']} | {q['sql_query'][:40]}... | {q['exec_time_ms']} | {q['exec_count']} | {q['status']} | {q['suggestion']}"
            c.drawString(100, y, line)
            y -= 13
            if y < 50:
                c.showPage()
                y = 750
        c.save()
        pdf = buffer.getvalue()
        buffer.close()
        return Response(content=pdf, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=report.pdf"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Xuất file PDF thất bại: {str(e)}")
