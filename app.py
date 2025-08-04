import os
from flask import Flask, render_template, request, Response
from backend.matcher import *
from backend.all_flow import recognize_multi_cards
import json
from backend.choice_flow import process_uploaded_image, draw_boxes
from backend.detection_api import get_roboflow_predictions
from flask import session, jsonify


app = Flask(__name__)
app.secret_key = "tim-secret-123"  # 🔐 Replace with something random in production


def get_css_files():
    css_folder = os.path.join(app.static_folder, 'css')
    return [f'css/{f}' for f in os.listdir(css_folder) if f.endswith('.css')]

@app.route('/')
def index():
    return render_template('index.html', css_files=get_css_files())

@app.route('/about')
def about():
    return render_template('about.html', css_files=get_css_files())

@app.route('/one')
def one():
    return render_template('one.html', css_files=get_css_files(), page_class='page-one')

@app.route('/all')
def all():
    return render_template('all.html', css_files=get_css_files(), page_class='page-all')


@app.route('/choice')
def choice():
    try:
        image_path = os.path.join(os.path.dirname(__file__), "uploads", "choice_temp.jpg")
        output_dir = os.path.join(os.path.dirname(__file__), "uploads")

        # ✅ Step 1: Get predictions
        predictions = get_roboflow_predictions(image_path)

        # ✅ Step 2: Process image with predictions
        boxed_path, cropped_paths = process_uploaded_image(image_path, predictions, output_dir)

        # ✅ Step 3: Serialize prediction boxes to JSON
        boxes_json = json.dumps(predictions)

        print("Predictions:", predictions)

        return render_template(
            'choice.html',
            css_files=get_css_files(), 
            image_data=boxed_path,
            boxes_json=boxes_json,
            page_class='page-choice',
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(f"<p>處理錯誤：{str(e)}</p>", status=500, mimetype='text/html; charset=utf-8')


# ----------- 單卡辨識 -----------
@app.route('/match_one', methods=['POST'])
def match_one():
    file = request.files.get("image")
    if not file:
        print("❌ 沒有收到圖片")
        return jsonify({"error": "❌ 請正確上傳一張圖檔"}), 400

    img_data = file.read()
    temp_path = os.path.join("uploads", "temp.jpg")

    try:
        result = process_image(img_data)

        if isinstance(result, str):
            return jsonify({
                "images_html": "",
                "text_html": result
            })

        (images_html, text_html), card_name_jp = result
        return jsonify({
            "images_html": images_html,
            "text_html": text_html,
            "card_name_jp": card_name_jp
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"處理錯誤：{str(e)}"}), 500
    finally:
        try:
            os.remove(temp_path)
        except Exception as e:
            print(f"⚠️ 無法刪除上傳圖檔: {e}")

@app.route('/get_price', methods=['POST'])
def get_price():
    data = request.get_json()
    card_name_jp = data.get("card_name_jp", "").strip()

    if not card_name_jp:
        return jsonify({"price_html": "<br><b>平均價格:</b> 名稱錯誤或缺失"})

    price_html = get_price_html(card_name_jp)
    return jsonify({"price_html": price_html})

# ----------- 多卡辨識 -----------
@app.route('/match_all', methods=['POST'])
def match_all():
    file = request.files.get("image")
    if not file:
        print("❌ 沒有收到圖片")
        return Response("<p>❌ 請正確上傳一張圖檔</p>", status=400, mimetype='text/html; charset=utf-8')

    upload_dir = os.path.join(os.path.dirname(__file__), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    image_path = os.path.join(upload_dir, "multi_temp.jpg")
    file.save(image_path)

    try:
        result_html = recognize_multi_cards(image_path)
        return Response(result_html, mimetype='text/html; charset=utf-8')
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(f"<p>處理錯誤：{str(e)}</p>", status=500, mimetype='text/html; charset=utf-8')
    finally:
        try:
            os.remove(image_path)
        except Exception as e:
            print(f"⚠️ 無法刪除上傳圖檔: {e}")

# ----------- 分類模式 -----------
@app.route('/upload_choice_image', methods=['POST'])
def upload_choice_image():
    file = request.files.get("image")
    if not file:
        print("❌ 沒有收到圖片")
        return Response("<p>❌ 請正確上傳一張圖檔</p>", status=400, mimetype='text/html; charset=utf-8')

    upload_dir = os.path.join(os.path.dirname(__file__), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    image_path = os.path.join(upload_dir, "choice_temp.jpg")
    file.save(image_path)

    return render_template('choice.html', css_files=get_css_files())

from backend.crop import *
import json

# ----------- 自行選擇 -----------
@app.route("/match_choice", methods=["POST"])
def match_choice():
    try:
        index = request.json.get("index")
        crop_path = f"./uploads/crop_{index}.jpg"
        if not os.path.exists(crop_path):
            return jsonify({"error": "Crop image not found"}), 404
        
        result = process_image_file(crop_path)

        if isinstance(result, str):
            return jsonify({
                "images_html": "",
                "text_html": result
            })

        (images_html, text_html), card_name_jp = result
        return jsonify({
            "images_html": images_html,
            "text_html": text_html,
            "card_name_jp": card_name_jp
        })

    except Exception as e:
        print("❌ Error in match_choice:", e)
        return jsonify({"error": "Internal error"}), 500
    
@app.route("/choice_result")
def choice_result():
    result = session.get("match_result")
    result_html = f"<p>{result}</p>" if result else "<p>❌ 找不到辨識結果</p>"
    return render_template("choice_result.html", result_html=result_html)

from flask import send_from_directory

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory("uploads", filename)

if __name__ == '__main__':
    app.run(debug=True)
