// Đăng ký
if (document.getElementById('registerForm')) {
    document.getElementById('registerForm').onsubmit = async function(e) {
        e.preventDefault();
        const form = e.target;
        const res = await fetch('http://localhost:8000/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: form.username.value,
                email: form.email.value,
                password: form.password.value
            })
        });
        const data = await res.json();
        document.getElementById('registerResult').innerText = data.message || data.detail;
    }
}
// Đăng nhập
if (document.getElementById('loginForm')) {
    document.getElementById('loginForm').onsubmit = async function(e) {
        e.preventDefault();
        const form = e.target;
        const res = await fetch('http://localhost:8000/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: form.username.value,
                password: form.password.value
            })
        });
        const data = await res.json();
        if (data.access_token) {
            localStorage.setItem('token', data.access_token);
            window.location.href = 'dashboard.html';
        } else {
            document.getElementById('loginResult').innerText = data.detail;
        }
    }
}
// Dashboard functions
async function uploadLogFile() {
    const fileInput = document.getElementById('logFile');
    if (!fileInput.files.length) return;
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    const res = await fetch('http://localhost:8000/log/parse', {
        method: 'POST',
        body: formData
    });
    const data = await res.json();
    document.getElementById('logResult').innerText = data.message;
    fetchDatabases();
}
async function fetchDatabases() {
    const res = await fetch('http://localhost:8000/crud/databases');
    const dbs = await res.json();
    const dropdown = document.getElementById('dbDropdown');
    dropdown.innerHTML = '';
    dbs.forEach(db => {
        const opt = document.createElement('option');
        opt.value = db;
        opt.innerText = db;
        dropdown.appendChild(opt);
    });
    if (dbs.length) fetchQueries();
}
async function fetchQueries() {
    const db = document.getElementById('dbDropdown').value;
    const res = await fetch(`http://localhost:8000/crud/queries/${db}`);
    const data = await res.json();
    const queriesDiv = document.getElementById('queries');
    if (data.message) {
        queriesDiv.innerText = data.message;
    } else {
        queriesDiv.innerHTML = '<table><tr><th>SQL Query</th><th>Exec Time (ms)</th><th>Exec Count</th></tr>' +
            data.map(q => `<tr><td>${q.sql_query}</td><td>${q.exec_time_ms}</td><td>${q.exec_count}</td></tr>`).join('') + '</table>';
    }
}
async function scanAbnormalQueries() {
    // Giả lập quét bất thường, thực tế cần API riêng
    const res = await fetch('http://localhost:8000/crud/log_entries');
    const logs = await res.json();
    const abnormal = logs.filter(q => q.exec_time_ms > 500 && q.exec_count > 100);
    const resultDiv = document.getElementById('abnormalResult');
    if (abnormal.length) {
        resultDiv.innerHTML = '<table><tr><th>DB</th><th>SQL</th><th>Time</th><th>Count</th></tr>' +
            abnormal.map(q => `<tr style="background:#f8d7da"><td>${q.db_name}</td><td>${q.sql_query}</td><td>${q.exec_time_ms}</td><td>${q.exec_count}</td></tr>`).join('') + '</table>';
    } else {
        resultDiv.innerText = 'Không phát hiện truy vấn bất thường nào';
    }
}
async function fetchReportSummary() {
    const res = await fetch('http://localhost:8000/report/summary');
    const data = await res.json();
    document.getElementById('reportSummary').innerText = `Tổng số truy vấn: ${data.total_queries}, Số bất thường: ${data.abnormal_count}`;
}
function downloadCSV() {
    window.open('http://localhost:8000/report/export/csv');
}
function downloadPDF() {
    window.open('http://localhost:8000/report/export/pdf');
}
if (window.location.pathname.endsWith('dashboard.html')) {
    fetchDatabases();
}
