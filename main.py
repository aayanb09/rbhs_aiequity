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
            data = request.json
            base64_image = data.get('image')
            
            if not base64_image:
                return jsonify({'error': 'No image provided'}), 400
            
            print("=" * 50)
            print("PROCESSING IMAGE WITH GRADIO MODEL API")
            print(f"Received image data length: {len(base64_image)} chars")
            
            # DEBUG: Check if image has data URL prefix
            if base64_image.startswith('data:'):
                print("WARNING: Image includes data URL prefix in request!")
                print(f"Prefix: {base64_image[:50]}")
            
            print("=" * 50)
            
            # Get predictions from Gradio API
            predictions = predict_ingredients_gradio(base64_image)
            
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
            diet_suggestions = None
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
                            f"\n\nProvide TWO sections:\n"
                            f"1. HEALTH ADVICE (2-3 sentences): Provide practical, actionable advice about whether this food is a good choice for their needs. "
                            f"Be specific about how the nutritional content aligns (or doesn't align) with their requirements. "
                            f"Keep it conversational and supportive\n\n."
                            f"2.DIET SUGGESTIONS (3-4 bullet points): Provide specific, healthy meal ideas "
                            f"Format each suggestion as a brief, practical meal idea. \n"
                            f"Format your response EXACTLY like this:\n"
                            f"ADVICE: [your 2-3 sentence advice here]\n\n"
                            f"SUGGESTIONS:\n"
                            f"• [Suggestion 1]\n"
                            f"• [Suggestion 2]\n"
                            f"• [Suggestion 3]\n"
                            f"• [Suggestion 4]"
                        )
                    else:
                        prompt = (
                            f"You are a nutrition expert. The food identified is {top_food}. "
                            f"Nutritional information: {calories} calories, {protein}g protein, "
                            f"\n\nProvide TWO sections:\n"
                            f"{carbs}g carbohydrates, {fat}g fat, {fiber}g fiber, {sugar}g sugar, {sodium}mg sodium. "
                            f"1. HEALTH ADVICE (2-3 sentences): provide practical, actionable health advice about this food. "
                            f"Is this generally a good nutritional choice? What are the key benefits or concerns? "
                            f"Keep it conversational and supportive.\n\n"
                            f"2. DIET SUGGESTIONS (3-4 bullet points): Provide specific, healthy meal ideas or recipes "
                            f"that incorporate {top_food}. Include cooking methods, portion sizes, and complementary foods. "
                            f"Format each suggestion as a brief, practical meal idea.\n\n"
                            f"Format your response EXACTLY like this:\n"
                            f"ADVICE: [your 2-3 sentence advice here]\n\n"
                            f"SUGGESTIONS:\n"
                            f"• [Suggestion 1]\n"
                            f"• [Suggestion 2]\n"
                            f"• [Suggestion 3]\n"
                            f"• [Suggestion 4]"
                        )                        )
                else:
                    print("No nutrition data - using food name only for Gemini prompt")
                    if nutritional_needs and len(nutritional_needs) > 0:
                        needs_str = ", ".join(nutritional_needs)
                        prompt = (
                            f"You are a nutrition expert and diet coach. The food identified is {top_food}. "
                            f"The person has the following nutritional needs/preferences: {needs_str}. "
                            f"\n\nProvide TWO sections:\n"
                            f"1. HEALTH ADVICE (2-3 sentences): Practical advice about whether this food is generally a good choice for their needs. "
                            f"Focus on general nutritional characteristics of {top_food}. "
                            f"Keep it conversational and supportive.\n\n"
                            f"2. DIET SUGGESTIONS (3-4 bullet points): Provide specific meal ideas that incorporate {top_food} "
                            f"in a healthy way aligned with their needs ({needs_str}). "
                            f"Include cooking methods and complementary foods.\n\n"
                            f"Format your response EXACTLY like this:\n"
                            f"ADVICE: [your 2-3 sentence advice here]\n\n"
                            f"SUGGESTIONS:\n"
                            f"• [Suggestion 1]\n"
                            f"• [Suggestion 2]\n"
                            f"• [Suggestion 3]\n"
                            f"• [Suggestion 4]"
                        )
                    else:
                        prompt = (
                            f"You are a nutrition expert and diet coach. The food identified is {top_food}. "
                            f"\n\nProvide TWO sections:\n"
                            f"1. HEALTH ADVICE (2-3 sentences): Practical health advice about this food. "
                            f"Is this generally a good nutritional choice? What are the key benefits or concerns? "
                            f"Keep it conversational and supportive.\n\n"
                            f"2. DIET SUGGESTIONS (3-4 bullet points): Provide specific, healthy meal ideas "
                            f"that incorporate {top_food}. Include cooking methods and complementary foods.\n\n"
                            f"Format your response EXACTLY like this:\n"
                            f"ADVICE: [your 2-3 sentence advice here]\n\n"
                            f"SUGGESTIONS:\n"
                            f"• [Suggestion 1]\n"
                            f"• [Suggestion 2]\n"
                            f"• [Suggestion 3]\n"
                            f"• [Suggestion 4]"
                        )
                
                print(f"Prompt (first 100 chars): {prompt[:200]}...")
                print("Calling Gemini API NOW...")
                
                model = genai.GenerativeModel("gemini-2.5-flash")
                gemini_response = model.generate_content(prompt)
                
                full_response = gemini_response.text.strip()
                print(f"SUCCESS! Gemini advice received ({len(full_response)} characters)")
                print(f"Response preview: {full_response[:200]}...")
                
                if "ADVICE:" in full_response and "SUGGESTIONS:" in full_response:
                    parts = full_response.split("SUGGESTIONS:")
                    gemini_advice = parts[0].replace("ADVICE:","").strip()
                    diet_suggestions = parts[1].strip()
                    print(f"Parsed advice:{gemini_advice[:100]}...")
                    print(f"Parsed suggestions: {diet_suggestions[100:200]}...")
                else:
                    gemini_advice = full_response
                    die_suggestions=None
                    print("Wrong format")
                
                
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
                    'gemini_advice': gemini_advice if pred == predictions[0] else None,
                    'diet_suggestions': diet_suggestions if pred == predictions[0] else None
                }
                response_data['outputs'][0]['data']['concepts'].append(concept)
            
            print("=" * 50)
            print("RESPONSE DATA STRUCTURE:")
            print(f"Number of concepts: {len(response_data['outputs'][0]['data']['concepts'])}")
            print(f"Top concept has gemini_advice: {bool(response_data['outputs'][0]['data']['concepts'][0].get('gemini_advice'))}")
            print(f"Top concept has diet_suggestions: {bool(response_data['outputs'][0]['data']['concepts'][0].get('diet_suggestions'))}")
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
