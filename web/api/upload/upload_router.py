from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from core.file_validator import FileValidator
from api.logs.logs_router import process_log_file
from sqlalchemy.orm import Session
from fastapi import Depends
from db.database import get_db
import shutil
import os
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload và xử lý file log.
    Chỉ chấp nhận file có đuôi .txt
    """
    temp_file_path = None
    
    try:
        # 1. Validate file type
        is_valid, error_message = FileValidator.validate_file(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)
        
        # 2. Tạo tên file tạm thời
        temp_file_path = os.path.join(os.getcwd(), "temp_upload.txt")
        
        # 3. Lưu file
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 4. Xử lý file
        stats = process_log_file(db, temp_file_path)
        
        return {
            "status": "success",
            "message": "File đã được xử lý thành công",
            "filename": file.filename,
            "statistics": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi xử lý file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi xử lý file: {str(e)}"
        )
    finally:
        # Cleanup temp file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                logger.error(f"Lỗi xóa file tạm: {str(e)}")
    
    try:
        # 1. Validate file
        is_valid, error_message = FileValidator.validate_file(file)
        if not is_valid:
            raise HTTPException(
                status_code=400, 
                detail=error_message
            )

        # 2. Lưu và xử lý file
        try:
            # Lưu file
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Xử lý file
            stats = process_log_file(db, temp_file_path)
            
            return {
                "status": "success",
                "message": "File đã được tải lên và xử lý thành công",
                "filename": file.filename,
                "statistics": stats
            }
            
        except Exception as e:
            logger.error(f"Lỗi xử lý file: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Lỗi xử lý file: {str(e)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading file: {str(e)}"
        )
    finally:
        # Cleanup temp file if exists
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                logger.error(f"Error cleaning up temp file: {str(e)}")

# Endpoint để kiểm tra trạng thái xử lý
@router.get("/upload/status/{task_id}")
async def get_upload_status(task_id: str):
    """
    Kiểm tra trạng thái xử lý file
    """
    return {
        "status": "completed",
        "message": "File đã được xử lý thành công"
    }

@router.get("/upload/validate")
async def validate_file_type():
    """
    Trả về thông tin về các loại file được chấp nhận
    """
    return {
        "accepted_formats": [FileValidator.ALLOWED_EXTENSION],
        "error_message": "Chỉ chấp nhận file có đuôi .txt",
        "encoding": "UTF-8",
        "description": "Hệ thống chỉ xử lý các file có đuôi .txt. Các file khác (.log, .pdf, .doc, ...) sẽ bị từ chối."
    }
