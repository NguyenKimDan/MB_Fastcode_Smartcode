import re
import os
import json
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from db.database import get_db
from models.sql_log import SQLLog
from schemas.sql_log import SQLLogCreate, SQLLog as SQLLogSchema, OptimizationSuggestion
from core.sql_analyzer import SQLAnalyzer
import logging
from datetime import datetime

# Thiết lập logging
logging.basicConfig(
    filename='app.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter()

class LogParsingError(Exception):
    """Custom exception for log parsing errors"""
    pass

def validate_log_format(line: str) -> bool:
    """
    Kiểm tra xem dòng log có đúng định dạng không
    Format chuẩn: Database: dbname, Query: SELECT..., Time: 123ms
    
    Quy tắc:
    1. Bắt đầu với "Database:"
    2. Tên database không được rỗng và không chứa dấu phẩy
    3. Tiếp theo là "Query:"
    4. SQL query không được rỗng
    5. Kết thúc với "Time:" và số dương + "ms"
    """
    if not line or not isinstance(line, str):
        return False
        
    try:
        # Kiểm tra format tổng quát
        pattern = r"^Database:\s*([^,]+),\s*Query:\s*(.+),\s*Time:\s*(\d+(?:\.\d+)?)ms$"
        match = re.match(pattern, line.strip())
        
        if not match:
            return False
            
        # Extract các thành phần để kiểm tra chi tiết
        db_name, query, exec_time = match.groups()
        
        # Kiểm tra tên database
        if not db_name.strip():
            return False
            
        # Kiểm tra query
        if not query.strip():
            return False
            
        # Kiểm tra thời gian
        exec_time_float = float(exec_time)
        if exec_time_float < 0:
            return False
            
        return True
    except:
        return False

def parse_log_entry(line: str, line_number: int) -> Optional[SQLLogCreate]:
    """
    Parse một dòng log và trả về SQLLogCreate object
    Raises LogParsingError nếu có lỗi định dạng
    """
    try:
        if not validate_log_format(line):
            raise LogParsingError(f"Invalid log format at line {line_number}: {line}")

        # Pattern để extract thông tin
        pattern = r"Database:\s*([^,]+),\s*Query:\s*([^,]+),\s*Time:\s*(\d+(?:\.\d+)?)ms"
        match = re.match(pattern, line.strip())
        
        if not match:
            raise LogParsingError(f"Cannot extract information at line {line_number}")
            
        db_name, query, exec_time = match.groups()
        
        # Validate các giá trị
        if not db_name.strip():
            raise LogParsingError(f"Empty database name at line {line_number}")
        if not query.strip():
            raise LogParsingError(f"Empty query at line {line_number}")
        
        return SQLLogCreate(
            database_name=db_name.strip(),
            sql_query=query.strip(),
            execution_time=float(exec_time),
            execution_count=1,
            error_message=None
        )
    except LogParsingError as e:
        logger.error(str(e))
        return None
    except Exception as e:
        error_msg = f"Unexpected error at line {line_number}: {str(e)}"
        logger.error(error_msg)
        return None

def validate_file(filepath: str) -> bool:
    """
    Kiểm tra tính hợp lệ của file
    1. File phải tồn tại
    2. File phải có tên là logsql.txt
    3. File phải có nội dung
    4. File phải có đúng định dạng ít nhất dòng đầu tiên
    """
    # Kiểm tra tên file
    if os.path.basename(filepath) != "logsql.txt":
        logger.error(f"Invalid file name. Expected 'logsql.txt', got '{os.path.basename(filepath)}'")
        return False
        
    # Kiểm tra file tồn tại
    if not os.path.exists(filepath):
        logger.error(f"Log file not found: {filepath}")
        return False
        
    # Kiểm tra file không rỗng
    if os.path.getsize(filepath) == 0:
        logger.error(f"Log file is empty: {filepath}")
        return False
        
    # Kiểm tra định dạng của dòng đầu tiên
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            first_line = file.readline().strip()
            if not first_line or not validate_log_format(first_line):
                logger.error(f"Invalid file format. First line is not in correct format: {first_line}")
                return False
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        return False
        
    return True

def analyze_sql_query(query: str) -> Dict:
    """
    Phân tích câu truy vấn SQL và trả về các gợi ý tối ưu
    """
    analyzer = SQLAnalyzer()
    # TODO: Load existing indexes from database
    suggestions = analyzer.analyze_query(query)
    
    # Xác định mức độ ảnh hưởng tổng thể
    high_impact = any(s.impact == "HIGH" for s in suggestions)
    medium_impact = any(s.impact == "MEDIUM" for s in suggestions)
    
    if high_impact:
        overall_impact = "HIGH"
    elif medium_impact:
        overall_impact = "MEDIUM"
    else:
        overall_impact = "LOW"
        
    return {
        "suggestions": [s.__dict__ for s in suggestions],
        "overall_impact": overall_impact
    }

def process_log_file(db: Session, filepath: str) -> dict:
    """
    Xử lý file log và trả về thống kê
    """
    if not validate_file(filepath):
        raise HTTPException(
            status_code=400, 
            detail="Invalid log file. File must be named 'logsql.txt' and contain valid log entries"
        )

    stats = {
        "total_entries": 0,
        "successful_entries": 0,
        "failed_entries": 0,
        "start_time": datetime.now()
    }

    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            for line_number, line in enumerate(file, 1):
                stats["total_entries"] += 1
                try:
                    if not line.strip():
                        continue

                    log_entry = parse_log_entry(line, line_number)
                    if log_entry:
                        # Phân tích SQL và lấy gợi ý tối ưu
                        analysis_result = analyze_sql_query(log_entry.sql_query)
                        
                        # Kiểm tra entry đã tồn tại
                        existing_log = db.query(SQLLog).filter(
                            SQLLog.database_name == log_entry.database_name,
                            SQLLog.sql_query == log_entry.sql_query
                        ).first()
                        
                        if existing_log:
                            # Cập nhật số lần thực thi và thời gian trung bình
                            total_time = (existing_log.execution_time * existing_log.execution_count) + log_entry.execution_time
                            existing_log.execution_count += 1
                            existing_log.execution_time = total_time / existing_log.execution_count
                            # Cập nhật gợi ý tối ưu
                            existing_log.optimization_suggestions = json.dumps(analysis_result["suggestions"])
                            existing_log.performance_impact = analysis_result["overall_impact"]
                        else:
                            # Tạo entry mới với gợi ý tối ưu
                            log_entry_dict = log_entry.dict()
                            log_entry_dict["optimization_suggestions"] = json.dumps(analysis_result["suggestions"])
                            log_entry_dict["performance_impact"] = analysis_result["overall_impact"]
                            db_log = SQLLog(**log_entry_dict)
                            db.add(db_log)
                        
                        stats["successful_entries"] += 1
                    else:
                        stats["failed_entries"] += 1

                except Exception as e:
                    stats["failed_entries"] += 1
                    logger.error(f"Error processing line {line_number}: {str(e)}")
                    continue

            db.commit()
            
    except Exception as e:
        error_msg = f"Error processing log file: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    
    stats["end_time"] = datetime.now()
    stats["processing_time"] = (stats["end_time"] - stats["start_time"]).total_seconds()
    return stats

@router.get("/databases", response_model=List[str])
def get_databases(db: Session = Depends(get_db)):
    """Get list of all databases"""
    databases = db.query(SQLLog.database_name).distinct().all()
    return [db[0] for db in databases]

@router.get("/logs/{database_name}", response_model=List[SQLLogSchema])
def get_logs_by_database(database_name: str, db: Session = Depends(get_db)):
    """Get all SQL logs for a specific database"""
    logs = db.query(SQLLog).filter(SQLLog.database_name == database_name).all()
    if not logs:
        raise HTTPException(status_code=404, detail="Không tìm thấy truy vấn nào cho DB này")
    return logs

def start_log_processing(background_tasks: BackgroundTasks, db: Session):
    """Khởi động quá trình xử lý log khi system startup"""
    try:
        stats = process_log_file(db, "logsql.txt")
        logger.info(f"Log processing completed. Stats: {stats}")
    except Exception as e:
        logger.error(f"Failed to process logs on startup: {str(e)}")

@router.post("/process-logs")
async def process_logs_endpoint(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Endpoint to trigger log processing"""
    filepath = "logsql.txt"  # Hardcoded filename
    
    try:
        # Validate trước khi xử lý
        if not validate_file(filepath):
            raise HTTPException(
                status_code=400,
                detail="Invalid log file. File must be named 'logsql.txt' and contain valid log entries"
            )
            
        stats = process_log_file(db, filepath)
        logger.info(f"Log processing completed successfully. Stats: {stats}")
        
        return {
            "message": "Log processing completed successfully",
            "statistics": stats
        }
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error processing log file: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
