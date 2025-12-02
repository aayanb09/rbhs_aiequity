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

def predict_ingredients_gradio(base64_image):
    """Predict ingredients from base64 image using Gradio model"""
    temp_file_path = None
    try:
        print("=" * 50)
        print("CALLING GRADIO MODEL API")
        print(f"Image data length: {len(base64_image)} chars")
        print(f"Image starts with: {base64_image[:50]}")
        
        # FIXED: Remove data URL prefix if present
        if ',' in base64_image and base64_image.startswith('data:'):
            print("Removing data URL prefix...")
            base64_image = base64_image.split(',', 1)[1]
        
        # Additional check for any remaining prefix
        if base64_image.startswith('data:'):
            print("WARNING: Image still has data URL prefix after split!")
            # Force remove everything before comma
            if ',' in base64_image:
                base64_image = base64_image.split(',')[-1]
        
        print(f"Cleaned image data length: {len(base64_image)} chars")
        print(f"Cleaned image starts with: {base64_image[:30]}")
        
        # Decode base64 image and save to temporary file
        try:
            image_data = base64.b64decode(base64_image)
            print(f"Successfully decoded base64 data: {len(image_data)} bytes")
        except Exception as decode_error:
            print(f"Base64 decode error: {decode_error}")
            raise Exception(f"Failed to decode base64 image: {str(decode_error)}")
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_file.write(image_data)
            temp_file_path = temp_file.name
        
        print(f"Temporary file created: {temp_file_path}")
        
        # Verify file was created and has content
        if not os.path.exists(temp_file_path):
            raise Exception("Temporary file was not created")
        
        file_size = os.path.getsize(temp_file_path)
        print(f"Temporary file size: {file_size} bytes")
        
        if file_size == 0:
            raise Exception("Temporary file is empty")
        
        # Get Gradio client
        client = get_gradio_client()
        
        # Call the prediction API
        print("Calling Gradio predict API...")
        result = client.predict(
            image=handle_file(temp_file_path),
            api_name="/predict"
        )
        
        print(f"Gradio API Result: {result}")
        
        # Process results
        predictions = []
        
        # The result format depends on the model output
        # Common formats: dict with 'label' and 'confidences', or list of tuples
        if isinstance(result, dict):
            # Format: {'label': 'apple', 'confidences': [{'label': 'apple', 'confidence': 0.95}, ...]}
            if 'confidences' in result:
                for item in result['confidences'][:5]:  # Top 5
                    clean_name = clean_ingredient_name(item.get('label', ''))
                    predictions.append({
                        'name': clean_name,
                        'value': item.get('confidence', 0),
                        'raw_name': item.get('label', '')
                    })
            elif 'label' in result:
                # Single prediction format
                clean_name = clean_ingredient_name(result['label'])
                predictions.append({
                    'name': clean_name,
                    'value': result.get('confidence', 0.9),  # Default confidence if not provided
                    'raw_name': result['label']
                })
        elif isinstance(result, list):
            # Format: [('apple', 0.95), ('banana', 0.03), ...]
            for item in result[:5]:  # Top 5
                if isinstance(item, tuple) and len(item) >= 2:
                    label, confidence = item[0], item[1]
                    clean_name = clean_ingredient_name(label)
                    predictions.append({
                        'name': clean_name,
                        'value': float(confidence),
                        'raw_name': label
                    })
                elif isinstance(item, dict):
                    clean_name = clean_ingredient_name(item.get('label', ''))
                    predictions.append({
                        'name': clean_name,
                        'value': item.get('score', 0) or item.get('confidence', 0),
                        'raw_name': item.get('label', '')
                    })
        elif isinstance(result, str):
            # Single string result
            clean_name = clean_ingredient_name(result)
            predictions.append({
                'name': clean_name,
                'value': 0.9,  # Default confidence
                'raw_name': result
            })
        
        if not predictions:
            raise Exception(f"No predictions returned from Gradio API. Raw result: {result}")
        
        print("=" * 50)
        print("GRADIO MODEL PREDICTIONS:")
        for i, pred in enumerate(predictions, 1):
            print(f"{i}. {pred['name']}: {pred['value']*100:.2f}%")
        print("=" * 50)
        
        return predictions
        
    except Exception as e:
        print(f"Error in predict_ingredients_gradio: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                print(f"Temporary file deleted: {temp_file_path}")
            except Exception as e:
                print(f"Error deleting temporary file: {e}")

@app.route("/")
def welcome():
    return render_template("welcome.html")

@app.route("/home")
def home():
    return render_template("landing.html")

@app.route("/reminders")
def reminder():
    return render_template("reminders.html")

@app.route("/treatment_info")
def treatment_info():
    return render_template("treatment_info.html")    
    
@app.route('/upload', methods=['GET', 'POST'])
def identify_food():
    if request.method == "POST":
        try:
            # ========== READ multipart/form-data ==========
            if "image" not in request.files:
                return jsonify({'error': 'No image file uploaded'}), 400

            file = request.files["image"]

            # Optional: nutritional needs
            raw_needs = request.form.get("nutritional_needs", "[]")
            try:
                nutritional_needs = json.loads(raw_needs)
            except:
                nutritional_needs = []

            # Convert uploaded image → base64 so your existing code works
            img_bytes = file.read()
            base64_image = base64.b64encode(img_bytes).decode("utf-8")

            print("=" * 50)
            print("Image successfully received via multipart/form-data")
            print(f"Image size: {len(img_bytes)} bytes")
            print("=" * 50)

            # ========== RUN YOUR EXISTING ML PIPELINE ==========
            predictions = predict_ingredients_gradio(base64_image)

            if not predictions:
                return jsonify({'error': 'No ingredients detected'}), 400

            # Top prediction
            top_prediction = predictions[0]
            top_food = top_prediction['name']
            max_confidence = top_prediction['value']

            # ========== GET CALORIE NINJA NUTRITION ==========
            nutrition_data = None
            try:
                if CALORIENINJA_API_KEY:
                    resp = requests.get(
                        f'https://api.calorieninjas.com/v1/nutrition?query={top_food}',
                        headers={'X-Api-Key': CALORIENINJA_API_KEY},
                        timeout=5
                    )
                    if resp.status_code == 200:
                        items = resp.json().get('items', [])
                        if items:
                            nutrition_data = items[0]
            except Exception as e:
                print("CalorieNinja Error:", e)

            # ========== GENERATE GEMINI ADVICE ==========
            gemini_advice = None
            diet_suggestions = None
            try:
                prompt = f"Give nutrition advice for {top_food}."

                model = genai.GenerativeModel("gemini-2.5-flash")
                g_response = model.generate_content(prompt)
                full_response = g_response.text.strip()

                # Try to parse:
                if "ADVICE:" in full_response and "SUGGESTIONS:" in full_response:
                    parts = full_response.split("SUGGESTIONS:")
                    gemini_advice = parts[0].replace("ADVICE:", "").strip()
                    diet_suggestions = parts[1].strip()
                else:
                    gemini_advice = full_response
            except Exception as e:
                print("Gemini error:", e)

            # ========== BUILD FRONTEND RESPONSE ==========
            response_data = {
                'outputs': [
                    {
                        'data': {
                            'concepts': []
                        }
                    }
                ]
            }

            for pred in predictions:
                response_data['outputs'][0]['data']['concepts'].append({
                    'name': pred['name'],
                    'value': pred['value'],
                    'nutrition': nutrition_data if pred == predictions[0] else None,
                    'gemini_advice': gemini_advice if pred == predictions[0] else None,
                    'diet_suggestions': diet_suggestions if pred == predictions[0] else None
                })

            return jsonify(response_data), 200

        except Exception as e:
            print("UPLOAD ERROR:", e)
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
