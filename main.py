from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os
import base64
import requests
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = "password" 

# Set up API keys
CLARIFAI_PAT = os.environ.get("CLARIFAI_PAT")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
CALORIENINJA_API_KEY = os.environ.get("CALORIENINJA_API_KEY")

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)

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
            print("SENDING REQUEST TO CLARIFAI")
            print(f"API Key (first 10 chars): {CLARIFAI_PAT[:10]}...")
            print(f"Image data length: {len(base64_image)} chars")
            print("=" * 50)
            
            # Call Clarifai API
            clarifai_response = requests.post(
                'https://api.clarifai.com/v2/models/food-item-v1-recognition/outputs',
                headers={
                    'Accept': 'application/json',
                    'Authorization': f'Key {CLARIFAI_PAT}',
                    'Content-Type': 'application/json'
                },
                json={
                    "user_app_id": {
                        "user_id": "clarifai",
                        "app_id": "main"
                    },
                    "inputs": [
                        {
                            "data": {
                                "image": {
                                    "base64": base64_image
                                }
                            }
                        }
                    ]
                }
            )
            
            print(f"Clarifai Response status: {clarifai_response.status_code}")
            
            if clarifai_response.status_code != 200:
                return jsonify(clarifai_response.json()), clarifai_response.status_code
            
            clarifai_data = clarifai_response.json()
            
            # Get concepts
            if (clarifai_data.get('outputs') and 
                len(clarifai_data['outputs']) > 0 and 
                clarifai_data['outputs'][0].get('data') and 
                clarifai_data['outputs'][0]['data'].get('concepts') and
                len(clarifai_data['outputs'][0]['data']['concepts']) > 0):
                
                concepts = clarifai_data['outputs'][0]['data']['concepts']
                
                # Find the highest confidence
                max_confidence = concepts[0]['value']
                
                # Get all items with the same top confidence (handle ties)
                top_items = [c for c in concepts if abs(c['value'] - max_confidence) < 0.001]
                
                print(f"Top confidence: {max_confidence}")
                print(f"Items with top confidence: {[item['name'] for item in top_items]}")
                
                # Pick the best one from ties
                generic_terms = ['food', 'dish', 'meal', 'plate', 'cuisine']
                
                best_item = None
                for item in top_items:
                    name = item['name'].lower()
                    if any(term in name for term in generic_terms):
                        continue
                    if best_item is None or len(name) > len(best_item['name']):
                        best_item = item
                
                if best_item is None:
                    best_item = top_items[0]
                
                top_food = best_item['name']
                print(f"Selected top food: {top_food}")
                
                # Try to get nutrition from CalorieNinja API first
                nutrition_data = None
                try:
                    if CALORIENINJA_API_KEY:
                        print(f"Fetching nutrition data from CalorieNinja for: {top_food}")
                        print(f"CalorieNinja API Key exists: {bool(CALORIENINJA_API_KEY)}")
                        print(f"CalorieNinja API Key (first 10 chars): {CALORIENINJA_API_KEY[:10]}...")
                        
                        calorieninja_response = requests.get(
                            f'https://api.calorieninjas.com/v1/nutrition?query={top_food}',
                            headers={'X-Api-Key': CALORIENINJA_API_KEY},
                            timeout=5
                        )
                        
                        print(f"CalorieNinja Response Status: {calorieninja_response.status_code}")
                        print(f"CalorieNinja Response: {calorieninja_response.text[:200]}...")
                        
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
                                best_item['nutrition'] = nutrition_data
                            else:
                                print("CalorieNinja returned empty or invalid data")
                                print(f"Items in response: {ninja_data.get('items') if ninja_data else 'None'}")
                        else:
                            print(f"CalorieNinja API error: {calorieninja_response.status_code}")
                            print(f"Error response: {calorieninja_response.text}")
                    else:
                        print("CalorieNinja API key not set, using Clarifai nutrition data if available")
                except Exception as ninja_error:
                    print(f"CalorieNinja error: {ninja_error}")
                    print(f"Error type: {type(ninja_error).__name__}")
                    import traceback
                    traceback.print_exc()
                
                # If no CalorieNinja data, try to use Clarifai nutrition
                if not nutrition_data:
                    nutrition_data = best_item.get('nutrition', {})
                
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
                    
                    nutrition = nutrition_data
                    print(f"Nutrition data available: {bool(nutrition)}")
                    
                    # Build prompt
                    if nutrition and isinstance(nutrition, dict) and nutrition:
                        print("Using nutrition data for Gemini prompt")
                        calories = nutrition.get('calories', 'unknown')
                        protein = nutrition.get('protein_g', 'unknown')
                        fat = nutrition.get('fat_total_g', 'unknown')
                        sugar = nutrition.get('sugar_g', 'unknown')
                        fiber = nutrition.get('fiber_g', 'unknown')
                        sodium = nutrition.get('sodium_mg', 'unknown')
                        carbs = nutrition.get('carbohydrates_total_g', 'unknown')
                
                        prompt = (
                            f"You are a nutrition expert. The food identified is {top_food}. "
                            f"Nutritional information: {calories} calories, {protein}g protein, "
                            f"{carbs}g carbohydrates, {fat}g fat, {fiber}g fiber, {sugar}g sugar, {sodium}mg sodium. "
                            f"In 2-3 sentences, provide practical, actionable health advice about this food. "
                            f"Focus on: (1) whether it's a good choice for someone managing blood sugar, "
                            f"(2) any specific health benefits or concerns, and (3) a simple tip for healthy consumption. "
                            f"Keep it conversational and supportive."
                        )
                    else:
                        print("No nutrition data - using food name only for Gemini prompt")
                        prompt = (
                            f"You are a nutrition expert. The food identified is {top_food}. "
                            f"In 2-3 sentences, provide practical health advice about this food for someone "
                            f"managing their diet and blood sugar. Focus on general nutritional benefits and any tips. "
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
                
                # Add Gemini advice to the top concept
                if gemini_advice:
                    print(f"Adding gemini_advice to concepts...")
                    print(f"Looking for concept with name: '{top_food}'")
                    print(f"Available concepts: {[c['name'] for c in clarifai_data['outputs'][0]['data']['concepts']]}")
                    
                    concept_found = False
                    for i, concept in enumerate(clarifai_data['outputs'][0]['data']['concepts']):
                        print(f"Checking concept {i}: '{concept['name']}' vs '{top_food}'")
                        if concept['name'] == top_food:
                            concept['gemini_advice'] = gemini_advice
                            print(f"✓ Successfully added gemini_advice to concept index {i} ('{concept['name']}')")
                            print(f"Verifying: concept now has gemini_advice = {concept.get('gemini_advice')[:50]}...")
                            concept_found = True
                            break
                    
                    if not concept_found:
                        print(f"WARNING: Could not find concept with name '{top_food}' to add advice to")
                        print("Adding to first concept instead as fallback")
                        clarifai_data['outputs'][0]['data']['concepts'][0]['gemini_advice'] = gemini_advice
                else:
                    print("WARNING: No gemini_advice to add (it's None or empty)")
                    
            print("=" * 50)
            return jsonify(clarifai_data), 200
            
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
