from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from db.database import get_db
from models.sql_log import SQLLog
import pandas as pd
from fpdf import FPDF
import json
from datetime import datetime
import os
from typing import List

router = APIRouter()

def generate_csv_report(data: List[dict], filename: str):
    """Tạo file CSV từ dữ liệu"""
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    return filename

def generate_pdf_report(data: List[dict], filename: str):
    """Tạo file PDF từ dữ liệu"""
    pdf = FPDF()
    pdf.add_page()
    
    # Tiêu đề
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(190, 10, 'Báo Cáo Phân Tích SQL Logs', 0, 1, 'C')
    pdf.cell(190, 10, f'Ngày: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'C')
    
    # Thống kê tóm tắt
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(190, 10, 'Thống Kê Tổng Quan:', 0, 1)
    pdf.set_font('Arial', '', 12)
    pdf.cell(190, 10, f'Tổng số truy vấn: {len(data)}', 0, 1)
    pdf.cell(190, 10, f'Số truy vấn bất thường: {sum(1 for d in data if d["is_anomaly"])}', 0, 1)
    
    # Chi tiết truy vấn
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(190, 10, 'Chi Tiết Truy Vấn:', 0, 1)
    
    # Headers
    headers = ['Database', 'Query', 'Exec Time', 'Exec Count', 'Status']
    col_widths = [30, 70, 30, 30, 30]
    
    pdf.set_font('Arial', 'B', 10)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, 1)
    pdf.ln()
    
    # Data
    pdf.set_font('Arial', '', 8)
    for row in data:
        pdf.cell(30, 10, row['database'][:20], 1)
        pdf.cell(70, 10, row['sql'][:50], 1)
        pdf.cell(30, 10, str(row['execution_time']), 1)
        pdf.cell(30, 10, str(row['execution_count']), 1)
        pdf.cell(30, 10, 'Anomaly' if row['is_anomaly'] else 'Normal', 1)
        pdf.ln()
    
    pdf.output(filename)
    return filename

@router.get("/generate")
async def generate_report(format: str = "json", db: Session = Depends(get_db)):
    """
    Tạo báo cáo tổng hợp
    format: json, csv, pdf
    """
    try:
        # Lấy dữ liệu từ database
        queries = db.query(SQLLog).all()
        
        # Chuẩn bị dữ liệu
        data = []
        for query in queries:
            row = {
                "database": query.database_name,
                "sql": query.sql_query,
                "execution_time": round(query.execution_time, 2),
                "execution_count": query.execution_count,
                "is_anomaly": query.is_anomaly,
                "optimization_suggestions": json.loads(query.optimization_suggestions) if query.optimization_suggestions else [],
                "optimization_reasons": json.loads(query.optimization_reasons) if query.optimization_reasons else []
            }
            data.append(row)
        
        # Thống kê
        stats = {
            "total_queries": len(queries),
            "anomalous_queries": sum(1 for q in queries if q.is_anomaly),
            "total_suggestions": sum(len(json.loads(q.optimization_suggestions)) if q.optimization_suggestions else 0 for q in queries)
        }
        
        if format == "json":
            return {
                "statistics": stats,
                "queries": data,
                "timestamp": datetime.now().isoformat()
            }
            
        elif format == "csv":
            filename = "report.csv"
            generate_csv_report(data, filename)
            return FileResponse(
                filename,
                media_type="text/csv",
                filename=f"sql_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            
        elif format == "pdf":
            filename = "report.pdf"
            generate_pdf_report(data, filename)
            return FileResponse(
                filename,
                media_type="application/pdf",
                filename=f"sql_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            
        else:
            raise HTTPException(status_code=400, detail="Định dạng không hợp lệ")
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi tạo báo cáo: {str(e)}"
        )
