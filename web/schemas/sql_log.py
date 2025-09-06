from pydantic import BaseModel, validator
from typing import Optional, List, Dict
from datetime import datetime

class OptimizationSuggestion(BaseModel):
    type: str
    message: str
    priority: int
    impact: str

class SQLLogBase(BaseModel):
    database_name: str
    sql_query: str
    execution_time: float
    execution_count: int = 1
    error_message: Optional[str] = None
    optimization_suggestions: Optional[List[OptimizationSuggestion]] = None
    performance_impact: Optional[str] = None
    
    @validator('database_name')
    def validate_database_name(cls, v):
        if not v.strip():
            raise ValueError('Database name cannot be empty')
        return v.strip()
    
    @validator('sql_query')
    def validate_sql_query(cls, v):
        if not v.strip():
            raise ValueError('SQL query cannot be empty')
        return v.strip()
    
    @validator('execution_time')
    def validate_execution_time(cls, v):
        if v < 0:
            raise ValueError('Execution time cannot be negative')
        return v

class SQLLogCreate(SQLLogBase):
    pass

class SQLLog(SQLLogBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
