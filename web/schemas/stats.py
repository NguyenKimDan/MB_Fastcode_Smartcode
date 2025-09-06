from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SQLQueryStats(BaseModel):
    query: str
    execution_time: float
    execution_count: int
    database_name: str
    optimization_suggestions: List[dict]
    performance_impact: str
    last_executed: datetime

class DatabaseStats(BaseModel):
    database_name: str
    total_queries: int
    avg_execution_time: float
    queries_needing_optimization: int
    top_queries: List[SQLQueryStats]

class OptimizationResponse(BaseModel):
    suggestions: List[dict]
    impact: str
    estimated_improvement: str
