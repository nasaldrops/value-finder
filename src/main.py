import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__))) # DON'T CHANGE THIS !!!

from flask import Flask, request, jsonify, render_template
from src.lib.daft_analyzer import fetch_daft_listings, analyze_listings # Import the new functions

app = Flask(__name__, static_folder='static', template_folder='static')

# Uncomment the following line if you need to use mysql, do not modify the SQLALCHEMY_DATABASE_URI configuration
# app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USERNAME', 'root')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME', 'mydb')}"

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/api/analyze', methods=['POST'])
def analyze_properties_route(): # Renamed to avoid conflict with imported function if any
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request", "details": "No JSON data received"}), 400

    print(f"[main.py] Received API request data: {data}")

    # Extract filters for the daft_analyzer module
    filters = {
        "location": data.get("location"),
        "propertyType": data.get("propertyType"),
        "minPrice": data.get("minPrice"),
        "maxPrice": data.get("maxPrice"),
        "minBeds": data.get("minBeds"),
        "maxBeds": data.get("maxBeds"),
        # Keywords from the form will be passed to analyze_listings
    }
    user_keywords_str = data.get("keywords", "")

    # Step 1: Fetch listings using daft_analyzer
    print(f"[main.py] Calling fetch_daft_listings with filters: {filters}")
    fetched_data = fetch_daft_listings(filters)

    if isinstance(fetched_data, dict) and 'error' in fetched_data:
        print(f"[main.py] Error from fetch_daft_listings: {fetched_data['error']}")
        return jsonify(fetched_data), 500 # Propagate error to frontend
    
    if not fetched_data:
        print("[main.py] No listings fetched or an empty list was returned.")
        return jsonify({"message": "No properties found matching your criteria from Daft.ie.", "results": []})

    # Step 2: Analyze the fetched listings
    print(f"[main.py] Calling analyze_listings for {len(fetched_data)} listings. User keywords: '{user_keywords_str}'")
    analyzed_results = analyze_listings(fetched_data, user_keywords_str)
    
    if isinstance(analyzed_results, dict) and 'error' in analyzed_results: # Should not happen if fetch was ok
        print(f"[main.py] Error from analyze_listings: {analyzed_results['error']}")
        return jsonify(analyzed_results), 500

    message = f"Analysis complete. Found and analyzed {len(analyzed_results)} properties."
    email = data.get('email')
    if email:
        message += f" If this were live, an email notification would be sent to {email}."
        # Placeholder for actual email sending logic
        # send_email(email, "Property Analysis Results", f"Your analysis is complete. Results: {analyzed_results}")
        print(f"[main.py] Email sending to {email} would happen here with actual results.")

    print(f"[main.py] Sending response to frontend. Message: {message}, Results count: {len(analyzed_results)}")
    return jsonify({"message": message, "results": analyzed_results})

if __name__ == '__main__':
    # Ensure the venv is active and daft-scraper is installed: 
    # source venv/bin/activate
    # pip install -r requirements.txt
    app.run(host='0.0.0.0', port=5000, debug=True)
