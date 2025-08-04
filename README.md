# gamecards
遊戲王卡片搜尋

gamecards/
├── app.py                  # ✅ 主 Flask 程式
├── cache.npz               # ✅ 特徵快取，放根目錄合適
├── cards/                  # ✅ 卡牌資料庫
│   ├── images/             # ✅ 所有卡牌圖片
│   └── texts/              # ✅ 每張卡的對應說明文字
├── templates/              # ✅ 前端模板
<!-- │   ├── _desktop.html       # ✅ 桌面專用模板
│   ├── _mobile.html        # ✅ 手機專用模板 -->
│   ├── index.html          # ✅ 首頁
│   ├── about.html          # ✅ 關於我們
│   ├── one.html            # ✅ 單張顯示
│   ├── all.html            # ✅ 全部顯示
│   ├── choice.html         # ✅ 自行選擇
│   └── components/         # ✅ 可重複使用元件（header/footer）
│       ├── header.html
│       └── footer.html
├── static/                 # ✅ 靜態資源
│   ├── css/
│   │   ├── hftop.css       # ✅ 固定一致 header、fooder、top
│   │   ├── main.css        # ✅ index資料夾
│   │   ├── modal.css       # ✅ 彈跳視窗
│   │   └── upload.css      # ✅ 上傳框內
│   ├── js/
│   │   └── hint.js         # ✅ 提示相關互動 JS
│   ├── images/             # ✅ LOGO、背景等 UI 圖片
│   └── data/               # ✅ JSON / 前端模擬資料
├── uploads/                # ✅ 使用者上傳的卡圖（暫存）
├── results/                # ✅ 比對結果圖 + JSON 資料
└── README.md               # ✅ 專案說明

# 安裝套件
pip install -r requirements.txt