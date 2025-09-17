# app/utils/prediction.py
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
import numpy as np
import cv2

try:
    model = load_model("model_Tes2.h5")
    print("Model loaded successfully.")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

# Informasi Class
class_names = ['Tomato___Tomato_Yellow_Leaf_Curl_Virus', 'Tomato___healthy']
readable_labels = ['Infected (TYLCV)', 'Healthy']
colors = ['red', 'green']

def predict_image(image_path):
    if model is None:
        return {"label": "Model not loaded.", "color": "black", "confidence": 0}
    try:
        image = cv2.imread(image_path)
        if image is None:
            return {"label": "Invalid image file.", "color": "black", "confidence": 0}

        image_resized = cv2.resize(image, (224, 224))
        image_array = img_to_array(image_resized)
        image_array_expanded = np.expand_dims(image_array, axis=0)
        image_normalized = image_array_expanded / 255.0

        predictions = model.predict(image_normalized)[0]
        predicted_index = np.argmax(predictions)
        confidence = float(predictions[predicted_index])

        predicted_label_str = readable_labels[predicted_index]
        predicted_color = colors[predicted_index]

        return {
            "label": predicted_label_str,
            "color": predicted_color,
            "confidence": confidence
        }
    except Exception as e:
        print("Prediction error:", str(e))
        return {"label": "Prediction failed.", "color": "black", "confidence": 0}