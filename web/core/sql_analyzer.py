import re
from typing import List, Dict, Set
from dataclasses import dataclass
from enum import Enum

class OptimizationType(Enum):
    INDEX = "INDEX"
    JOIN = "JOIN"
    QUERY_STRUCTURE = "QUERY_STRUCTURE"
    PERFORMANCE = "PERFORMANCE"
    SCHEMA = "SCHEMA"

@dataclass
class SQLOptimizationSuggestion:
    type: OptimizationType
    message: str
    reason: str    # Lý do cần tối ưu
    priority: int  # 1-5, với 1 là cao nhất
    impact: str    # "HIGH", "MEDIUM", "LOW"
    is_anomaly: bool = False  # Đánh dấu nếu là truy vấn bất thường

class SQLAnalyzer:
    def __init__(self):
        self._existing_indexes: Set[str] = set()
        
    def set_existing_indexes(self, indexes: List[str]):
        """Set danh sách index đã tồn tại"""
        self._existing_indexes = set(indexes)

    def analyze_query(self, query: str, exec_time: float = None, exec_count: int = None) -> List[SQLOptimizationSuggestion]:
        """
        Phân tích query và trả về danh sách gợi ý
        Parameters:
            query: Câu truy vấn SQL
            exec_time: Thời gian thực thi (ms)
            exec_count: Số lần thực thi
        """
        suggestions = []
        query = query.upper()  # Normalize query

        # Kiểm tra truy vấn bất thường
        if exec_time is not None and exec_count is not None:
            anomaly = self._analyze_anomaly(query, exec_time, exec_count)
            if anomaly:
                suggestions.append(anomaly)

        # A. Cơ bản - Index & WHERE
        self._analyze_where_clause(query, suggestions)
        
        # B. JOIN & Subquery
        self._analyze_joins(query, suggestions)
        self._analyze_subqueries(query, suggestions)
        
        # C. ORDER BY, GROUP BY, Aggregation
        self._analyze_order_group(query, suggestions)
        self._analyze_aggregations(query, suggestions)
        
        # D. SELECT & Projection
        self._analyze_select_clause(query, suggestions)
        
        # E. LIKE & Pattern Matching
        self._analyze_pattern_matching(query, suggestions)
        
        # F. Performance nâng cao
        self._analyze_advanced_performance(query, suggestions)

        return sorted(suggestions, key=lambda x: (x.is_anomaly, x.priority), reverse=True)

        return sorted(suggestions, key=lambda x: x.priority)

    def _analyze_where_clause(self, query: str, suggestions: List[SQLOptimizationSuggestion]):
        """Phân tích mệnh đề WHERE"""
        where_match = re.search(r'WHERE\s+(.+?)(?:\s+(?:ORDER|GROUP|HAVING|LIMIT|$))', query)
        if not where_match:
            return

        where_clause = where_match.group(1)
        fields = re.findall(r'([A-Za-z_]\w*)\s*(?:=|>|<|LIKE|IN|BETWEEN)', where_clause)
        
        for field in fields:
            if field not in self._existing_indexes:
                suggestions.append(SQLOptimizationSuggestion(
                    type=OptimizationType.INDEX,
                    message=f"Thêm index trên trường [{field}]",
                    priority=1,
                    impact="HIGH"
                ))

        if 'OR' in where_clause:
            suggestions.append(SQLOptimizationSuggestion(
                type=OptimizationType.PERFORMANCE,
                message="Xem xét tách các điều kiện OR thành UNION để tối ưu index",
                priority=2,
                impact="MEDIUM"
            ))

    def _analyze_joins(self, query: str, suggestions: List[SQLOptimizationSuggestion]):
        """Phân tích JOIN"""
        joins = re.findall(r'(LEFT|RIGHT|INNER|OUTER)?\s*JOIN\s+(\w+)\s+ON\s+(.+?)(?:\s+(?:WHERE|JOIN|ORDER|GROUP|$))', query)
        
        for join_type, table, conditions in joins:
            if join_type in ('LEFT', 'RIGHT'):
                suggestions.append(SQLOptimizationSuggestion(
                    type=OptimizationType.JOIN,
                    message=f"Xem xét sử dụng INNER JOIN thay vì {join_type} JOIN nếu logic cho phép",
                    priority=3,
                    impact="MEDIUM"
                ))

            join_fields = re.findall(r'([A-Za-z_]\w*)\s*=', conditions)
            for field in join_fields:
                if field not in self._existing_indexes:
                    suggestions.append(SQLOptimizationSuggestion(
                        type=OptimizationType.INDEX,
                        message=f"Thêm index trên trường JOIN [{field}]",
                        priority=1,
                        impact="HIGH"
                    ))

    def _analyze_subqueries(self, query: str, suggestions: List[SQLOptimizationSuggestion]):
        """Phân tích Subqueries"""
        if query.count('SELECT') > 1:  # Nested subqueries
            suggestions.append(SQLOptimizationSuggestion(
                type=OptimizationType.QUERY_STRUCTURE,
                message="Xem xét viết lại subquery bằng JOIN hoặc CTE (WITH ...)",
                priority=2,
                impact="HIGH"
            ))

        if 'EXISTS' in query:
            suggestions.append(SQLOptimizationSuggestion(
                type=OptimizationType.PERFORMANCE,
                message="Xem xét chuyển EXISTS sang JOIN để cải thiện hiệu suất",
                priority=2,
                impact="MEDIUM"
            ))

    def _analyze_order_group(self, query: str, suggestions: List[SQLOptimizationSuggestion]):
        """Phân tích ORDER BY và GROUP BY"""
        order_match = re.search(r'ORDER\s+BY\s+(.+?)(?:\s+(?:LIMIT|$))', query)
        if order_match:
            fields = re.findall(r'([A-Za-z_]\w*)', order_match.group(1))
            if len(fields) > 0:
                suggestions.append(SQLOptimizationSuggestion(
                    type=OptimizationType.INDEX,
                    message=f"Thêm index trên các trường ORDER BY: {', '.join(fields)}",
                    priority=2,
                    impact="MEDIUM"
                ))

        group_match = re.search(r'GROUP\s+BY\s+(.+?)(?:\s+(?:HAVING|ORDER|LIMIT|$))', query)
        if group_match:
            fields = re.findall(r'([A-Za-z_]\w*)', group_match.group(1))
            if len(fields) > 1:
                suggestions.append(SQLOptimizationSuggestion(
                    type=OptimizationType.INDEX,
                    message=f"Thêm composite index trên các trường GROUP BY: {', '.join(fields)}",
                    priority=2,
                    impact="HIGH"
                ))

    def _analyze_select_clause(self, query: str, suggestions: List[SQLOptimizationSuggestion]):
        """Phân tích SELECT"""
        if 'SELECT *' in query:
            suggestions.append(SQLOptimizationSuggestion(
                type=OptimizationType.PERFORMANCE,
                message="Chỉ chọn cột cần thiết thay vì SELECT *",
                priority=1,
                impact="HIGH"
            ))

        select_items = re.findall(r'SELECT\s+(.+?)\s+FROM', query)
        if select_items:
            columns = select_items[0].split(',')
            if len(columns) > 20:
                suggestions.append(SQLOptimizationSuggestion(
                    type=OptimizationType.PERFORMANCE,
                    message=f"Truy vấn đang chọn {len(columns)} cột. Xem xét giảm số lượng cột",
                    priority=3,
                    impact="MEDIUM"
                ))

    def _analyze_pattern_matching(self, query: str, suggestions: List[SQLOptimizationSuggestion]):
        """Phân tích LIKE và Pattern Matching"""
        if "LIKE '%" in query and query.endswith("%'"):
            suggestions.append(SQLOptimizationSuggestion(
                type=OptimizationType.PERFORMANCE,
                message="Xem xét sử dụng Full-Text Index hoặc ElasticSearch cho tìm kiếm văn bản",
                priority=2,
                impact="HIGH"
            ))
        elif "LIKE '" in query and "'%" in query:
            suggestions.append(SQLOptimizationSuggestion(
                type=OptimizationType.INDEX,
                message="Thêm B-Tree index cho tìm kiếm prefix",
                priority=2,
                impact="MEDIUM"
            ))

    def _analyze_advanced_performance(self, query: str, suggestions: List[SQLOptimizationSuggestion]):
        """Phân tích các vấn đề performance nâng cao"""
        if 'LIMIT' in query:
            limit_value = re.search(r'LIMIT\s+(\d+)', query)
            if limit_value and int(limit_value.group(1)) > 1000:
                suggestions.append(SQLOptimizationSuggestion(
                    type=OptimizationType.PERFORMANCE,
                    message="Xem xét sử dụng phân trang hoặc keyset pagination cho LIMIT lớn",
                    priority=2,
                    impact="HIGH"
                ))

        if 'UNION' in query and 'UNION ALL' not in query:
            suggestions.append(SQLOptimizationSuggestion(
                type=OptimizationType.PERFORMANCE,
                message="Xem xét sử dụng UNION ALL nếu không cần loại bỏ trùng lặp",
                priority=3,
                impact="MEDIUM"
            ))

        in_clause = re.search(r'IN\s*\(([\d\s,]+)\)', query)
        if in_clause and len(in_clause.group(1).split(',')) > 100:
            suggestions.append(SQLOptimizationSuggestion(
                type=OptimizationType.PERFORMANCE,
                message="Chuyển danh sách IN lớn sang JOIN với bảng tạm",
                priority=2,
                impact="HIGH"
            ))
