# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from closed_form_chosencust import optimizationAlgo  # Adjust the import according to your file structure
import os

app = Flask(__name__)
CORS(app)
app.config['ALLOWED_EXTENTIONS'] = {'xlsx', 'xls'}

@app.route('/optimize', methods=['POST'])
def optimize():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        filepath = os.path.join("./chosen_customers.xlsx")
        print('File saved')
        file.save(filepath)
        output = optimizationAlgo()        
        return jsonify({"message": "File uploaded successfully", "data": output}), 200
    

if __name__ == '__main__':
    app.run(debug=True, port=5050)

# Activate your virtual environment
#source venv/bin/activate  # For macOS/Linux
# .\venv\Scripts\activate  # For Windows
# Set the FLASK_APP environment variable
# export FLASK_APP=app.py  # For macOS/Linux
# set FLASK_APP=app.py  # For Windows

# Run the Flask application
# flask run OR python3 app.py

# lsof -i :5050
# kill -9 <PID> 

