from flask import Flask, request, jsonify
from pymongo import MongoClient
from flask_cors import CORS  
import numpy as np
import cv2
import os
from tensorflow.keras.applications.vgg16 import VGG16, preprocess_input
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.image import img_to_array
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
CORS(app)

BASE_PATH = "C:/Users/HP/OneDrive/Desktop/Full Stack/Virtual Shopping Assistant/backend"

# Load VGG16 model
model = VGG16(weights='imagenet', include_top=False)
model = Model(inputs=model.input, outputs=model.output)

def get_products():
    uri = "mongodb+srv://aarthiraju23527:ZsbNPkGfqEacY37S@cluster.mgghd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster"
    client = MongoClient(uri)
    
    db = client.get_database("test")  # Selecting the database
    collection = db["products"]  # Selecting the collection
    
    products = list(collection.find({}, {"_id": 1, "productOwner": 1, "productName": 1, "description": 1, "category": 1, "style": 1, "quantity": 1, "price": 1, "productImage": 1}))
    
    # Convert ObjectId to string
    for product in products:
        product["_id"] = str(product["_id"])
    
    client.close()
    return products

def load_images(image_paths):
    image_data = []
    image_full_paths = []
    
    for rel_path in image_paths:
        full_path = os.path.join(BASE_PATH, rel_path.lstrip("/"))
        if os.path.exists(full_path):
            img = cv2.imread(full_path)
            if img is not None:
                img = cv2.resize(img, (224, 224))  # Resize to match VGG16 input size
                image_data.append(img)
                image_full_paths.append(rel_path)
    
    return np.array(image_data), np.array(image_full_paths)

def extract_features(images):
    images = preprocess_input(images)  # Normalize images for VGG16
    features = model.predict(images)
    return features.reshape(features.shape[0], -1)  # Flatten feature vectors

def find_similar_images(query_img, products, image_features):
    query_img = cv2.resize(query_img, (224, 224))
    query_img = preprocess_input(np.expand_dims(img_to_array(query_img), axis=0))
    query_feature = model.predict(query_img).flatten().reshape(1, -1)
    
    image_paths = np.array([p["productImage"] for p in products])
    similarities = cosine_similarity(query_feature, image_features)[0]
    top_indices = np.argsort(similarities)[::-1][:20]  # Get top 20 matches
    
    similar_products = [products[i] for i in top_indices] if top_indices.size > 0 else []
    
    # Convert ObjectId to string in response
    for product in similar_products:
        product["_id"] = str(product["_id"])
    
    return similar_products

@app.route("/find_similar", methods=["POST"])
def find_similar():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    
    file_path = os.path.join(BASE_PATH, "temp_query.jpg")
    file.save(file_path)
    
    query_img = cv2.imread(file_path)
    if query_img is None:
        return jsonify({"error": "Invalid image file"}), 400
    
    products = get_products()
    image_paths = [p["productImage"] for p in products]
    images_array, full_paths_array = load_images(image_paths)
    image_features = extract_features(images_array)
    
    similar_products = find_similar_images(query_img, products, image_features)
    
    return jsonify({"similar_products": similar_products})

if __name__ == "__main__":
    app.run(debug=True)
