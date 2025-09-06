from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from db.database import get_db, engine, Base
from api.logs import logs_router
import logging

# Tạo logger
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Tạo app
app = FastAPI()

# Create database tables
Base.metadata.create_all(bind=engine)

# Thêm router
app.include_router(logs_router.router, prefix="/api/logs", tags=["logs"])

# Import và thêm các router
from api.upload import upload_router
from api.anomaly import anomaly_router

app.include_router(upload_router.router, prefix="/api/upload", tags=["upload"])
app.include_router(anomaly_router.router, prefix="/api/anomaly", tags=["anomaly"])

@app.on_event("startup")
async def startup_event():
    """
    Xử lý log file khi khởi động hệ thống
    """
    filepath = "logsql.txt"
    try:
        # Validate file trước khi xử lý
        if not logs_router.validate_file(filepath):
            logger.error("Invalid log file at startup. Skipping log processing.")
            return
            
        db = next(get_db())
        try:
            logs_router.start_log_processing(None, db)
            logger.info("System startup: Log processing completed")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"System startup error: {str(e)}")
        # Không raise exception để không ảnh hưởng đến việc khởi động server

@app.get("/health")
def health_check():
    """
    Endpoint kiểm tra health của hệ thống
    """
    return {"status": "healthy"}
