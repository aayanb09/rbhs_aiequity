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
                top_items = [c for c in concepts if abs(c['value'] - max_confidence) < 0.001]  # Float comparison tolerance
                
                print(f"Top confidence: {max_confidence}")
                print(f"Items with top confidence: {[item['name'] for item in top_items]}")
                
                # Pick the best one from ties
                # Priority: more specific names (longer, more descriptive)
                # Avoid generic terms like "food", "dish", "meal"
                generic_terms = ['food', 'dish', 'meal', 'plate', 'cuisine']
                
                best_item = None
                for item in top_items:
                    name = item['name'].lower()
                    # Skip generic terms
                    if any(term in name for term in generic_terms):
                        continue
                    # Prefer longer, more specific names
                    if best_item is None or len(name) > len(best_item['name']):
                        best_item = item
                
                # If all were generic, just use the first one
                if best_item is None:
                    best_item = top_items[0]
                
                top_food = best_item['name']
                print(f"Selected top food: {top_food}")
                
                # ALWAYS try to generate Gemini advice
                try:
                    print("=" * 50)
                    print("ATTEMPTING GEMINI API CALL")
                    print(f"Food name: {top_food}")
                    
                    # Extract nutrition info for Gemini
                    nutrition = best_item.get('nutrition', {})
                    print(f"Nutrition data available: {bool(nutrition)}")
                    if nutrition:
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
                        
                        print(f"Prompt: {prompt[:100]}...")
                        print("Calling Gemini API...")
                
                        model = genai.GenerativeModel("gemini-1.5-flash")
                        gemini_response = model.generate_content(prompt)
                
                        advice = gemini_response.text.strip()
                        print(f"Gemini advice received: {advice}")
                        print("=" * 50)
                
                        # Add Gemini output to the top food concept
                        for i, concept in enumerate(clarifai_data['outputs'][0]['data']['concepts']):
                            if concept['name'] == top_food:
                                concept['gemini_advice'] = advice
                                print(f"Added gemini_advice to concept at index {i}")
                                break
                    else:
                        print("No nutrition data - using food name only for Gemini prompt")
                        prompt = (
                            f"You are a nutrition expert. The food identified is {top_food}. "
                            f"In 2-3 sentences, provide practical health advice about this food for someone "
                            f"managing their diet and blood sugar. Focus on general nutritional benefits and any tips. "
                            f"Keep it conversational and supportive."
                        )
                        
                        print(f"Prompt: {prompt[:100]}...")
                        print("Calling Gemini API...")
                        
                        model = genai.GenerativeModel("gemini-1.5-flash")
                        gemini_response = model.generate_content(prompt)
                        advice = gemini_response.text.strip()
                        
                        print(f"Gemini advice received: {advice}")
                        print("=" * 50)
                        
                        for i, concept in enumerate(clarifai_data['outputs'][0]['data']['concepts']):
                            if concept['name'] == top_food:
                                concept['gemini_advice'] = advice
                                print(f"Added gemini_advice to concept at index {i}")
                                break
                
                except Exception as gemini_error:
                    print("Gemini error:", gemini_error)
                    import traceback
                    traceback.print_exc()
                    # Don't add advice if there was an error
                    
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
