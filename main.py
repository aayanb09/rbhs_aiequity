from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os
import base64
import io
import requests
import google.generativeai as genai
from PIL import Image
from gradio_client import Client, handle_file
import tempfile

app = Flask(__name__)
app.secret_key = "password" 

# Set up API keys
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
CALORIENINJA_API_KEY = os.environ.get("CALORIENINJA_API_KEY")

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize Gradio client
GRADIO_CLIENT = None

def get_gradio_client():
    """Lazy initialization of Gradio client"""
    global GRADIO_CLIENT
    if GRADIO_CLIENT is None:
        try:
            print("Initializing Gradio client for fredsok/ingredientsmodel...")
            GRADIO_CLIENT = Client("fredsok/ingredientsmodel")
            print("✓ Gradio client initialized successfully")
        except Exception as e:
            print(f"Error initializing Gradio client: {e}")
            raise
    return GRADIO_CLIENT

# ============== HELPER FUNCTIONS ==============

def clean_ingredient_name(name):
    """Clean up ingredient name for display"""
    # Remove parentheses content and underscores
    name = name.split('_(')[0]  # Remove (meat), (fish), etc.
    name = name.replace('_', ' ')
    return name.title()
def predict_ingredients_inference_api(base64_image):
    """Predict ingredients using Hugging Face Inference API (router endpoint)."""
    HF_API_KEY = os.environ.get("HF_API_KEY")
    if not HF_API_KEY:
        raise Exception("HF_API_KEY not set in environment variables")

    # NEW updated endpoint:
    url = "https://router.huggingface.co/hf-inference/models/fredsok/ingredientsmodel"

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": base64_image
    }

    response = requests.post(url, headers=headers, json=payload, timeout=20)

    if response.status_code != 200:
        raise Exception(f"Hugging Face API Error {response.status_code}: {response.text}")

    result = response.json()

    predictions = []
    if isinstance(result, list):
        for item in result[:5]:
            predictions.append({
                "name": clean_ingredient_name(item["label"]),
                "value": float(item["score"]),
                "raw_name": item["label"]
            })

    elif isinstance(result, dict) and "label" in result:
        predictions.append({
            "name": clean_ingredient_name(result["label"]),
            "value": result.get("score", 0.9),
            "raw_name": result["label"]
        })

    if not predictions:
        raise Exception(f"No predictions returned from HF API. Raw response: {result}")

    return predictions

@app.route("/")
def welcome():
    return render_template("welcome.html")

@app.route("/home")
def home():
    return render_template("landing.html")

@app.route("/reminders")
def reminder():
    return render_template("reminders.html")
    
    
