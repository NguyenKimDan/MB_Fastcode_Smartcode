// Hàm tạo và hiển thị báo cáo
async function fetchReportSummary() {
    const reportContainer = document.getElementById('reportSummary');
    reportContainer.innerHTML = '<div class="loading">Đang tải báo cáo...</div>';

    try {
        const response = await fetch('http://localhost:8000/report/summary');
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Không thể tải báo cáo');
        }

        // Tạo phần tổng quan
        let metricsHtml = `
            <div class="report-metrics">
                <div class="metric-card">
                    <div class="metric-label">Tổng số truy vấn</div>
                    <div class="metric-value">${data.total_queries}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Truy vấn bất thường</div>
                    <div class="metric-value">${data.abnormal_count}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Có gợi ý tối ưu</div>
                    <div class="metric-value">${data.suggestion_count}</div>
                </div>
            </div>`;

        // Tạo bảng báo cáo chi tiết
        let tableHtml = `
            <div class="report-table-container">
                <table class="report-table">
                    <thead>
                        <tr>
                            <th>Database</th>
                            <th>Truy vấn SQL</th>
                            <th>Thời gian (ms)</th>
                            <th>Số lần thực thi</th>
                            <th>Trạng thái</th>
                            <th>Gợi ý tối ưu</th>
                        </tr>
                    </thead>
                    <tbody>`;

        data.abnormal_queries.forEach(query => {
            const performanceClass = getPerformanceClass(query.exec_time_ms);
            tableHtml += `
                <tr>
                    <td>${escapeHtml(query.db_name)}</td>
                    <td class="sql-cell">${escapeHtml(query.sql_query)}</td>
                    <td>${query.exec_time_ms}
                        <span class="performance-indicator ${performanceClass}">
                            ${getPerformanceText(query.exec_time_ms)}
                        </span>
                    </td>
                    <td>${query.exec_count}</td>
                    <td>${escapeHtml(query.status)}</td>
                    <td>${escapeHtml(query.suggestion || 'Không có')}</td>
                </tr>`;
        });

        tableHtml += `
                </tbody>
            </table>
        </div>`;

        reportContainer.innerHTML = metricsHtml + tableHtml;

    } catch (error) {
        reportContainer.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                Lỗi: ${error.message}
            </div>`;
    }
}

// Hàm phân loại hiệu năng dựa trên thời gian thực thi
function getPerformanceClass(execTime) {
    if (execTime <= 100) return 'performance-good';
    if (execTime <= 1000) return 'performance-warning';
    return 'performance-critical';
}

// Hàm trả về text hiệu năng
function getPerformanceText(execTime) {
    if (execTime <= 100) return 'Tốt';
    if (execTime <= 1000) return 'Cần cải thiện';
    return 'Chậm';
}

// Hàm escape HTML để tránh XSS
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Tải CSV
async function downloadCSV() {
    try {
        const response = await fetch('http://localhost:8000/report/export/csv');
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `bao_cao_truy_van_${formatDate(new Date())}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
    } catch (error) {
        alert('Lỗi khi tải file CSV: ' + error.message);
    }
}

// Tải PDF
async function downloadPDF() {
    try {
        const response = await fetch('http://localhost:8000/report/export/pdf');
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `bao_cao_truy_van_${formatDate(new Date())}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
    } catch (error) {
        alert('Lỗi khi tải file PDF: ' + error.message);
    }
}

// Format date cho tên file
function formatDate(date) {
    return date.toISOString().split('T')[0];
}

// Auto-refresh report mỗi 5 phút
let autoRefreshInterval;
function toggleAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
        document.getElementById('autoRefreshBtn').classList.remove('active');
    } else {
        fetchReportSummary(); // Refresh ngay lập tức
        autoRefreshInterval = setInterval(fetchReportSummary, 300000); // 5 phút
        document.getElementById('autoRefreshBtn').classList.add('active');
    }
}
