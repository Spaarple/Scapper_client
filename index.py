from flask import Flask, jsonify, request, render_template
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

app = Flask(__name__)

# URL de l'API Sirene Open Data
SIRENE_API_URL = "https://api.insee.fr/entreprises/sirene/V3.11/siret"

# Obtenir la clé API depuis les variables d'environnement
API_KEY = os.getenv("SIRENE_API_KEY")
CHATGPT_API_KEY = os.getenv("CHATGPT_API_KEY")

def fetch_companies_for_date(date):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    params = {
        'q': f'dateCreationUniteLegale:{date}',
        'date': date,
        'masquerValeursNulles': 'true',
        'nombre': 300
    }
    response = requests.get(SIRENE_API_URL, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json().get('etablissements', [])
    else:
        return []

@app.route('/new_companies', methods=['GET'])
def get_new_companies():
    days = int(request.args.get('days', 30))

    end_date = datetime.today()
    start_date = end_date - timedelta(days=days)
    
    all_companies = []
    
    for single_date in (start_date + timedelta(n) for n in range(days)):
        date_str = single_date.strftime('%Y-%m-%d')
        companies = fetch_companies_for_date(date_str)
        all_companies.extend(companies)
    
    return jsonify(all_companies)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_email', methods=['POST'])
def generate_email():
    data = request.json
    company_name = data.get('company_name')
    activity = data.get('activity')
    
    prompt = f"Create a professional email introducing the new company {company_name}, which is specialized in {activity}."
    
    headers = {
        'Authorization': f'Bearer {CHATGPT_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(
        'https://api.openai.com/v1/engines/davinci-codex/completions',
        headers=headers,
        json={
            'prompt': prompt,
            'max_tokens': 150
        }
    )
    
    email_content = response.json().get('choices')[0].get('text').strip()
    
    return jsonify({'email': email_content})

if __name__ == '__main__':
    app.run(debug=True)