@app.route('/upload', methods=['GET', 'POST'])
def identify_food():
    if request.method == "POST":
        try:
            data = request.json
            base64_image = data.get('image')
            
            if not base64_image:
                return jsonify({'error': 'No image provided'}), 400
            
            print("=" * 50)
            print("PROCESSING IMAGE WITH GRADIO MODEL API")
            print(f"Image data length: {len(base64_image)} chars")
            print("=" * 50)
            
            # Get predictions from Gradio API
            predictions = predict_ingredients_inference_api(base64_image)
            
            if not predictions or len(predictions) == 0:
                return jsonify({'error': 'No ingredients detected in the image'}), 400
            
            # Get the top prediction
            top_prediction = predictions[0]
            top_food = top_prediction['name']
            max_confidence = top_prediction['value']
            
            print(f"Top prediction: {top_food} ({max_confidence*100:.2f}%)")
            
            # Try to get nutrition from CalorieNinja API
            nutrition_data = None
            try:
                if CALORIENINJA_API_KEY:
                    print(f"Fetching nutrition data from CalorieNinja for: {top_food}")
                    
                    calorieninja_response = requests.get(
                        f'https://api.calorieninjas.com/v1/nutrition?query={top_food}',
                        headers={'X-Api-Key': CALORIENINJA_API_KEY},
                        timeout=5
                    )
                    
                    print(f"CalorieNinja Response Status: {calorieninja_response.status_code}")
                    
                    if calorieninja_response.status_code == 200:
                        ninja_data = calorieninja_response.json()
                        print(f"CalorieNinja JSON: {ninja_data}")
                        
                        if ninja_data and ninja_data.get('items') and len(ninja_data['items']) > 0:
                            item = ninja_data['items'][0]
                            nutrition_data = {
                                'calories': item.get('calories', 0),
                                'protein_g': item.get('protein_g', 0),
                                'carbohydrates_total_g': item.get('carbohydrates_total_g', 0),
                                'fat_total_g': item.get('fat_total_g', 0),
                                'fiber_g': item.get('fiber_g', 0),
                                'sugar_g': item.get('sugar_g', 0),
                                'sodium_mg': item.get('sodium_mg', 0),
                                'serving_size_g': item.get('serving_size_g', 100)
                            }
                            print(f"✓ CalorieNinja data retrieved: {nutrition_data}")
                        else:
                            print("CalorieNinja returned empty or invalid data")
                    else:
                        print(f"CalorieNinja API error: {calorieninja_response.status_code}")
                else:
                    print("CalorieNinja API key not set")
            except Exception as ninja_error:
                print(f"CalorieNinja error: {ninja_error}")
                import traceback
                traceback.print_exc()
            
            # Generate Gemini advice
            gemini_advice = None
            try:
                print("=" * 50)
                print("ATTEMPTING GEMINI API CALL")
                print(f"Food name: {top_food}")
                print(f"Google API Key exists: {bool(GOOGLE_API_KEY)}")
                
                if not GOOGLE_API_KEY:
                    print("ERROR: GOOGLE_API_KEY is not set!")
                    raise Exception("Missing Google API Key")
                
                # Get nutritional needs from request data
                nutritional_needs = data.get('nutritional_needs', [])
                print(f"Nutritional needs: {nutritional_needs}")
                
                # Build prompt based on nutritional needs and available data
                if nutrition_data and isinstance(nutrition_data, dict):
                    print("Using nutrition data for Gemini prompt")
                    calories = nutrition_data.get('calories', 'unknown')
                    protein = nutrition_data.get('protein_g', 'unknown')
                    fat = nutrition_data.get('fat_total_g', 'unknown')
                    sugar = nutrition_data.get('sugar_g', 'unknown')
                    fiber = nutrition_data.get('fiber_g', 'unknown')
                    sodium = nutrition_data.get('sodium_mg', 'unknown')
                    carbs = nutrition_data.get('carbohydrates_total_g', 'unknown')
            
                    if nutritional_needs and len(nutritional_needs) > 0:
                        needs_str = ", ".join(nutritional_needs)
                        prompt = (
                            f"You are a nutrition expert. The food identified is {top_food}. "
                            f"Nutritional information: {calories} calories, {protein}g protein, "
                            f"{carbs}g carbohydrates, {fat}g fat, {fiber}g fiber, {sugar}g sugar, {sodium}mg sodium. "
                            f"The person has the following nutritional needs/preferences: {needs_str}. "
                            f"In 2-3 sentences, provide practical, actionable advice about whether this food is a good choice for their needs. "
                            f"Be specific about how the nutritional content aligns (or doesn't align) with their requirements. "
                            f"Keep it conversational and supportive."
                        )
                    else:
                        prompt = (
                            f"You are a nutrition expert. The food identified is {top_food}. "
                            f"Nutritional information: {calories} calories, {protein}g protein, "
                            f"{carbs}g carbohydrates, {fat}g fat, {fiber}g fiber, {sugar}g sugar, {sodium}mg sodium. "
                            f"In 2-3 sentences, provide practical, actionable health advice about this food. "
                            f"Is this generally a good nutritional choice? What are the key benefits or concerns? "
                            f"Keep it conversational and supportive."
                        )
                else:
                    print("No nutrition data - using food name only for Gemini prompt")
                    if nutritional_needs and len(nutritional_needs) > 0:
                        needs_str = ", ".join(nutritional_needs)
                        prompt = (
                            f"You are a nutrition expert. The food identified is {top_food}. "
                            f"The person has the following nutritional needs/preferences: {needs_str}. "
                            f"In 2-3 sentences, provide practical advice about whether this food is generally a good choice for their needs. "
                            f"Focus on general nutritional characteristics of {top_food}. "
                            f"Keep it conversational and supportive."
                        )
                    else:
                        prompt = (
                            f"You are a nutrition expert. The food identified is {top_food}. "
                            f"In 2-3 sentences, provide practical health advice about this food. "
                            f"Is this generally a good nutritional choice? What are the key benefits or concerns? "
                            f"Keep it conversational and supportive."
                        )
                
                print(f"Prompt (first 100 chars): {prompt[:100]}...")
                print("Calling Gemini API NOW...")
                
                model = genai.GenerativeModel("gemini-2.5-flash")
                gemini_response = model.generate_content(prompt)
                
                gemini_advice = gemini_response.text.strip()
                print(f"SUCCESS! Gemini advice received ({len(gemini_advice)} characters)")
                print(f"Advice preview: {gemini_advice[:100]}...")
                print("=" * 50)
                
            except Exception as gemini_error:
                print("=" * 50)
                print(f"GEMINI ERROR: {str(gemini_error)}")
                print("Error type:", type(gemini_error).__name__)
                import traceback
                traceback.print_exc()
                print("=" * 50)
            
            # Build response in Clarifai format for compatibility with frontend
            response_data = {
                'outputs': [
                    {
                        'data': {
                            'concepts': []
                        }
                    }
                ]
            }
            
            # Add all predictions as concepts
            for pred in predictions:
                concept = {
                    'name': pred['name'],
                    'value': pred['value'],
                    'nutrition': nutrition_data if pred == predictions[0] else None,
                    'gemini_advice': gemini_advice if pred == predictions[0] else None
                }
                response_data['outputs'][0]['data']['concepts'].append(concept)
            
            print("=" * 50)
            print("RESPONSE DATA STRUCTURE:")
            print(f"Number of concepts: {len(response_data['outputs'][0]['data']['concepts'])}")
            print(f"Top concept has gemini_advice: {bool(response_data['outputs'][0]['data']['concepts'][0].get('gemini_advice'))}")
            print("=" * 50)
            
            return jsonify(response_data), 200
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
            
    return render_template("upload.html")


@app.route("/symptomTracker")
def symptom():
    return render_template("symptomReport.html")

@app.route("/glucose")
def glucose():
    return render_template("glucose.html")

@app.route("/settings")
def settings():
    return render_template("settings.html")

@app.route("/test-gemini")
def test_gemini():
    """Test endpoint to verify Gemini is working"""
    try:
        if not GOOGLE_API_KEY:
            return jsonify({'error': 'GOOGLE_API_KEY not set'}), 500
        
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content("Say hello in one sentence")
        
        return jsonify({
            'success': True,
            'message': 'Gemini is working!',
            'response': response.text
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route("/test-gradio")
def test_gradio():
    """Test endpoint to verify Gradio API is working"""
    try:
        client = get_gradio_client()
        
        return jsonify({
            'success': True,
            'message': 'Gradio client initialized successfully',
            'model': 'fredsok/ingredientsmodel'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
