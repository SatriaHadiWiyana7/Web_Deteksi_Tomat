// static/js/notifications.js

/**
 * Fungsi ini mengambil array pesan dan menampilkannya sebagai notifikasi toast.
 * @param {Array<Array<string>>} messages - Array berisi array pesan, contoh: [['success', 'Login berhasil!']]
 */
function showFlashMessages(messages) {

    if (!messages || messages.length === 0) {
        return;
    }

    const Toast = Swal.mixin({
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3500,
        timerProgressBar: true,
        didOpen: (toast) => {
            toast.addEventListener('mouseenter', Swal.stopTimer);
            toast.addEventListener('mouseleave', Swal.resumeTimer);
        }
    });

    messages.forEach(msg => {
        const category = msg[0]; // contoh: 'success'
        const message = msg[1];  // contoh: 'Login berhasil! ...'

        Toast.fire({
            icon: category,
            title: message
        });
    });
}

// Cek apakah data notifikasi (FLASH_MESSAGES) sudah disiapkan di HTML
if (typeof FLASH_MESSAGES !== 'undefined' && FLASH_MESSAGES.length > 0) {
    showFlashMessages(FLASH_MESSAGES);
}