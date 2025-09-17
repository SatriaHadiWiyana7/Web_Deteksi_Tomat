document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('register-form');
    if (!form) return; // Keluar jika bukan di halaman register

    const usernameInput = document.getElementById('username');
    const phoneInput = document.getElementById('phone');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm-password');

    const showError = (input, message) => {
        const errorDiv = document.getElementById(`${input.id}-error`);
        input.classList.add('invalid');
        errorDiv.textContent = message;
    };

    const clearError = (input) => {
        const errorDiv = document.getElementById(`${input.id}-error`);
        input.classList.remove('invalid');
        errorDiv.textContent = '';
    };

    const validatePassword = () => {
        const password = passwordInput.value;
        const strengthBar = document.getElementById('password-strength-bar');
        const strengthText = document.getElementById('password-strength-text');
        
        let score = 0;
        if (password.length >= 8) score++;
        if (/[a-z]/.test(password)) score++;
        if (/[A-Z]/.test(password)) score++;
        if (/[0-9]/.test(password)) score++;
        
        strengthBar.className = 'strength-bar';
        strengthText.className = 'strength-text';
        
        switch(score) {
            case 1:
            case 2:
                strengthBar.classList.add('weak');
                strengthText.textContent = 'Kekuatan: Lemah';
                break;
            case 3:
                strengthBar.classList.add('medium');
                strengthText.textContent = 'Kekuatan: Sedang';
                break;
            case 4:
                strengthBar.classList.add('strong');
                strengthText.textContent = 'Kekuatan: Kuat';
                break;
            default:
                strengthText.textContent = '';
                break;
        }
        return score >= 3; // Dianggap valid jika kekuatan sedang atau kuat
    };
    
    form.addEventListener('submit', function (event) {
        let isValid = true;

        if (usernameInput.value.trim().length < 3) {
            showError(usernameInput, 'Username minimal 3 karakter.');
            isValid = false;
        } else {
            clearError(usernameInput);
        }

        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailInput.value)) {
            showError(emailInput, 'Format email tidak valid.');
            isValid = false;
        } else {
            clearError(emailInput);
        }

        const isPasswordStrong = validatePassword();
        if (!isPasswordStrong) {
            showError(passwordInput, 'Password harus mengandung huruf besar, huruf kecil, dan angka, serta minimal 8 karakter.');
            isValid = false;
        } else {
             clearError(passwordInput);
        }
        
        if (passwordInput.value !== confirmPasswordInput.value) {
            showError(confirmPasswordInput, 'Password tidak cocok.');
            isValid = false;
        } else {
            clearError(confirmPasswordInput);
        }

        if (!isValid) {
            event.preventDefault();
        }
    });

    // Validasi real-time saat pengguna mengetik
    passwordInput.addEventListener('input', validatePassword);
    confirmPasswordInput.addEventListener('input', () => {
        if (passwordInput.value !== confirmPasswordInput.value) {
            showError(confirmPasswordInput, 'Password tidak cocok.');
        } else {
            clearError(confirmPasswordInput);
        }
    });
});