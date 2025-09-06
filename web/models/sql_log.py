from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from datetime import datetime
from db.database import Base

class SQLLog(Base):
    __tablename__ = "sql_logs"

    id = Column(Integer, primary_key=True, index=True)
    database_name = Column(String, index=True)
    sql_query = Column(String)
    execution_time = Column(Float)  # in milliseconds
    execution_count = Column(Integer, default=1)
    error_message = Column(String, nullable=True)  # For storing error messages if any
    optimization_suggestions = Column(String, nullable=True)  # JSON string of suggestions
    optimization_reasons = Column(String, nullable=True)  # JSON string of reasons
    performance_impact = Column(String, nullable=True)  # HIGH, MEDIUM, LOW
    is_anomaly = Column(Boolean, default=False)  # Flag for anomalous queries
    anomaly_reason = Column(String, nullable=True)  # Reason why query is anomalous
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
