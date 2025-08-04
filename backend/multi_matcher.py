import os
import cv2
import numpy as np
import faiss
import re
import html
from tqdm import tqdm
from collections import defaultdict
from backend.image_processing import load_or_build_cache
from backend.avg_price import get_average_price, to_fullwidth, convert_jpy_to_twd


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INFO_DIR = os.path.join(BASE_DIR, "data", "cards_info")
INDEX_PATH = os.path.join(BASE_DIR, "data", "cache", "all.index")


def build_or_load_index(des_list, desc_dim):
    if os.path.exists(INDEX_PATH):
        return faiss.read_index(INDEX_PATH)
    quantizer = faiss.IndexFlatL2(desc_dim)
    index = faiss.IndexIVFPQ(quantizer, desc_dim, 500, 24, 8)
    index.train(des_list)
    index.add(des_list)
    faiss.write_index(index, INDEX_PATH)
    print("✅ 建立新索引完成")
    return index


def match_single_crop(des1, index, descs, names):
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
    if best_idx is None or len(good_per_img[best_idx]) < 2:
        return None

    return names[best_idx]


def read_info(matched_name):
    card_id = os.path.splitext(matched_name)[0].zfill(8)
    matches = [
        fname for fname in os.listdir(INFO_DIR)
        if fname.startswith(card_id) and fname.lower().endswith(".txt")
    ]
    if not matches:
        print(f"⚠️ 找到相似卡片 {matched_name}，但缺少對應資訊檔案")
        return None, card_id

    info_file = os.path.join(INFO_DIR, matches[0])
    print(f"🔍 匹配資訊檔案：{info_file}")

    with open(info_file, encoding="utf-8") as f:
        lines = f.readlines()

    card_name_jp = ""
    for line in lines:
        if line.startswith("日文名:"):
            card_name_jp = line.replace("日文名:", "").strip()
            break

    info = "".join(lines)
    info = html.escape(info, quote=False).replace("圖片 URL:", "")
    info = info.replace("\n", " <br>")
    info = re.sub(r"(https?://[^\s]+)", r'<img src="\1" alt="圖片" />', info)

    image_html_list = re.findall(r'<img src="[^"]+" alt="圖片" />', info)
    images_html = "".join(image_html_list)

    text_html = re.sub(r'<img src="[^"]+" alt="圖片" />', '', info)

    # Get average price using correct Japanese name
    # fullwidth_name = to_fullwidth(card_name_jp)
    # average_price = get_average_price(fullwidth_name)

    
    # if average_price is not None:
    #     from backend.avg_price import convert_jpy_to_twd  # add this if not already imported
    #     price_twd = convert_jpy_to_twd(average_price)
    #     if price_twd:
    #         text_html += f"<br><b>平均價格:</b> {average_price} 円 (NT${price_twd})"
    #     else:
    #         text_html += f"<br><b>平均價格:</b> {average_price} 円 (TWD轉換失敗)"
    # else:
    #     text_html += "<br><b>平均價格:</b> 價格未找到"

    return (text_html, images_html), card_id


def process_multi_image(image_bytes_list):
    paths, names, kp_attrs, descs, all_desc = load_or_build_cache("all")
    index = build_or_load_index(all_desc, descs[0].shape[1])
    sift = cv2.SIFT_create()

    result_dict = defaultdict(lambda: [0, None])  # card_id: [count, info]

    for img_data in tqdm(image_bytes_list, desc="處理每張裁切圖片"):
        img = cv2.imdecode(np.frombuffer(img_data, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            continue
        kp, des = sift.detectAndCompute(img, None)
        if des is None or len(kp) == 0:
            continue

        matched_name = match_single_crop(des, index, descs, names)
        if matched_name:
            (info_text_html, images_html), card_id = read_info(matched_name)
            if info_text_html:
                result_dict[card_id][0] += 1
                result_dict[card_id][1] = (info_text_html, images_html)

    if not result_dict:
        return "<p>❌ 沒有辨識出任何卡片</p>"

    sorted_items = sorted(result_dict.items(), key=lambda x: x[0])
    total_cards = sum([v[0] for _, v in sorted_items])

    result_html = f"<p id='cardSummary' style='padding: 0rem 0rem 1.5rem 2rem; font-size: large;'>辨識出 {total_cards} 張卡片（{len(sorted_items)} 種）：</p>\n<div class='card-list'>\n"
    for card_id, (count, (text_html, images_html)) in sorted_items:
        result_html += f"""
        <div class="card-item">
            <div class="card-images">
                {images_html}
            </div>
            <div class="card-text">
                <p><strong>{count} 張</strong></p>
                {text_html}
            </div>
        </div>\n
        """
    result_html += "</div>"
    return result_html


def run_multi_match_from_crops(crop_paths):
    image_bytes_list = []
    for path in crop_paths:
        with open(path, "rb") as f:
            image_bytes_list.append(f.read())
    return process_multi_image(image_bytes_list)
