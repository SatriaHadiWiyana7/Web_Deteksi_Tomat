document.addEventListener('DOMContentLoaded', function() {
    const tableBody = document.getElementById('logTableBody');
    const alertContainer = document.getElementById('alert-container');


    /**
     * Mengambil data log dari API backend dan mengisi tabel.
     */
    async function fetchData() {
        tableBody.innerHTML = '<tr><td colspan="7" class="no-data">Memuat data...</td></tr>';

        try {
            const response = await fetch('/admin/logs');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const logs = await response.json();

            tableBody.innerHTML = ''; // Kosongkan tabel sebelum diisi
            if (logs.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="7" class="no-data">Tidak ada data log yang tersedia.</td></tr>';
                return;
            }

            logs.forEach((log, index) => {
                const row = tableBody.insertRow();
                const confidence = (log.confidence * 100).toFixed(2);
                const date = new Date(log.detection_date).toLocaleString('id-ID', {
                    year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                });

                // Cek jika URL gambar ada. Jika tidak, tampilkan teks.
                const imageCellHtml = log.raw_image_url 
                    ? `<img src="${log.raw_image_url}" alt="Gambar Deteksi" style="width: 60px; height: 60px; object-fit: cover; border-radius: 4px;">`
                    : '<span>Tidak Ada Gambar</span>';

                row.innerHTML = `
                    <td>${index + 1}</td>
                    <td>${date}</td>
                    <td>${log.user_name || 'N/A'}</td>
                    <td>${log.result}</td>
                    <td>${confidence}%</td>
                    <td>${imageCellHtml}</td>
                    <td class="action-icons">
                        <button title="Delete" class="delete-btn" data-log-id="${log.id}"><i class="fas fa-trash"></i></button>
                    </td>
                `;
            });
        } catch (error) {
            console.error('Gagal mengambil logs:', error);
            tableBody.innerHTML = '<tr><td colspan="7" class="no-data">Gagal memuat data. Silakan coba lagi.</td></tr>';
            showAlert('Gagal memuat data log.', 'error');
        }
    }

    /**
     * Menghapus satu entri log berdasarkan ID-nya.
     * @param {number} logId - ID dari log yang akan dihapus.
     */
    async function deleteLog(logId) {
        if (!confirm('Apakah Anda yakin ingin menghapus log ini? Tindakan ini tidak dapat diurungkan.')) return;
        
        try {
            const response = await fetch(`/admin/logs/${logId}`, { method: 'DELETE' });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Gagal menghapus log.');

            showAlert(result.message || 'Log berhasil dihapus!');
            fetchData(); // Muat ulang data tabel setelah berhasil dihapus
        } catch (error) {
            console.error('Error saat menghapus log:', error);
            showAlert(error.message, 'danger');
        }
    }
    
    // Menggunakan event delegation untuk menangani klik pada tombol hapus
    tableBody.addEventListener('click', function(event) {
        const deleteButton = event.target.closest('.delete-btn');
        if (deleteButton) {
            const logId = deleteButton.dataset.logId;
            deleteLog(logId);
        }
    });

    // Membuat fungsi hapus semua menjadi global agar bisa dipanggil dari atribut onclick di HTML
    window.confirmDeleteAll = async function() {
        if (!confirm('PERINGATAN: Apakah Anda benar-benar yakin ingin menghapus SEMUA data log? Tindakan ini akan menghapus semua catatan dan gambar terkait secara permanen.')) return;
        
        const confirmationText = 'HAPUS SEMUA';
        if (prompt(`Untuk konfirmasi, ketik "${confirmationText}" di bawah ini:`) !== confirmationText) {
            showAlert('Penghapusan dibatalkan. Teks konfirmasi tidak cocok.', 'info');
            return;
        }

        try {
            // AKTIFKAN BLOK KODE DI BAWAH INI:
            const response = await fetch('/admin/logs/delete_all', { method: 'DELETE' });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Gagal menghapus semua log.');
            
            showAlert(result.message, 'success');
            fetchData(); // Muat ulang data tabel setelah berhasil
            
        } catch (error) {
            console.error('Error saat menghapus semua log:', error);
            showAlert(error.message, 'danger');
        }
    };

    // Panggil fungsi fetchData() saat halaman pertama kali dimuat
    fetchData();
});