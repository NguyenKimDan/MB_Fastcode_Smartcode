from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

class LogEntry(Base):
    __tablename__ = "log_entries"
    id = Column(Integer, primary_key=True, index=True)
    db_name = Column(String)
    sql_query = Column(Text)
    exec_time_ms = Column(Integer)
    exec_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class AbnormalQuery(Base):
    __tablename__ = "abnormal_queries"
    id = Column(Integer, primary_key=True, index=True)
    db_name = Column(String)
    sql_query = Column(Text)
    exec_time_ms = Column(Integer)
    exec_count = Column(Integer)
    status = Column(String)
    suggestion = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
