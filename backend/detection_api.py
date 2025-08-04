import os
import requests

# Roboflow API 設定
API_KEY = ""
MODEL_ID = "my-first-project-hcdmk/10"
CONFIDENCE = 0.18
UPLOAD_FOLDER = "static/uploads"

def get_roboflow_predictions(image_path):
    """
    使用 Roboflow API 的 HTTP POST 方式，偵測圖片中的卡片位置，並回傳裁切資訊。
    """
    try:
        url = f"https://detect.roboflow.com/{MODEL_ID}?api_key={API_KEY}&confidence={CONFIDENCE}&overlap=0.3"

        with open(image_path, "rb") as f:
            response = requests.post(url, files={"file": f})

        if response.status_code != 200:
            print(f"Roboflow API 呼叫失敗: {response.text}")
            return {"predictions": []}

        result = response.json()
        preds = result.get("predictions", [])
        clean_preds = [
            {"x": p["x"], "y": p["y"], "width": p["width"], "height": p["height"]}
            for p in preds
        ]
        return {"predictions": clean_preds}

    except Exception as e:
        print(f"Roboflow API 調用錯誤: {e}")
        return {"predictions": []}
