// Các hàm tiện ích
function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.textContent = message;
    errorDiv.classList.add('show');
}

function hideError() {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.classList.remove('show');
}

function showLoading(button) {
    button.disabled = true;
    button.classList.add('loading');
    const icon = button.querySelector('i');
    if (icon) {
        icon.className = 'fas fa-spinner';
    }
}

function hideLoading(button, originalIcon) {
    button.disabled = false;
    button.classList.remove('loading');
    const icon = button.querySelector('i');
    if (icon && originalIcon) {
        icon.className = originalIcon;
    }
}

// Xử lý đăng ký
if (document.getElementById('registerForm')) {
    const form = document.getElementById('registerForm');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideError();

        const username = form.username.value;
        const email = form.email.value;
        const password = form.password.value;
        const confirmPassword = form.confirmPassword.value;
        const submitButton = form.querySelector('button[type="submit"]');
        const originalIcon = 'fas fa-user-plus';

        // Kiểm tra mật khẩu xác nhận
        if (password !== confirmPassword) {
            showError('Mật khẩu xác nhận không khớp');
            return;
        }

        // Validate username
        if (!/^[a-zA-Z0-9_]{4,20}$/.test(username)) {
            showError('Tên người dùng phải từ 4-20 ký tự và chỉ chứa chữ cái, số và dấu gạch dưới');
            return;
        }

        // Validate email
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            showError('Email không hợp lệ');
            return;
        }

        // Validate password length
        if (password.length < 8) {
            showError('Mật khẩu phải có ít nhất 8 ký tự');
            return;
        }

        showLoading(submitButton);

        try {
            const response = await fetch('http://localhost:8000/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username,
                    email,
                    password
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Đăng ký thất bại');
            }

            // Redirect to login page with success message
            localStorage.setItem('registerSuccess', 'true');
            window.location.href = 'login.html';

        } catch (error) {
            showError(error.message);
            hideLoading(submitButton, originalIcon);
        }
    });
}

// Xử lý đăng nhập
if (document.getElementById('loginForm')) {
    const form = document.getElementById('loginForm');
    
    // Check for register success message
    if (localStorage.getItem('registerSuccess')) {
        const successDiv = document.createElement('div');
        successDiv.className = 'success-message';
        successDiv.innerHTML = '<i class="fas fa-check-circle"></i> Đăng ký thành công! Vui lòng đăng nhập.';
        form.insertBefore(successDiv, form.firstChild);
        localStorage.removeItem('registerSuccess');
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideError();

        const username = form.username.value;
        const password = form.password.value;
        const submitButton = form.querySelector('button[type="submit"]');
        const originalIcon = 'fas fa-sign-in-alt';

        showLoading(submitButton);

        try {
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);

            const response = await fetch('http://localhost:8000/auth/login', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Đăng nhập thất bại');
            }

            // Save token
            localStorage.setItem('token', data.access_token);

            // Redirect to dashboard
            window.location.href = 'dashboard.html';

        } catch (error) {
            showError(error.message);
            hideLoading(submitButton, originalIcon);
        }
    });
}

// Kiểm tra xác thực cho các trang được bảo vệ
function checkAuth() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    // Verify token is valid
    fetch('http://localhost:8000/auth/me', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Token invalid');
        }
        return response.json();
    })
    .catch(() => {
        localStorage.removeItem('token');
        window.location.href = 'login.html';
    });
}

// Thực hiện kiểm tra xác thực trên các trang được bảo vệ
if (window.location.pathname.includes('dashboard.html')) {
    checkAuth();
}

// Xử lý đăng xuất
function logout() {
    localStorage.removeItem('token');
    window.location.href = 'login.html';
}
