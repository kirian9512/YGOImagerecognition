import os
import numpy as np
import cv2
import faiss
import re
import html
from backend.image_processing import load_or_build_cache
from backend.classified_api import get_card_class
from backend.avg_price import get_average_price, to_fullwidth, convert_jpy_to_twd


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INFO_DIR = os.path.join(BASE_DIR, "data", "cards_info")

def process_image(img_data):
    # 1. 儲存圖片至暫存檔（分類器需要路徑）
    upload_dir = os.path.join(BASE_DIR, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    temp_path = os.path.join(upload_dir, "temp.jpg")
    with open(temp_path, "wb") as f:
        f.write(img_data)
        
    # 2. 執行 Roboflow 分類
    category = get_card_class(temp_path)
    if not category:
        raise ValueError("❌ Roboflow 分類失敗，無法辨識類別")

    # 3. 擷取特徵
    sift = cv2.SIFT_create()
    img = cv2.imdecode(np.frombuffer(img_data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError("❌ 無法讀取圖像")

    kp1, des1 = sift.detectAndCompute(img, None)
    if des1 is None or len(kp1) == 0:
        raise ValueError("❌ 找不到特徵點")
    d = des1.shape[1]

    # 4. 載入快取
    paths, names, kp_attrs, descs, all_desc = load_or_build_cache(category)

    # 5. 建立 / 載入索引
    index_path = os.path.join(os.path.dirname(INFO_DIR), "cache", f"{category}.index")
    if os.path.exists(index_path):
        index = faiss.read_index(index_path)
    else:
        quantizer = faiss.IndexFlatL2(d)
        index = faiss.IndexIVFPQ(quantizer, d, 500, 24, 8)
        index.train(all_desc)
        index.add(all_desc)
        faiss.write_index(index, index_path)

    index.nprobe = 1

    # 6. 搜尋比對
    D, I = index.search(des1.astype('float32'), 2)
    good_per_img = [[] for _ in descs]
    boundaries = np.cumsum([len(d) for d in descs])
    for qi in range(len(des1)):
        d0, d1 = D[qi]
        if d0 < 0.9 * d1:
            tr = int(I[qi, 0])
            idx = np.searchsorted(boundaries, tr, side='right')
            start = boundaries[idx - 1] if idx > 0 else 0
            local = tr - start
            good_per_img[idx].append(cv2.DMatch(qi, local, d0))

    best_idx = max(range(len(good_per_img)), key=lambda i: len(good_per_img[i]), default=None)
    if best_idx is None or len(good_per_img[best_idx]) <= 1:
        return "<p>❌ 沒有找到匹配的卡片</p>"

    matched_name = names[best_idx]
    card_id = matched_name[:8].zfill(8)

    # 7. 模糊匹配 txt 檔案
    matches = [
        fname for fname in os.listdir(INFO_DIR)
        if fname.startswith(card_id) and fname.lower().endswith(".txt")
    ]

    if not matches:
        return f"<p>⚠️ 找到相似卡片 {matched_name}，但缺少對應資訊檔</p>"

    info_file = os.path.join(INFO_DIR, matches[0])
    print(f"🔍 匹配資訊檔案：{info_file}")

    
    with open(info_file, encoding="utf-8") as f:
        lines = f.readlines()

    info = "".join(lines)
    info = html.escape(info, quote=False).replace("圖片 URL:", "")
    info = info.replace("\n", " <br>")
    info = re.sub(r"(https?://[^\s]+)", r'<img src="\1" alt="圖片" />', info)
    
    image_html_list = re.findall(r'<img src="[^"]+" alt="圖片" />', info)
    images_html = "".join(image_html_list)
    text_html = re.sub(r'<img src="[^"]+" alt="圖片" />', '', info)

    # Get average price using correct Japanese name
    card_name_jp = ""
    for line in lines:
        if line.startswith("日文名:"):
            card_name_jp = line.replace("日文名:", "").strip()
            break
    
    
    return (images_html, text_html), card_name_jp

def get_price_html(card_name_jp):
    fullwidth_name = to_fullwidth(card_name_jp)
    average_price = get_average_price(fullwidth_name)

    if average_price is not None:
        from backend.avg_price import convert_jpy_to_twd  # add this if not already imported
        price_twd = convert_jpy_to_twd(average_price)
        if price_twd:
            return f"<br><b>平均價格:</b> {average_price} 円 (NT${price_twd})"
        else:
            return f"<br><b>平均價格:</b> {average_price} 円 (TWD轉換失敗)"
    else:
        return "<br><b>平均價格:</b> 價格未找到"

#choice
def process_image_file(image_path):
    """
    給定圖像路徑（例如 crop_0.jpg），直接辨識。
    """
    with open(image_path, "rb") as f:
        img_data = f.read()
    return process_image(img_data)