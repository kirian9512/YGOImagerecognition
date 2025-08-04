let currentMode = null;

function switchMode(mode) {
    document.querySelectorAll('.mode-container').forEach(el => el.style.display = 'none');
    document.getElementById(`block-${mode}`).style.display = 'block';

    document.querySelectorAll('.mode-button').forEach(btn => {
        btn.classList.remove('mode-one-active', 'mode-all-active', 'mode-choice-active');
    });

    const selectedBtn = document.querySelector(`.mode-button[data-mode="${mode}"]`);
    if (selectedBtn) {
        selectedBtn.classList.add(`mode-${mode}-active`);
    }
}

function createUploadBlockHTML(mode) {
    return `
        <input type="file" id="fileInput-${mode}" style="display:none;">
        <div class="file-name" id="fileNameDisplay-${mode}"></div>
        <img id="previewImage-${mode}" class="preview-image" style="display:none;">
        <div class="progress-bar-container-${mode}">
            <div class="progress-bar-${mode}" id="progressBar-${mode}"></div>
        </div>
        <button id="selectButton-${mode}" class="upload-button upload-button-${mode}">選取檔案</button>
        <p class="upload-hint">或拖曳檔案到此</p>
    `;
}

function setupUploadEvents(mode) {
    const fileInput = document.getElementById(`fileInput-${mode}`);
    const selectButton = document.getElementById(`selectButton-${mode}`);
    const uploadArea = document.getElementById(`uploadArea-${mode}`);
    const fileNameDisplay = document.getElementById(`fileNameDisplay-${mode}`);
    const previewImage = document.getElementById(`previewImage-${mode}`);
    const progressContainer = uploadArea.querySelector(`.progress-bar-container-${mode}`);
    const progressBar = document.getElementById(`progressBar-${mode}`);

    selectButton.onclick = (e) => {
        e.stopPropagation();
        fileInput.click();
    };
    uploadArea.onclick = () => fileInput.click();

    fileInput.onchange = () => {
        if (fileInput.files.length > 0) {
            const file = fileInput.files[0];
            fileNameDisplay.textContent = `已選取：${file.name}`;
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = e => {
                    previewImage.src = e.target.result;
                    previewImage.style.display = 'block';
                    previewImage.classList.remove('fade-in');
                    void previewImage.offsetWidth;
                    previewImage.classList.add('fade-in');
                };
                reader.readAsDataURL(file);
            } else {
                previewImage.style.display = 'none';
            }

            progressContainer.style.display = 'block';
            progressBar.style.width = '0%';

            let percent = 0;
            const interval = setInterval(() => {
                percent += 10;
                progressBar.style.width = `${percent}%`;
                if (percent >= 100) {
                    clearInterval(interval);
                    setTimeout(() => {
                        progressContainer.style.transition = 'opacity 1s ease';
                        progressContainer.style.opacity = '0';
                        setTimeout(() => {
                            progressContainer.style.display = 'none';
                            progressContainer.style.opacity = '1';
                        }, 1000);
                    }, 800);
                }
            }, 100);
        }
    };

    uploadArea.ondragover = e => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    };
    uploadArea.ondragleave = e => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
    };
    uploadArea.ondrop = e => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
            fileInput.onchange();
        }
    };
}

function openModal(mode) {
    const fileInput = document.getElementById(`fileInput-${mode}`);
    if (!fileInput || fileInput.files.length === 0) {
        alert('💥 請上傳一張圖檔');
        return;
    }

    const file = fileInput.files[0];
    const allowedExts = ['jpg', 'jpeg', 'png', 'jfif', 'webp'];
    const fileName = file.name.toLowerCase();
    const ext = fileName.substring(fileName.lastIndexOf('.') + 1);
    if (!allowedExts.includes(ext)) {
        alert('❌ 僅支援 jpg、jpeg、png、jfif、webp 格式的圖檔');
        return;
    }

    currentMode = mode;
    const modal = document.getElementById(`myModal-${mode}`);
    const title = modal.querySelector('.modal-title');
    const message = modal.querySelector('.modal-message');

    const modeTitleMap = {
        one: '單張顯示 📌',
        all: '⚠️ 全部顯示',
        choice: '自行選擇 👆'
    };

    title.textContent = modeTitleMap[mode] || '提醒';

    if (mode === 'all') {
        message.innerHTML = '由於卡片過多<br>顯示速度會較慢<br>是否確定以此方式做搜尋？';
    } else if (mode === 'choice') {
        message.innerHTML = '不會顯示全部資訊<br>需自行選擇想要呈現的卡片<br>是否確定以此方式做搜尋？';
    } else if (mode === 'one') {
        message.innerHTML = '只會顯示一張卡片<br>是否確定以此方式做搜尋？';
    }

    modal.classList.remove('hidden');
}

function closeModal() {
    if (currentMode) {
        document.getElementById(`myModal-${currentMode}`).classList.add('hidden');
    }
}

function confirmAction() {
    if (!currentMode) return;

    const fileInput = document.getElementById(`fileInput-${currentMode}`);
    const file = fileInput.files[0];

    if (!file) {
        alert('❌ 請先上傳圖片');
        return;
    }

    const reader = new FileReader();
    reader.onload = function (e) {
    sessionStorage.setItem('uploadedImage', e.target.result);

    if (currentMode === 'one') {
        window.location.href = "/one";
    } else if (currentMode === 'all') {
        window.location.href = "/all";
    } else if (currentMode === 'choice') {
        const formData = new FormData();
        formData.append('image', file);

        fetch('/upload_choice_image', {
        method: 'POST',
        body: formData,
        })
        .then(response => {
            if (response.ok) {
            window.location.href = "/choice";
            } else {
            alert('❌ 圖片上傳失敗');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('❌ 圖片上傳失敗');
        });
    } else {
        alert("⚠️ 不明的模式");
    }
    };

    reader.readAsDataURL(file);
    closeModal();
}

window.onload = () => {
    const blockOne = document.getElementById('block-one');
    if (!blockOne) return; // ❗不是首頁就直接結束

    const activeBtn = document.querySelector('.mode-button.mode-one-active, .mode-button.mode-all-active, .mode-button.mode-choice-active');
    const initialMode = activeBtn ? activeBtn.dataset.mode : 'one';
    switchMode(initialMode); 

    ['one', 'all', 'choice'].forEach(mode => {
        const area = document.getElementById(`uploadArea-${mode}`);
        area.innerHTML = createUploadBlockHTML(mode);
        setupUploadEvents(mode);
    });
};

window.onscroll = function () {
    const btn = document.getElementById("myBtn");
    if (!btn) return;
    if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
        btn.style.display = "block";
    } else {
        btn.style.display = "none";
    }
};

function topFunction() {
    document.body.scrollTop = 0;
    document.documentElement.scrollTop = 0;
}
