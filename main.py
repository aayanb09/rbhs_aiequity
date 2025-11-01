from flask import Flask, render_template, request, redirect, url_for, flash
import os
import base64
import requests

app = Flask(__name__)
app.secret_key = "password" 

CLARIFAI_KEY = os.environ.get("CLARIFAI_KEY")
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"

@app.route("/")
def welcome():
    return render_template("welcome.html")

@app.route("/home")
def home():
    return render_template("landing.html", test_value=test_value)

@app.route("/reminders")
def reminder():
    return render_template("reminders.html")

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        # 1. Get the image
        image_file = request.files.get("image")
        if not image_file:
            return jsonify({"error": "No image uploaded"}), 400
        image_bytes = image_file.read()
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        # 2. Get selected nutritional goals
        goals = request.form.getlist("goals")  # JS sends goals[] via FormData

        # 3. Call Clarifai API for ingredient recognition
        try:
            ingredients = call_clarifai_api(image_base64)
        except Exception as e:
            return jsonify({"error": f"Clarifai API error: {e}"}), 500

        # 4. Call Gemini API for analysis
        try:
            analysis = call_gemini_api(ingredients, goals)
        except Exception as e:
            return jsonify({"error": f"Gemini API error: {e}"}), 500

        # 5. Return JSON to JS
        return jsonify({
            "ingredients": ingredients,
            "analysis": analysis
        })

    # GET → render the upload page
    return render_template("upload.html")
    
def call_clarifai_api(image_base64):
    """
    Calls Clarifai's general model to recognize food ingredients.
    """
    url = "https://api.clarifai.com/v2/models/food-item-recognition/outputs"
    headers = {
        "Authorization": f"Key {CLARIFAI_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "inputs": [
            {
                "data": {
                    "image": {
                        "base64": image_base64
                    }
                }
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    results = response.json()
    # Extract ingredient names
    ingredients = []
    concepts = results["outputs"][0]["data"].get("concepts", [])
    for concept in concepts:
        ingredients.append(concept["name"])
    return ingredients

def call_gemini_api(ingredients, goals):
    """
    Calls Google Gemini API to generate analysis of how ingredients align
    with the user's selected dietary goals.
    """
    prompt = (
        f"You are a nutrition expert. The user has selected the following dietary goals: {', '.join(goals)}. "
        f"The ingredients in the food they uploaded are: {', '.join(ingredients)}. "
        "Provide a clear analysis of how well these ingredients align with the selected goals, "
        "and give any helpful suggestions."
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    headers = {
        "x-goog-api-key": GEMINI_API_KEY,
        "Content-Type": "application/json"
    }
    body = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    response = requests.post(url, headers=headers, json=body)
    response.raise_for_status()
    result = response.json()

    # The text is usually in outputs[0].content
    return result["outputs"][0]["content"].strip()

@app.route("/symptomTracker")
def symptom():
    return render_template("symptomReport.html")

@app.route("/glucose")
def glucose():
    return render_template("glucose.html")

@app.route("/settings")
def settings():
    return render_template("settings.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
