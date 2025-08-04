import os
from backend.crop import process_roboflow_detections
from backend.multi_matcher import run_multi_match_from_crops

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")

def recognize_multi_cards(image_path):

    # 1. 利用 Roboflow 偵測並裁切卡片圖
    crop_paths = process_roboflow_detections(image_path, output_crop_dir=UPLOAD_DIR)

    # 2. 若無偵測到卡片，直接回傳訊息
    if not crop_paths:
        return "<p>❌ 沒有偵測到任何卡片</p>"

    # 3. 執行多卡辨識
    result_html = run_multi_match_from_crops(crop_paths)

    # 4. 辨識後刪除所有裁切圖
    for path in crop_paths:
        try:
            os.remove(path)
        except Exception as e:
            print(f"⚠️ 無法刪除裁切檔案 {path}: {e}")

    return result_html
