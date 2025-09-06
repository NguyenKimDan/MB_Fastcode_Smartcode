class LogAnalyzer {
    constructor() {
        this.logDetails = document.getElementById('logDetails');
        this.progressSteps = document.getElementById('progressSteps');
        this.summaryStats = document.getElementById('summaryStats');
        
        this.steps = [
            { id: 'read', label: 'Đọc file', icon: 'fa-file-alt' },
            { id: 'parse', label: 'Phân tích', icon: 'fa-code' },
            { id: 'validate', label: 'Kiểm tra', icon: 'fa-check-circle' },
            { id: 'import', label: 'Import', icon: 'fa-database' }
        ];
    }

    // Khởi tạo UI phân tích
    initAnalysis() {
        this.resetUI();
        this.updateSteps('read', 'active');
        this.addLogEntry('info', 'Bắt đầu phân tích file log...');
    }

    // Reset UI về trạng thái ban đầu
    resetUI() {
        this.logDetails.innerHTML = '';
        this.renderProgressSteps();
    }

    // Render các bước tiến trình
    renderProgressSteps() {
        this.progressSteps.innerHTML = this.steps.map(step => `
            <div class="step" id="step-${step.id}">
                <div class="step-icon">
                    <i class="fas ${step.icon}"></i>
                </div>
                <div class="step-label">${step.label}</div>
            </div>
        `).join('');
    }

    // Cập nhật trạng thái của bước
    updateSteps(stepId, status) {
        const currentStep = document.getElementById(`step-${stepId}`);
        
        // Remove existing status classes
        currentStep.classList.remove('active', 'completed', 'error');
        
        // Add new status class
        currentStep.classList.add(status);

        // Update previous steps as completed
        let found = false;
        this.steps.forEach(step => {
            if (step.id === stepId) {
                found = true;
                return;
            }
            if (!found) {
                const el = document.getElementById(`step-${step.id}`);
                el.classList.remove('active', 'error');
                el.classList.add('completed');
            }
        });
    }

    // Thêm log entry mới
    addLogEntry(type, message) {
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        entry.innerHTML = `
            <i class="fas ${this.getLogIcon(type)}"></i>
            <span>${message}</span>
            <span class="log-time">${new Date().toLocaleTimeString()}</span>
        `;
        this.logDetails.appendChild(entry);
        this.logDetails.scrollTop = this.logDetails.scrollHeight;
    }

    // Lấy icon cho loại log
    getLogIcon(type) {
        const icons = {
            info: 'fa-info-circle',
            success: 'fa-check-circle',
            warning: 'fa-exclamation-triangle',
            error: 'fa-times-circle'
        };
        return icons[type] || icons.info;
    }

    // Hiển thị thống kê tổng quan
    updateSummary(stats) {
        this.summaryStats.innerHTML = `
            <div class="stat-item">
                <div class="stat-value ${stats.total > 0 ? 'text-success' : ''}">${stats.total}</div>
                <div class="stat-label">Tổng số logs</div>
            </div>
            <div class="stat-item">
                <div class="stat-value ${stats.imported > 0 ? 'text-success' : ''}">${stats.imported}</div>
                <div class="stat-label">Import thành công</div>
            </div>
            <div class="stat-item">
                <div class="stat-value ${stats.errors === 0 ? 'text-success' : 'text-danger'}">${stats.errors}</div>
                <div class="stat-label">Lỗi</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${stats.skipped}</div>
                <div class="stat-label">Bỏ qua</div>
            </div>
        `;
    }
}
