import os
import json
import cv2
from flask import request, jsonify
from werkzeug.utils import secure_filename
from backend.detection_api import get_roboflow_predictions

def process_uploaded_image(image_path, predictions_raw, output_dir):
    # ✅ safely unpack predictions from dict
    predictions = predictions_raw.get("predictions", []) if isinstance(predictions_raw, dict) else predictions_raw

    os.makedirs(output_dir, exist_ok=True)
    img = cv2.imread(image_path)
    height, width = img.shape[:2]
    cropped_paths = []

    for i, pred in enumerate(predictions):
        x, y, w, h = int(pred["x"]), int(pred["y"]), int(pred["width"]), int(pred["height"])
        x1, y1 = max(x - w // 2, 0), max(y - h // 2, 0)
        x2, y2 = min(x + w // 2, width), min(y + h // 2, height)
        crop = img[y1:y2, x1:x2]

        if crop.size == 0:
            continue

        crop_path = os.path.join(output_dir, f"crop_{i}.jpg")
        cv2.imwrite(crop_path, crop)
        cropped_paths.append(crop_path)

    boxed_path = os.path.join(output_dir, "boxed.jpg")
    draw_boxes(image_path, predictions, boxed_path)
    return boxed_path, cropped_paths

def draw_boxes(image_path, predictions, save_path):
    img = cv2.imread(image_path)
    for i, pred in enumerate(predictions):
        x, y, w, h = int(pred["x"]), int(pred["y"]), int(pred["width"]), int(pred["height"])
        x1, y1 = x - w // 2, y - h // 2
        x2, y2 = x + w // 2, y + h // 2
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img, str(i + 1), (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.imwrite(save_path, img)

def handle_choice_flow(image):
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)

    image_path = os.path.join(upload_dir, secure_filename(image.filename))
    image.save(image_path)

    # ✅ Predict
    predictions = get_roboflow_predictions(image_path)
    # ✅ Save prediction result for later use in /choice preview
    with open(os.path.join(upload_dir, "roboflow_result.json"), "w", encoding="utf-8") as f:
        json.dump({"predictions": predictions}, f, ensure_ascii=False, indent=2)


    # ✅ Draw and crop
    boxed_path, cropped_paths = process_uploaded_image(image_path, predictions, upload_dir)

    return {
        "boxed_path": boxed_path,
        "crops": cropped_paths,
        "count": len(cropped_paths),
        "predictions": predictions
    }
