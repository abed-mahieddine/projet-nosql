# Projet NoSQL

Application web Flask pour la supervision d'équipements industriels avec données météo. Utilise MongoDB pour l'historique et Redis pour le temps réel.

## Description

Ce projet simule un système de supervision industrielle (Dashboard IoT) permettant de :
- Surveiller l'état des équipements industriels (température, pression)
- Suivre les conditions météorologiques de sites géographiques distants
- Stocker l'historique dans MongoDB
- Maintenir l'état en temps réel dans Redis

### Concept IoT

Le système simule des capteurs qui envoient des données (température, humidité, pression, alertes). Ces données sont affichées sur un dashboard en temps réel.

**Pourquoi Redis ?**
- Alertes en temps réel 
- Dernières valeurs "live" pour un affichage instantané
- Structure hash pour accès rapide
- Compteur d'alertes global

**Pourquoi MongoDB ?**
- Historique complet de toutes les mesures
- Permet de faire des graphiques sur le mois dernier
- Structure flexible pour différents capteurs
- Requêtes pour l'analyse temporelle

## Fonctionnalités

### Dashboard Machines
- Visualisation temps réel des équipements
- Saisie manuelle de mesures (température ou pression)
- Calcul du statut (NORMAL, WARNING, CRITICAL)
- Historique des mesures

### Dashboard Météo
- Données météo pour 3 villes (Paris, New York, Tokyo)
- Température, humidité, conditions
- Température ressentie
- Historique
- Utilise le cache si l'API est down

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

2. Configurer la clé API 

Copier `.env.example` en `.env` :
```bash
cp .env.example .env
```

Éditer `.env` et mettre votre clé API OpenWeatherMap. Si pas de clé, le dashboard météo ne fonctionnera pas mais le reste marche.

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

1. Aller sur `http://localhost:5000`
2. Remplir le formulaire :
   - Équipement : Machine-A1, Machine-B2 ou Machine-C3
   - Type : Température ou Pression
   - Valeur : un nombre
3. Cliquer sur "Enregistrer la mesure"

Le statut se calcule tout seul :
- > 80 : CRITICAL (rouge)
- > 50 : WARNING (orange)
- Sinon : NORMAL (vert)

### Dashboard Météo

1. Cliquer sur "Météo" dans le menu
2. Les données se récupèrent depuis l'API OpenWeatherMap
3. Actualiser pour mettre à jour

Affiche : température, température ressentie, humidité, conditions, historique

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
- **mongo** : MongoDB sur le port 27017 (avec healthcheck)
- **redis** : Redis sur le port 6379 (avec healthcheck)

Les healthchecks garantissent que les services sont prêts avant le démarrage de l'application web.

### Stockage des données

Architecture avec deux bases pour optimiser selon l'usage :

- **MongoDB** : Historique complet (machines + météo)
  - Collection `sensor_logs`
  - Filtrage par `machine_id` ou `site`
  - Pour les graphiques et analyses

- **Redis** : État actuel uniquement
  - Clés `machine:{id}` pour les équipements
  - Clés `weather:{ville}` pour la météo
  - Compteur `global_alerts_count` pour les alertes
  - Accès rapide pour le dashboard temps réel

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
├── .env.example               # Template de configuration
├── .env                       # Fichier de configuration (créé à partir de .env.example)
└── README.md
```

## Technologies utilisées

- **Backend** : Python 3.9, Flask
- **Bases de données** : MongoDB, Redis
- **API externe** : OpenWeatherMap API
- **Frontend** : HTML/CSS, Font Awesome
- **Containerisation** : Docker, Docker Compose

## Notes

- Données machines et météo dans la même collection MongoDB, filtrées selon le contexte
- Si l'API météo est down, utilise le cache Redis
- Seuils modifiables dans `app.py` (lignes 40-44)
- La clé API OpenWeatherMap peut prendre 10-15 min à s'activer

## Arrêt de l'application

```bash
docker compose down
```

Pour supprimer aussi les volumes (données) :
```bash
docker compose down -v
```
