

from fastapi import APIRouter, HTTPException
from .database import SessionLocal
from .models import LogEntry
import csv
import os
from fastapi.responses import StreamingResponse, Response
from io import StringIO, BytesIO
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
import datetime
import re
import os

# Register Vietnamese font
FONT_PATHS = [
    os.path.join(os.environ['WINDIR'], 'Fonts', 'arial.ttf'),  # Arial
    os.path.join(os.environ['WINDIR'], 'Fonts', 'ARIALUNI.TTF'),  # Arial Unicode MS
    os.path.join(os.environ['WINDIR'], 'Fonts', 'Tahoma.ttf'),  # Tahoma
    os.path.join(os.environ['WINDIR'], 'Fonts', 'segoeui.ttf'),  # Segoe UI
    os.path.join(os.environ['WINDIR'], 'Fonts', 'msyh.ttc'),  # Microsoft YaHei
]

font_registered = False
for font_path in FONT_PATHS:
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('ArialUnicode', font_path))
            print(f"Using font: {font_path}")
            font_registered = True
            break
        except:
            continue

if not font_registered:
    print("Warning: No suitable Unicode font found. Vietnamese text may not display correctly.")

router = APIRouter(prefix="/report", tags=["report"])

def get_abnormal_and_suggestion():
    db = SessionLocal()
    logs = db.query(LogEntry).all()
    abnormal = []
    for q in logs:
        is_abnormal = q.exec_time_ms > 500 and q.exec_count > 100
        suggestion = "Khuyến nghị xem xét thủ công"  # Mặc định nếu không phân tích được
        sql = q.sql_query
        # Phân tích mệnh đề WHERE để gợi ý index
        if "WHERE" in sql.upper():
            try:
                where_clause = sql.split("WHERE", 1)[1]
                # Tách các điều kiện bằng AND
                conditions = [cond.strip() for cond in where_clause.split("AND")]
                fields = []
                for cond in conditions:
                    # Lấy tên trường trước dấu =, >, <, LIKE, IN...
                    match = re.match(r"([a-zA-Z0-9_]+)", cond)
                    if match:
                        fields.append(match.group(1))
                if fields:
                    suggestion = ", ".join([f"Thêm index trên {field}" for field in fields])
            except Exception:
                suggestion = "Khuyến nghị xem xét thủ công"
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
        
        # Sử dụng csv.writer với quoting để tránh lỗi với nội dung đặc biệt
        writer = csv.writer(
            output, 
            delimiter=',',
            quotechar='"', 
            quoting=csv.QUOTE_ALL
        )
        
        # Viết header tiếng Việt với encoding đúng
        writer.writerow([
            "Tên Database",
            "Câu lệnh SQL",
            "Thời gian thực thi (ms)",
            "Số lần thực thi",
            "Trạng thái",
            "Gợi ý tối ưu"
        ])
        
        # Viết dữ liệu, đảm bảo encode đúng và xử lý các ký tự đặc biệt
        for q in abnormal:
            writer.writerow([
                str(q["db_name"]).strip(),
                str(q["sql_query"]).strip(),
                str(q["exec_time_ms"]),
                str(q["exec_count"]),
                str(q["status"]).strip(),
                str(q["suggestion"]).strip()
            ])
            
        output.seek(0)
        
        # Đảm bảo encoding UTF-8 với BOM để Excel đọc được tiếng Việt
        filename = f"bao_cao_truy_van_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return StreamingResponse(
            BytesIO(output.getvalue().encode('utf-8-sig')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Xuất file CSV thất bại: {str(e)}")

@router.get("/export/pdf")
def export_pdf():
    try:
        abnormal = get_abnormal_and_suggestion()
        buffer = BytesIO()
        
        # Tạo PDF với SimpleDocTemplate để có bảng đẹp
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )

        # Tạo các elements cho PDF
        elements = []
        
        # Tiêu đề và thông tin báo cáo với font Unicode
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName='ArialUnicode',
            fontSize=16,
            alignment=1,  # Center alignment
            spaceAfter=20,
            leading=20
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName='ArialUnicode',
            fontSize=11,
            alignment=1,
            spaceAfter=20
        )
        
        elements.append(Paragraph("BÁO CÁO TRUY VẤN BẤT THƯỜNG", title_style))
        elements.append(Paragraph(f"Thời gian: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", normal_style))
        elements.append(Spacer(1, 20))

        # Tạo style cho header với font Unicode
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=styles['Heading2'],
            fontName='ArialUnicode',
            fontSize=10,
            alignment=1,
            leading=12
        )

        # Tạo dữ liệu cho bảng với Paragraph để tự động wrap text
        tabledata = [[
            Paragraph("Tên Database", header_style),
            Paragraph("Câu lệnh SQL", header_style),
            Paragraph("Thời gian (ms)", header_style),
            Paragraph("Số lần thực thi", header_style),
            Paragraph("Trạng thái", header_style),
            Paragraph("Gợi ý tối ưu", header_style)
        ]]

        cell_style = ParagraphStyle(
            'CellStyle',
            parent=styles['Normal'],
            fontName='ArialUnicode',
            fontSize=9,
            leading=12,
            wordWrap='CJK'  # Hỗ trợ wrap text tốt hơn
        )
        
        for q in abnormal:
            # Wrap tất cả text trong Paragraph
            tabledata.append([
                Paragraph(str(q['db_name']), cell_style),
                Paragraph(q['sql_query'], cell_style),
                Paragraph(str(q['exec_time_ms']), cell_style),
                Paragraph(str(q['exec_count']), cell_style),
                Paragraph(str(q['status']), cell_style),
                Paragraph(str(q['suggestion']), cell_style)
            ])

        # Tạo bảng với style đẹp và tự động điều chỉnh chiều cao
        table = Table(
            tabledata, 
            repeatRows=1, 
            colWidths=[1.2*inch, 2.5*inch, 0.8*inch, 0.8*inch, 1*inch, 2*inch],
            rowHeights=None  # Tự động điều chỉnh chiều cao
        )
        table.setStyle(TableStyle([
            # Header style
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Vertical alignment for all cells
            ('FONT', (0, 0), (-1, 0), 'ArialUnicode', 11),  # Header font
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONT', (0, 1), (-1, -1), 'ArialUnicode', 10),  # Data font
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LINEBEFORE', (0, 0), (-1, -1), 1, colors.black),
            ('LINEAFTER', (0, 0), (-1, -1), 1, colors.black),
            ('LINEBELOW', (0, 0), (-1, -1), 1, colors.black),
            ('LINEABOVE', (0, 0), (-1, -1), 1, colors.black),
            
            # Word wrapping
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f4f6fa')])
        ]))
        
        elements.append(table)

        # Build PDF
        doc.build(elements)
        
        # Return PDF file với tên file có timestamp
        pdf = buffer.getvalue()
        buffer.close()
        filename = f"bao_cao_truy_van_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Xuất file PDF thất bại: {str(e)}")
