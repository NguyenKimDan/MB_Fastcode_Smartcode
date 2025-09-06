
from fastapi import APIRouter, UploadFile, File, HTTPException
from .database import SessionLocal
from .models import LogEntry
import re

router = APIRouter(prefix="/log", tags=["log"])

# API này tương thích với UI và PostgreSQL
@router.post("/parse")
async def parse_log(file: UploadFile = File(...)):
    try:
        # Kiểm tra file
        if not file.filename.endswith('.log'):
            raise HTTPException(status_code=400, detail="Chỉ chấp nhận file .log")

        db = SessionLocal()
        try:
            content = await file.read()
            # Thử decode với các encoding khác nhau
            try:
                text_content = content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    text_content = content.decode('utf-16')
                except UnicodeDecodeError:
                    text_content = content.decode('utf-8', errors='ignore')

            lines = text_content.splitlines()
            if not lines:
                raise HTTPException(status_code=400, detail="File rỗng")

            pattern = re.compile(r"DB:(?P<db>[^,]+),sql:(?P<sql>.*?),exec_time_ms:(?P<time>\d+),exec_count:(?P<count>\d+)")
            imported = 0
            errors = 0
            error_lines = []

            # Xử lý từng dòng
            for line_num, line in enumerate(lines, 1):
                try:
                    line = line.strip()
                    if not line:  # Bỏ qua dòng trống
                        continue

                    match = pattern.match(line)
                    if match:
                        db_name = match.group("db").strip()
                        sql_query = match.group("sql").strip()
                        exec_time_ms = int(match.group("time"))
                        exec_count = int(match.group("count"))

                        # Validate dữ liệu
                        if not db_name or not sql_query:
                            raise ValueError("DB name hoặc SQL query không được để trống")
                        if exec_time_ms < 0 or exec_count < 0:
                            raise ValueError("Thời gian và số lần thực thi phải >= 0")

                        entry = LogEntry(
                            db_name=db_name,
                            sql_query=sql_query,
                            exec_time_ms=exec_time_ms,
                            exec_count=exec_count
                        )
                        db.add(entry)
                        imported += 1
                    else:
                        errors += 1
                        error_lines.append(f"Dòng {line_num}: Định dạng không đúng")
                except Exception as e:
                    errors += 1
                    error_lines.append(f"Dòng {line_num}: {str(e)}")

            # Lưu vào database
            if imported > 0:
                try:
                    db.commit()
                except Exception as e:
                    db.rollback()
                    raise HTTPException(
                        status_code=500,
                        detail=f"Lỗi khi lưu vào database: {str(e)}"
                    )

            return {
                "success": True,
                "message": f"Đã phân tích xong file log. Thành công: {imported}, lỗi: {errors}",
                "imported": imported,
                "errors": errors,
                "error_details": error_lines if error_lines else None
            }

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Lỗi xử lý file: {str(e)}"
            )
        finally:
            db.close()

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi hệ thống: {str(e)}"
        )
