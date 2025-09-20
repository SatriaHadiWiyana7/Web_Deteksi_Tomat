// static/js/admin/users.js

document.addEventListener('DOMContentLoaded', function() {
    // --- Elemen DOM ---
    const userModal = document.getElementById('userModal');
    const deleteConfirmModal = document.getElementById('deleteConfirmModal');
    const userForm = document.getElementById('userForm');
    const modalTitle = document.getElementById('modalTitle');
    const passwordHelpText = document.getElementById('passwordHelpText');
    const usersTableBody = document.getElementById('usersTableBody');
    const confirmDeleteButton = document.getElementById('confirmDeleteButton');

    let userToDeleteId = null;
    
    // Fungsi lainnya tetap sama
    window.openUserModal = function(userId = null, name = '', phone = '', email = '') {
        userForm.reset();
        document.getElementById('userId').value = userId || '';
        document.getElementById('displayName').value = name;
        document.getElementById('phoneNumber').value = phone;
        document.getElementById('email').value = email;

        if (userId) {
            modalTitle.textContent = 'Edit Pengguna';
            document.getElementById('password').required = false;
            passwordHelpText.style.display = 'block';
        } else {
            modalTitle.textContent = 'Tambah Pengguna Baru';
            document.getElementById('password').required = true;
            passwordHelpText.style.display = 'none';
        }
        userModal.style.display = 'block';
    }

    window.closeUserModal = function() { userModal.style.display = 'none'; }
    window.closeDeleteConfirmModal = function() { deleteConfirmModal.style.display = 'none'; }
    
    window.promptDeleteUser = function(userId, userName) {
        userToDeleteId = userId;
        document.getElementById('userNameToDelete').textContent = userName;
        deleteConfirmModal.style.display = 'block';
    }

    async function fetchUsers() {
        usersTableBody.innerHTML = '<tr><td colspan="7" class="no-data">Memuat data pengguna...</td></tr>';
        try {
            const response = await fetch('/admin/users/data');
            if (!response.ok) throw new Error('Gagal mengambil data pengguna');
            const users = await response.json();
            
            usersTableBody.innerHTML = '';
            if (users.error || users.length === 0) {
                usersTableBody.innerHTML = `<tr><td colspan="7" class="no-data">${users.error || 'Tidak ada pengguna ditemukan.'}</td></tr>`; return;
            }

            users.forEach((user, index) => {
                const row = usersTableBody.insertRow();
                row.innerHTML = `
                    <td>${index + 1}</td>
                    <td>${user.display_name}</td>
                    <td>${user.phone_number}</td>
                    <td>${user.email}</td>
                    <td>
                        <button class="status-btn ${user.is_active ? 'active' : 'inactive'}" onclick="toggleActivation(${user.id})">
                            ${user.is_active ? 'Aktif' : 'Nonaktif'}
                        </button>
                    </td>
                    <td>${new Date(user.created_at).toLocaleDateString('id-ID')}</td>
                    <td class="action-icons">
                        <button title="Edit" class="edit-btn" onclick="openUserModal('${user.id}', '${user.display_name}', '${user.phone_number}', '${user.email}')"><i class="fas fa-edit"></i></button>
                        <button title="Delete" class="delete-btn" onclick="promptDeleteUser('${user.id}', '${user.display_name}')"><i class="fas fa-trash"></i></button>
                    </td>
                `;
            });
        } catch (error) {
            usersTableBody.innerHTML = '<tr><td colspan="7" class="no-data">Gagal memuat data pengguna.</td></tr>';
            showAlert(error.message, 'danger');
        }
    }
    
    userForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = document.getElementById('userId').value;
        const url = id ? `/admin/users/update/${id}` : '/admin/users/add';
        const payload = {
            display_name: document.getElementById('displayName').value,
            phone_number: document.getElementById('phoneNumber').value,
            email: document.getElementById('email').value
        };
        const password = document.getElementById('password').value;
        if (password || !id) {
            payload.password = password;
        }

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Operasi gagal');
            showAlert(result.message, 'success'); // Sekarang akan memanggil pop-up!
            fetchUsers();
            closeUserModal();
        } catch (error) {
            showAlert(error.message, 'error'); // Tipe 'error' untuk SweetAlert2
        }
    });

    window.toggleActivation = async function(userId) {
        if (!confirm('Apakah Anda yakin ingin mengubah status aktivasi pengguna ini?')) return;
        try {
            const response = await fetch(`/admin/users/toggle_activation/${userId}`, { method: 'POST' });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Gagal mengubah status');
            showAlert(result.message, 'success');
            fetchUsers();
        } catch (error) {
            showAlert(error.message, 'error');
        }
    }
    
    confirmDeleteButton.addEventListener('click', async () => {
        if (!userToDeleteId) return;
        try {
            const response = await fetch(`/admin/users/delete/${userToDeleteId}`, { method: 'DELETE' });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Gagal menghapus pengguna');
            showAlert(result.message, 'success');
            fetchUsers();
        } catch (error) {
            showAlert(error.message, 'error');
        } finally {
            closeDeleteConfirmModal();
            userToDeleteId = null;
        }
    });

    fetchUsers();
});