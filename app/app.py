from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
import redis
import os
from datetime import datetime

app = Flask(__name__)

# Connexions DB
mongo_client = MongoClient(os.getenv('MONGO_URI', 'mongodb://mongo:27017/'))
db = mongo_client.factory_db
sensor_logs = db.sensor_logs

redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'redis'), port=6379, decode_responses=True)

# Machines à surveiller
MACHINES = ['Machine-A1', 'Machine-B2', 'Machine-C3']

@app.route('/', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        machine_id = request.form.get('machine_id')
        metric_type = request.form.get('metric_type')
        value = float(request.form.get('value'))
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Calcul du statut
        status = "NORMAL"
        if value > 80:
            status = "CRITICAL"
        elif value > 50:
            status = "WARNING"

        # Redis pour l'état actuel
        redis_client.hset(f"machine:{machine_id}", mapping={
            "current_value": value,
            "status": status,
            "last_seen": timestamp,
            "metric": metric_type
        })
        
        if status == "CRITICAL":
            redis_client.incr("global_alerts_count")

        # MongoDB pour l'historique
        log_entry = {
            "machine_id": machine_id,
            "metric": metric_type,
            "value": value,
            "status": status,
            "timestamp": timestamp
        }
        sensor_logs.insert_one(log_entry)

        return redirect(url_for('dashboard'))

    # Récup des données pour l'affichage
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

    recent_logs = list(sensor_logs.find().sort('_id', -1).limit(10))

    return render_template('dashboard.html', machines=machines_data, logs=recent_logs, alert_count=alert_count)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)