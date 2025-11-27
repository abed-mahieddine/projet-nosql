from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
import redis
import os
import requests
from datetime import datetime

app = Flask(__name__)

# Connexions aux bases de données
mongo_client = MongoClient(os.getenv('MONGO_URI', 'mongodb://mongo:27017/'))
db = mongo_client.factory_db
sensor_logs = db.sensor_logs

redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'redis'), port=6379, decode_responses=True)

# Liste des équipements surveillés
MACHINES = ['Machine-A1', 'Machine-B2', 'Machine-C3']

# Configuration de l'API météo OpenWeatherMap
OPENWEATHER_API_KEY = 'mettre la clé api ici'
OPENWEATHER_BASE_URL = 'https://api.openweathermap.org/data/2.5/weather'

# Sites géographiques suivis pour la météo
WEATHER_SITES = [
    {'name': 'Paris', 'country': 'FR', 'display_name': 'Paris, France'},
    {'name': 'New York', 'country': 'US', 'display_name': 'New York, USA'},
    {'name': 'Tokyo', 'country': 'JP', 'display_name': 'Tokyo, Japon'}
]

@app.route('/', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        machine_id = request.form.get('machine_id')
        metric_type = request.form.get('metric_type')
        value = float(request.form.get('value'))
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Détermination du statut selon les seuils
        status = "NORMAL"
        if value > 80:
            status = "CRITICAL"
        elif value > 50:
            status = "WARNING"

        # Mise à jour de l'état en temps réel dans Redis
        redis_client.hset(f"machine:{machine_id}", mapping={
            "current_value": value,
            "status": status,
            "last_seen": timestamp,
            "metric": metric_type
        })
        
        if status == "CRITICAL":
            redis_client.incr("global_alerts_count")

        # Enregistrement dans MongoDB pour l'historique
        log_entry = {
            "machine_id": machine_id,
            "metric": metric_type,
            "value": value,
            "status": status,
            "timestamp": timestamp
        }
        sensor_logs.insert_one(log_entry)

        return redirect(url_for('dashboard'))

    # Récupération des données des machines depuis Redis
    machines_data = []
    for m_id in MACHINES:
        data = redis_client.hgetall(f"machine:{m_id}")
        if not data:
            data = {"current_value": 0, "status": "OFFLINE", "last_seen": "Jamais", "metric": "N/A"}
        
        data['id'] = m_id
        machines_data.append(data)

    alert_count = redis_client.get("global_alerts_count")
    if alert_count is None:
        alert_count = 0

    # Récupération de l'historique des machines (exclut les données météo)
    recent_logs = list(sensor_logs.find({"machine_id": {"$exists": True}}).sort('_id', -1).limit(10))

    return render_template('dashboard.html', machines=machines_data, logs=recent_logs, alert_count=alert_count)

@app.route('/weather')
def weather_dashboard():
    """Récupération et affichage des données météorologiques des sites extérieurs"""
    weather_data = []
    
    for site in WEATHER_SITES:
        try:
            # Requête à l'API OpenWeatherMap
            params = {
                'q': f"{site['name']},{site['country']}",
                'appid': OPENWEATHER_API_KEY,
                'units': 'metric',
                'lang': 'fr'
            }
            
            response = requests.get(OPENWEATHER_BASE_URL, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Parsing des données reçues
                temperature = data['main']['temp']
                humidity = data['main']['humidity']
                description = data['weather'][0]['description']
                city_name = data['name']
                feels_like = data['main'].get('feels_like', temperature)
                
                # Sauvegarde dans Redis pour l'état actuel
                site_key = f"weather:{site['name']}"
                redis_client.hset(site_key, mapping={
                    "temperature": temperature,
                    "humidity": humidity,
                    "description": description,
                    "last_update": timestamp,
                    "city": city_name
                })
                
                # Enregistrement dans MongoDB pour l'historique
                weather_log = {
                    "site": site['display_name'],
                    "city": city_name,
                    "temperature": temperature,
                    "humidity": humidity,
                    "description": description,
                    "timestamp": timestamp
                }
                sensor_logs.insert_one(weather_log)
                
                weather_data.append({
                    'display_name': site['display_name'],
                    'city': city_name,
                    'temperature': round(temperature, 1),
                    'feels_like': round(feels_like, 1),
                    'humidity': humidity,
                    'description': description.capitalize(),
                    'status': 'ACTIVE',
                    'last_update': timestamp
                })
            else:
                # Fallback sur les données en cache si l'API échoue
                cached_data = redis_client.hgetall(f"weather:{site['name']}")
                if cached_data:
                    weather_data.append({
                        'display_name': site['display_name'],
                        'city': cached_data.get('city', site['name']),
                        'temperature': round(float(cached_data.get('temperature', 0)), 1),
                        'humidity': int(cached_data.get('humidity', 0)),
                        'description': cached_data.get('description', 'Données non disponibles'),
                        'status': 'CACHED',
                        'last_update': cached_data.get('last_update', 'N/A')
                    })
                else:
                    weather_data.append({
                        'display_name': site['display_name'],
                        'city': site['name'],
                        'temperature': 0,
                        'humidity': 0,
                        'description': 'Données non disponibles',
                        'status': 'ERROR',
                        'last_update': 'N/A'
                    })
        except Exception as e:
            # Récupération depuis le cache en cas d'erreur réseau
            cached_data = redis_client.hgetall(f"weather:{site['name']}")
            if cached_data:
                weather_data.append({
                    'display_name': site['display_name'],
                    'city': cached_data.get('city', site['name']),
                    'temperature': round(float(cached_data.get('temperature', 0)), 1),
                    'humidity': int(cached_data.get('humidity', 0)),
                    'description': cached_data.get('description', 'Données non disponibles'),
                    'status': 'CACHED',
                    'last_update': cached_data.get('last_update', 'N/A')
                })
            else:
                error_msg = "Erreur de connexion"
                if "Connection" in str(e) or "timeout" in str(e).lower():
                    error_msg = "Problème de connexion réseau"
                elif "NameResolution" in str(e) or "DNS" in str(e):
                    error_msg = "Impossible de résoudre le nom de domaine"
                weather_data.append({
                    'display_name': site['display_name'],
                    'city': site['name'],
                    'temperature': 0,
                    'humidity': 0,
                    'description': error_msg,
                    'status': 'ERROR',
                    'last_update': 'N/A'
                })
    
    # Récupération de l'historique météo
    weather_history = list(sensor_logs.find({"site": {"$exists": True}}).sort('_id', -1).limit(15))
    
    return render_template('weather.html', weather_sites=weather_data, history=weather_history)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)