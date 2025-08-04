window.onload = () => {
    const base64 = sessionStorage.getItem('uploadedImage');
    if (!base64) {
        console.log("⚠️ 沒有圖片可辨識");
        return;
    }

    console.log("📤 發送辨識請求（多卡）...");

    const byteString = atob(base64.split(',')[1]);
    const mimeString = base64.split(',')[0].split(':')[1].split(';')[0];
    const ab = new ArrayBuffer(byteString.length);
    const ia = new Uint8Array(ab);
    for (let i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
    }
    const blob = new Blob([ab], { type: mimeString });
    const file = new File([blob], 'upload.jpg', { type: mimeString });

    const formData = new FormData();
    formData.append('image', file);

    fetch('/match_all', {
        method: 'POST',
        body: formData
    })
        .then(response => response.text())
        .then(html => {
            const result = document.getElementById('cardResult');
            if (result) {
                result.innerHTML = html;
                sessionStorage.removeItem('uploadedImage');
                updateCardListLayout();
            }
        })
        .catch(err => {
            console.error('❌ 發送資料失敗', err);
            const result = document.getElementById('cardResult');
            if (result) result.innerHTML = '❌ 發送資料失敗';
        });
};

// 萃取主分類
function parseCategory(text) {
    const lines = text.split('<br>').map(line => line.trim());
    let typeLine = lines.find(line => line.startsWith('類型:'));
    if (!typeLine) return '通常';

    let cardType = typeLine.replace('類型:', '').trim();

    const CATEGORIES = ['魔法', '陷阱'];
    for (const cat of CATEGORIES) {
        if (cardType.includes(cat)) return cat;
    }

    if (cardType.includes('靈擺')) return '靈擺';

    const special = ['同步', '超量', '融合', '連結', '儀式'];
    for (const sp of special) {
        if (cardType.includes(sp)) return sp;
    }

    if (cardType.includes('怪獸')) {
        if (cardType.includes('效果')) return '效果';
        else return '通常';
    }

    return '通常';
}

function updateCardListLayout() {
    const cardList = document.querySelector('.card-list');
    if (!cardList) return;
    const visibleItems = Array.from(cardList.children).filter(
        el => el.classList.contains('card-item') && el.style.display !== 'none'
    );
    if (visibleItems.length === 1) {
        cardList.classList.add('single-column');
    } else {
        cardList.classList.remove('single-column');
    }
}

// 類型篩選功能
function filterCards(button, type) {
    document.querySelectorAll('.filter-bar button').forEach(btn => {
        btn.classList.remove('active');
    });
    button.classList.add('active');

    const cards = document.querySelectorAll('.card-item');
    cards.forEach(card => {
        const text = card.querySelector('.card-text')?.innerHTML || '';
        const category = parseCategory(text);
        if (type === '全部' || category === type) {
            card.style.display = 'flex';
        } else {
            card.style.display = 'none';
        }
    });

    const summary = document.getElementById('cardSummary');
    if (summary) {
        summary.style.display = (type === '全部') ? 'block' : 'none';
    }
    
    updateCardListLayout();
}