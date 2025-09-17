document.addEventListener("DOMContentLoaded", function () {
    // --- State Aplikasi ---
    const bodyData = document.body.dataset;
    let isUserLoggedIn = bodyData.loggedIn === 'true';

    // --- Pemilihan Elemen DOM ---
    const screens = document.querySelectorAll(".screen");
    const dropArea = document.querySelector(".drop-area");
    const uploadBtn = document.querySelector(".upload-btn");
    const backBtn = document.querySelector(".back-btn");
    const resultImage = document.getElementById("result-image");
    const healthStatus = document.getElementById("health-status");
    const accuracyLevel = document.getElementById("accuracy-level");
    const infoMessage = document.getElementById("info-message");
    const userProfileLink = document.getElementById("user-profile-link");
    const navHistory = document.getElementById("nav-history");
    const historySection = document.getElementById("detection-history-section");
    const aboutUsSection = document.getElementById("about-us-section");
    const showHistoryBtn = document.getElementById("show-history-btn");
    const btnLogin = document.getElementById("btn-login");
    const btnRegister = document.getElementById("btn-register");
    const btnLogout = document.getElementById("btn-logout");

    // --- Fungsi Pengelola Tampilan (UI) ---
    function showScreen(screenId) {
        screens.forEach(screen => screen.classList.remove("active"));
        const activeScreen = document.getElementById(screenId);
        if (activeScreen) activeScreen.classList.add("active");
        
        // Atur visibilitas elemen lain berdasarkan layar yang aktif
        // About Us section selalu ditampilkan di home-screen
        aboutUsSection.style.display = (screenId === 'home-screen') ? 'block' : 'none';
        historySection.style.display = (screenId === 'home-screen' && isUserLoggedIn) ? 'block' : 'none';
    }

    function updateAuthUI() {
        if (btnLogin) btnLogin.style.display = isUserLoggedIn ? 'none' : 'inline-block';
        if (btnRegister) btnRegister.style.display = isUserLoggedIn ? 'none' : 'inline-block';
        if (userProfileLink) userProfileLink.style.display = isUserLoggedIn ? 'flex' : 'none';
        if (btnLogout) btnLogout.style.display = isUserLoggedIn ? 'inline-block' : 'none';
        if (navHistory) navHistory.style.display = isUserLoggedIn ? 'block' : 'none';
        if (isUserLoggedIn) fetchAndDisplayHistory();
    }
    
    function displayResults(result, imageUrl) {
        // Tampilkan modal popup dengan hasil deteksi
        showDetectionModal(result, imageUrl);
    }

    function showDetectionModal(result, imageUrl) {
        const modal = document.getElementById('detection-modal');
        const modalImage = document.getElementById('modal-result-image');
        const modalStatusIcon = document.getElementById('modal-status-icon');
        const modalStatusText = document.getElementById('modal-status-text');
        const modalConfidenceText = document.getElementById('modal-confidence-text');
        const modalDescriptionText = document.getElementById('modal-description-text');

        // Set gambar hasil
        modalImage.src = imageUrl;

        // Set status dan confidence
        modalStatusText.textContent = result.label;
        modalConfidenceText.textContent = `Tingkat Akurasi: ${(result.confidence * 100).toFixed(2)}%`;

        // Set icon berdasarkan hasil
        if (result.label.toLowerCase().includes('healthy')) {
            modalStatusIcon.src = "/static/assets/check-svgrepo-com.svg";
            modalDescriptionText.textContent = "Selamat! Tanaman tomat Anda terlihat sehat dan tidak terinfeksi penyakit layu fusarium. Tetap jaga kondisi tanaman dengan perawatan yang baik.";
        } else {
            modalStatusIcon.src = "/static/assets/info-circle-svgrepo-com.svg";
            modalDescriptionText.textContent = "Peringatan! Tanaman tomat Anda menunjukkan gejala terinfeksi penyakit layu fusarium. Segera lakukan tindakan pencegahan dan pengobatan yang tepat.";
        }

        // Tampilkan modal
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
    }

    function hideDetectionModal() {
        const modal = document.getElementById('detection-modal');
        modal.style.display = 'none';
        document.body.style.overflow = 'auto'; // Restore scrolling
        
        // Pastikan About Us section tetap terlihat setelah modal ditutup
        if (aboutUsSection) {
            aboutUsSection.style.display = 'block';
        }
    }

    // --- Fungsi Logika & API ---
    async function fetchAndDisplayHistory() {
        if (!isUserLoggedIn) return;
        const historyTableBody = historySection.querySelector("tbody");
        historyTableBody.innerHTML = '<tr><td colspan="4">Memuat riwayat...</td></tr>';
        
        try {
            const response = await fetch('/history');
            if (!response.ok) throw new Error('Gagal memuat riwayat');
            const historyData = await response.json();

            if (historyData.length === 0) {
                historyTableBody.innerHTML = '<tr><td colspan="4">Tidak ada riwayat deteksi.</td></tr>';
                return;
            }
            
            historyTableBody.innerHTML = '';
            historyData.forEach((item, index) => {
                const row = historyTableBody.insertRow();
                row.innerHTML = `
                    <td>${index + 1}</td>
                    <td>${new Date(item.detection_date).toLocaleDateString('id-ID')}</td>
                    <td>${item.result}</td>
                    <td><img src="${item.raw_image_url}" alt="Riwayat Gambar" style="width: 50px; height: 50px; object-fit: cover;"></td>
                `;
            });
        } catch (error) {
            historyTableBody.innerHTML = '<tr><td colspan="4">Gagal memuat riwayat.</td></tr>';
            console.error("Error:", error);
        }
    }
    
    async function sendImageToServer(file) {
        showScreen("loading-screen");
        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch("/upload", { method: "POST", body: formData });
            const data = await response.json();
            
            if (data.error) throw new Error(data.error);
            
            displayResults(data.result, URL.createObjectURL(file));
            if (isUserLoggedIn) fetchAndDisplayHistory(); // Refresh riwayat setelah upload
            
        } catch (error) {
            console.error("Error:", error);
            alert("Terjadi kesalahan: " + error.message);
            showScreen("home-screen");
        }
    }

    // --- Event Listeners ---
    uploadBtn.addEventListener("click", () => {
        const input = document.createElement("input");
        input.type = "file";
        input.accept = "image/png, image/jpeg, image/jpg";
        input.onchange = (event) => sendImageToServer(event.target.files[0]);
        input.click();
    });

    dropArea.addEventListener("dragover", (e) => e.preventDefault());
    dropArea.addEventListener("drop", (e) => {
        e.preventDefault();
        if (e.dataTransfer.files.length > 0) {
            sendImageToServer(e.dataTransfer.files[0]);
        }
    });

    backBtn.addEventListener("click", () => showScreen("home-screen"));
    showHistoryBtn.addEventListener('click', (e) => {
        e.preventDefault();
        showScreen('home-screen'); // Riwayat ditampilkan di home screen
        historySection.scrollIntoView({ behavior: 'smooth' });
    });

    // --- Modal Event Listeners ---
    const modal = document.getElementById('detection-modal');
    const closeBtn = document.querySelector('.close-btn');
    const modalCloseBtn = document.getElementById('modal-close-btn');
    const modalTryAgainBtn = document.getElementById('modal-try-again-btn');

    // Close modal when clicking X button
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            hideDetectionModal();
            // Pastikan kembali ke home-screen dengan About Us terlihat
            showScreen("home-screen");
        });
    }

    // Close modal when clicking close button
    if (modalCloseBtn) {
        modalCloseBtn.addEventListener('click', () => {
            hideDetectionModal();
            // Pastikan kembali ke home-screen dengan About Us terlihat
            showScreen("home-screen");
        });
    }

    // Try again button - close modal and return to home screen
    if (modalTryAgainBtn) {
        modalTryAgainBtn.addEventListener('click', () => {
            hideDetectionModal();
            showScreen("home-screen");
            // Pastikan About Us section tetap terlihat
            if (aboutUsSection) {
                aboutUsSection.style.display = 'block';
            }
        });
    }

    // Close modal when clicking outside of it
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                hideDetectionModal();
                // Pastikan kembali ke home-screen dengan About Us terlihat
                showScreen("home-screen");
            }
        });
    }

    // Close modal with Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal && modal.style.display === 'block') {
            hideDetectionModal();
            // Pastikan kembali ke home-screen dengan About Us terlihat
            showScreen("home-screen");
        }
    });
    
    // --- Inisialisasi ---
    updateAuthUI();
    showScreen("home-screen");
});