import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__))) # DON'T CHANGE THIS !!!

from flask import Flask, request, jsonify, render_template
# from src.routes.analysis import analysis_bp # Will create this blueprint later

app = Flask(__name__, static_folder='static', template_folder='static')

# Uncomment the following line if you need to use mysql, do not modify the SQLALCHEMY_DATABASE_URI configuration
# app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USERNAME', 'root')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME', 'mydb')}"

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/api/analyze', methods=['POST'])
def analyze_properties():
    data = request.get_json()
    email = data.get('email')
    location = data.get('location')
    property_type = data.get('propertyType')
    min_price = data.get('minPrice')
    max_price = data.get('maxPrice')
    min_beds = data.get('minBeds')
    max_beds = data.get('maxBeds')
    keywords = data.get('keywords')

    # Placeholder for actual analysis logic
    print(f"Received analysis request: {data}")

    # Simulate processing and results
    mock_results = [
        {
            "title": "Placeholder: Charming Fixer-Upper",
            "price": "€120,000",
            "description": "Needs work, great potential. Location: {location if location else 'Any'}",
            "url": "#placeholder1"
        },
        {
            "title": "Placeholder: Modern Apartment",
            "price": "€280,000",
            "description": "2 Bed, City Centre. Type: {property_type if property_type else 'Any'}",
            "url": "#placeholder2"
        }
    ]

    message = "Analysis complete! (Placeholder data)."
    if email:
        message += f" Email notification would be sent to {email}."
        # Placeholder for email sending logic
        # send_email(email, "Property Analysis Results", f"Your analysis is complete. Results: {mock_results}")
        print(f"Email sending to {email} would happen here.")

    return jsonify({"message": message, "results": mock_results})

# app.register_blueprint(analysis_bp, url_prefix='/api') # Will register blueprint later

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
