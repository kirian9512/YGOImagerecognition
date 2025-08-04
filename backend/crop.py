import os
import cv2
import uuid
from backend.detection_api import get_roboflow_predictions

def process_roboflow_detections(image_path, output_crop_dir="uploads"):
    """
    使用 Roboflow 偵測卡片，根據結果裁切圖片，回傳所有裁切後圖檔路徑
    """
    os.makedirs(output_crop_dir, exist_ok=True)
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"❌ 無法載入圖片：{image_path}")

    height, width = img.shape[:2]
    roboflow_result = get_roboflow_predictions(image_path)
    results = []

    for i, pred in enumerate(roboflow_result.get("predictions", [])):
        x, y, w, h = int(pred['x']), int(pred['y']), int(pred['width']), int(pred['height'])
        x1 = max(x - w // 2, 0)
        y1 = max(y - h // 2, 0)
        x2 = min(x + w // 2, width)
        y2 = min(y + h // 2, height)

        if x2 <= x1 or y2 <= y1:
            print(f"⚠️ Skipped invalid box #{i}")
            continue

        crop = img[y1:y2, x1:x2]
        if crop.size == 0 or crop.shape[0] < 20 or crop.shape[1] < 20:
            print(f"⚠️ Skipped too-small crop #{i}: shape={crop.shape}")
            continue

        unique_id = uuid.uuid4().hex[:8]
        crop_path = os.path.join(output_crop_dir, f"crop_{i}_{unique_id}.jpg")
        cv2.imwrite(crop_path, crop)
        results.append(crop_path)

    return results
