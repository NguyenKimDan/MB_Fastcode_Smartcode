from .database import SessionLocal
from .models import LogEntry
import re
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_logs_on_startup():
    """
    Import logs from logsql.txt when the system starts
    Returns True if import was successful, False otherwise
    """
    try:
        # Đường dẫn tới file log
        log_file_path = os.path.join(os.path.dirname(__file__), '..', 'logsql.txt')
        if not os.path.exists(log_file_path):
            logger.error(f"Không tìm thấy file log tại {log_file_path}")
            return False

        # Đọc file với nhiều encoding khác nhau để tránh lỗi
        content = None
        encodings = ['utf-8', 'utf-8-sig', 'latin-1']
        for encoding in encodings:
            try:
                with open(log_file_path, 'r', encoding=encoding) as file:
                    content = file.read()
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            logger.error("Không thể đọc file log với bất kỳ encoding nào")
            return False

        db = SessionLocal()
        try:
            # Xóa dữ liệu cũ trước khi import
            db.query(LogEntry).delete()
            
            lines = content.splitlines()
            imported = 0
            errors = 0

            # Pattern chính cho format chuẩn
            main_pattern = re.compile(
                r"DB:(?P<db>[^,]+),"
                r"sql:(?P<sql>[^,]+),"
                r"exec_time_ms:(?P<time>\d+),"
                r"exec_count:(?P<count>\d+)"
            )

            # Pattern phụ cho các format khác
            alt_patterns = [
                # Format phụ 1: DB|SQL|TIME|COUNT
                re.compile(r"(?P<db>[^|]+)\|(?P<sql>[^|]+)\|(?P<time>\d+)\|(?P<count>\d+)"),
                # Format phụ 2: DB;SQL;TIME;COUNT
                re.compile(r"(?P<db>[^;]+);(?P<sql>[^;]+);(?P<time>\d+);(?P<count>\d+)")
            ]

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:  # Bỏ qua dòng trống
                    continue

                # Thử pattern chính trước
                match = main_pattern.match(line)
                if not match:
                    # Nếu không khớp, thử các pattern phụ
                    for pattern in alt_patterns:
                        match = pattern.match(line)
                        if match:
                            break

                if match:
                    try:
                        # Trích xuất và làm sạch dữ liệu
                        db_name = match.group("db").strip()
                        sql_query = match.group("sql").strip()
                        
                        try:
                            exec_time_ms = int(match.group("time"))
                            exec_count = int(match.group("count"))
                        except ValueError:
                            logger.warning(f"Dòng {line_num}: Giá trị thời gian hoặc số lần thực thi không hợp lệ")
                            errors += 1
                            continue

                        # Validate dữ liệu
                        if not db_name:
                            logger.warning(f"Dòng {line_num}: Tên database trống")
                            errors += 1
                            continue
                            
                        if not sql_query:
                            logger.warning(f"Dòng {line_num}: Câu truy vấn SQL trống")
                            errors += 1
                            continue

                        if exec_time_ms < 0:
                            logger.warning(f"Dòng {line_num}: Thời gian thực thi không thể âm")
                            errors += 1
                            continue

                        if exec_count < 0:
                            logger.warning(f"Dòng {line_num}: Số lần thực thi không thể âm")
                            errors += 1
                            continue

                        # Tạo và thêm entry mới
                        entry = LogEntry(
                            db_name=db_name,
                            sql_query=sql_query,
                            exec_time_ms=exec_time_ms,
                            exec_count=exec_count
                        )
                        db.add(entry)
                        imported += 1
                        logger.info(f"Đã import dòng {line_num} thành công: DB={db_name}, Time={exec_time_ms}ms, Count={exec_count}")

                    except Exception as e:
                        logger.warning(f"Dòng {line_num}: Lỗi xử lý - {str(e)}")
                        errors += 1
                else:
                    logger.warning(f"Dòng {line_num}: Định dạng không hợp lệ - {line}")
                    errors += 1

            # Commit transaction nếu có ít nhất 1 entry hợp lệ
            if imported > 0:
                try:
                    db.commit()
                    logger.info(f"Import hoàn tất: Thành công={imported}, Lỗi={errors}")
                    return True
                except Exception as e:
                    db.rollback()
                    logger.error(f"Lỗi khi lưu vào database: {str(e)}")
                    return False
            else:
                db.rollback()
                logger.error("Không có entry nào hợp lệ để import")
                return False

        except Exception as e:
            db.rollback()
            logger.error(f"Lỗi khi xử lý file log: {str(e)}")
            return False
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Lỗi hệ thống: {str(e)}")
        return False
