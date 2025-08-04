import cv2

def draw_boxes(image_path, predictions, output_path):
    """
    在原始圖片上畫出 Roboflow 偵測框與編號，並儲存成新圖片。

    :param image_path: 原始圖片路徑（例如 uploads/original.jpg）
    :param predictions: Roboflow 回傳的 predictions list（含 x, y, width, height）
    :param output_path: 畫框後要儲存的圖片路徑（例如 uploads/boxed.jpg）
    :return: output_path
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"❌ 無法讀取圖片：{image_path}")

    height, width = img.shape[:2]

    for i, pred in enumerate(predictions):
        x, y, w, h = int(pred['x']), int(pred['y']), int(pred['width']), int(pred['height'])
        x1, y1 = max(x - w // 2, 0), max(y - h // 2, 0)
        x2, y2 = min(x + w // 2, width), min(y + h // 2, height)

        # 畫綠框
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # 編號（從 1 開始）
        cv2.putText(img, str(i + 1), (x1, max(y1 - 10, 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    cv2.imwrite(output_path, img)
    return output_path
