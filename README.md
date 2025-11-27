# Projet NoSQL - Supervision Industrielle

Application web Flask de supervision industrielle avec intégration de données météorologiques en temps réel. Le système utilise MongoDB pour l'historique et Redis pour l'état actuel des équipements.

## Description

Ce projet simule un système de supervision industrielle permettant de :
- Surveiller l'état des équipements industriels (température, pression)
- Suivre les conditions météorologiques de sites géographiques distants
- Stocker l'historique dans MongoDB
- Maintenir l'état en temps réel dans Redis

## Fonctionnalités

### Dashboard Machines
- Visualisation en temps réel de l'état des équipements
- Saisie manuelle de mesures (température ou pression)
- Calcul automatique du statut (NORMAL, WARNING, CRITICAL)
- Historique des mesures avec filtrage automatique

### Dashboard Météo
- Données météorologiques en temps réel pour 3 villes (Paris, New York, Tokyo)
- Température, humidité et conditions météo
- Température ressentie
- Historique des données météo
- Fallback sur cache en cas d'indisponibilité de l'API

## Installation

### Prérequis
- Docker et Docker Compose
- Git
- Clé API OpenWeatherMap (gratuite sur [openweathermap.org](https://openweathermap.org/api))

### Configuration

1. Cloner le repository
```bash
git clone <url-du-repo>
cd projet_no-sql
```

2. Configurer la clé API OpenWeatherMap

Éditer `app/app.py` et remplacer la clé API :
```python
OPENWEATHER_API_KEY = 'votre_cle_api_ici'
```

3. Lancer l'application
```bash
docker compose up
```

4. Accéder à l'interface
```
http://localhost:5000
```

## Utilisation

### Dashboard Machines

1. Accéder à la page principale (`http://localhost:5000`)
2. Dans le formulaire "Saisie de données", saisir :
   - **Équipement** : Machine-A1, Machine-B2 ou Machine-C3
   - **Type de mesure** : Température (°C) ou Pression (Bar)
   - **Valeur mesurée** : une valeur numérique
3. Cliquer sur "Enregistrer la mesure"

Le statut est calculé automatiquement :
- Valeur > 80 : **CRITICAL** (rouge)
- Valeur > 50 : **WARNING** (orange)
- Sinon : **NORMAL** (vert)

### Dashboard Météo

1. Cliquer sur l'onglet "Météo" dans la navigation
2. Les données sont récupérées automatiquement depuis l'API OpenWeatherMap
3. Cliquer sur "Actualiser les données" pour mettre à jour

Les données affichées :
- Température actuelle
- Température ressentie
- Humidité relative
- Conditions météorologiques
- Historique des dernières mesures

## Vérification de la persistance

### Redis (état temps réel)

Vérifier l'état d'une machine :
```bash
docker exec -it nosql_redis redis-cli HGETALL machine:Machine-A1
```

Vérifier le compteur d'alertes :
```bash
docker exec -it nosql_redis redis-cli GET global_alerts_count
```

Vérifier les données météo en cache :
```bash
docker exec -it nosql_redis redis-cli HGETALL weather:Paris
```

### MongoDB (historique)

Voir les dernières mesures machines :
```bash
docker exec -it nosql_mongo mongosh factory_db --eval "db.sensor_logs.find({machine_id: {\$exists: true}}).sort({_id:-1}).limit(5)"
```

Voir les dernières données météo :
```bash
docker exec -it nosql_mongo mongosh factory_db --eval "db.sensor_logs.find({site: {\$exists: true}}).sort({_id:-1}).limit(5)"
```

## Architecture

Le projet utilise 3 containers Docker :
- **web** : Application Flask sur le port 5000
- **mongo** : MongoDB sur le port 27017
- **redis** : Redis sur le port 6379

### Stockage des données

- **MongoDB** : Stocke tout l'historique (machines + météo)
  - Collection `sensor_logs` pour toutes les données
  - Filtrage par `machine_id` ou `site` selon le contexte

- **Redis** : Stocke uniquement l'état actuel
  - Clés `machine:{id}` pour les équipements
  - Clés `weather:{ville}` pour les données météo
  - Compteur `global_alerts_count` pour les alertes critiques

## Structure du projet

```
projet_no-sql/
├── app/
│   ├── app.py                 # Application Flask principale
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── static/
│   │   └── css/
│   │       └── style.css      # Styles de l'interface
│   └── templates/
│       ├── base.html          # Template de base
│       ├── dashboard.html    # Dashboard machines
│       └── weather.html       # Dashboard météo
├── docker-compose.yml
└── README.md
```

## Technologies utilisées

- **Backend** : Python 3.9, Flask
- **Bases de données** : MongoDB, Redis
- **API externe** : OpenWeatherMap API
- **Frontend** : HTML/CSS, Font Awesome
- **Containerisation** : Docker, Docker Compose

## Notes importantes

- Les données machines et météo sont stockées dans la même collection MongoDB mais filtrées selon le contexte
- En cas d'indisponibilité de l'API météo, le système utilise les données en cache Redis
- Les seuils de statut peuvent être modifiés dans `app.py` (lignes 47-51)
- La clé API OpenWeatherMap peut nécessiter 10-15 minutes d'activation après création

## Arrêt de l'application

```bash
docker compose down
```

Pour supprimer aussi les volumes (données) :
```bash
docker compose down -v
```
