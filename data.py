import http.client
import json
import os
import requests
from pymongo import MongoClient

# MongoDB Connection
client = MongoClient("mongodb+srv://aarthiraju23527:ZsbNPkGfqEacY37S@cluster.mgghd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster")  
db = client["test"]  # Your database name
collection = db["products"]  # Your collection name

# Base Uploads Directory
UPLOADS_DIR = "uploads/men"

def search_images(query, api_key, num_images=100):
    conn = http.client.HTTPSConnection("google.serper.dev")
    payload = json.dumps({"q": query, "gl": "in"})
    headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
    
    conn.request("POST", "/images", payload, headers)  # Correct API endpoint
    res = conn.getresponse()
    data = res.read()
    conn.close()
    
    try:
        results = json.loads(data.decode("utf-8"))
        image_urls = [img['imageUrl'] for img in results.get('images', [])][:50]

        print(f"Found {len(image_urls)} images for '{query}'")
        return image_urls
    except json.JSONDecodeError:
        print(f"Error decoding JSON response for '{query}'. API response: {data.decode('utf-8')}")
        return []

def is_valid_url(url):
    """Check if URL is accessible"""
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

def download_images(image_urls, category):
    folder = os.path.join(UPLOADS_DIR, category)  # Save to 'uploads/women/{category}'
    
    # Replace backslashes with forward slashes
    folder = folder.replace("\\", "/")
    
    if not os.path.exists(folder):
        os.makedirs(folder)

    for i, url in enumerate(image_urls):
        if not is_valid_url(url):
            print(f"Skipping invalid URL: {url}")
            continue

        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                image_path = os.path.join(folder, f"image_{i+1}.jpg")
                
                # Replace backslashes with forward slashes in image path
                image_path = image_path.replace("\\", "/")
                
                with open(image_path, "wb") as file:
                    for chunk in response.iter_content(1024):
                        file.write(chunk)
                
                print(f"Downloaded: {image_path}")

                # Store image metadata in MongoDB
                collection.insert_one({
                    "productOwner": "67ea2c0ed591edc2c43d2683",
                    "productName": "Mens Wear",
                    "description": "trending on the styles",
                    "category": "men",
                    "style": category,
                    "quantity": 5,
                    "price": 1800,
                    "productImage": "/"+image_path
                })
                print(f"Inserted into MongoDB: {image_path}")

            else:
                print(f"Failed to download {url} - Status Code: {response.status_code}")
        except Exception as e:
            print(f"Error downloading {url}: {e}")

if __name__ == "__main__":
    api_key = "0ef811f768869961392796cc4aebe1ce2f9cc825"
    categories = ["menFormals", "menHoodies", "menPants", "menTies", "menShoes", "menShorts"]

    for category in categories:
        print(f"Searching images for: {category}")
        image_urls = search_images(category, api_key)

        if not image_urls:
            print(f"No images found for '{category}'")
            continue

        download_images(image_urls, category)

    print("Download complete!")
