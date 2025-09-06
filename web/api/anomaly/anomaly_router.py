from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from models.sql_log import SQLLog
from schemas.sql_log import SQLLogSchema
import json

router = APIRouter()

@router.get("/scan")
async def scan_anomalous_queries(db: Session = Depends(get_db)):
    """
    Quét và phát hiện các truy vấn bất thường dựa trên quy tắc:
    - Thời gian thực thi > 500ms VÀ
    - Số lần thực thi > 100
    """
    # Tìm các truy vấn bất thường
    anomalous_queries = db.query(SQLLog).filter(
        SQLLog.execution_time > 500,
        SQLLog.execution_count > 100
    ).all()

    # Cập nhật trạng thái bất thường
    for query in anomalous_queries:
        query.is_anomaly = True
        query.anomaly_reason = (
            f"Truy vấn thực thi {query.execution_count} lần "
            f"với thời gian trung bình {query.execution_time:.2f}ms"
        )
    db.commit()

    # Chuẩn bị response
    if not anomalous_queries:
        return {
            "message": "Không phát hiện truy vấn bất thường nào",
            "total": 0,
            "queries": []
        }

    # Format kết quả
    result_queries = []
    for query in anomalous_queries:
        result = {
            "database": query.database_name,
            "sql": query.sql_query,
            "execution_time": round(query.execution_time, 2),
            "execution_count": query.execution_count,
            "anomaly_reason": query.anomaly_reason,
            "optimization_suggestions": json.loads(query.optimization_suggestions) if query.optimization_suggestions else [],
            "optimization_reasons": json.loads(query.optimization_reasons) if query.optimization_reasons else [],
            "performance_impact": query.performance_impact
        }
        result_queries.append(result)

    return {
        "message": f"Phát hiện {len(anomalous_queries)} truy vấn bất thường",
        "total": len(anomalous_queries),
        "queries": result_queries
    }

@router.get("/stats")
async def get_performance_stats(db: Session = Depends(get_db)):
    """
    Lấy thống kê hiệu năng tổng quan
    """
    total_queries = db.query(SQLLog).count()
    anomalous_queries = db.query(SQLLog).filter(
        SQLLog.is_anomaly == True
    ).count()
    
    # Tính phần trăm truy vấn bất thường
    anomaly_percentage = (anomalous_queries / total_queries * 100) if total_queries > 0 else 0
    
    return {
        "total_queries": total_queries,
        "anomalous_queries": anomalous_queries,
        "anomaly_percentage": round(anomaly_percentage, 2),
        "status": "warning" if anomaly_percentage > 10 else "normal"
    }
