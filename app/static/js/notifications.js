// static/js/notifications.js

/**
 * Fungsi global untuk menampilkan notifikasi pop-up (toast).
 * @param {string} message - Pesan yang akan ditampilkan.
 * @param {string} [type='success'] - Tipe notifikasi ('success', 'error', 'warning', 'info').
 */
function showAlert(message, type = 'success') {
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

    Toast.fire({
        icon: type,
        title: message
    });
}


/**
 * Bagian ini berjalan otomatis saat halaman dimuat.
 * Ia memeriksa pesan 'flash' dari Flask dan menampilkannya menggunakan fungsi showAlert di atas.
 */
document.addEventListener('DOMContentLoaded', () => {
    if (typeof FLASH_MESSAGES !== 'undefined' && FLASH_MESSAGES.length > 0) {
        FLASH_MESSAGES.forEach(msg => {
            let category = msg[0];
            if (category === 'danger') {
                category = 'error';
            }
            showAlert(msg[1], category);
        });
    }
});