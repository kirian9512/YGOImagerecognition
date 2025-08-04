import requests

# --- Roboflow API Config ---
API_KEY = ""
MODEL_ID = "color-zagok/6"
CONFIDENCE = 0.18

def get_card_class(image_path):
    try:
        url = f"https://detect.roboflow.com/{MODEL_ID}?api_key={API_KEY}&confidence={CONFIDENCE}&overlap=0.3"
        with open(image_path, "rb") as f:
            response = requests.post(url, files={"file": f})

        if response.status_code != 200:
            print("❌ Roboflow error:", response.text)
            return None

        result = response.json()
        predictions = result.get("predictions", [])
        if predictions:
            return predictions[0].get("class")
        else:
            print("❌ No predictions found.")
            return None

    except Exception as e:
        print("❌ Error during Roboflow call:", e)
        return None
