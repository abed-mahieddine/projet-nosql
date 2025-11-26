# Projet NoSQL

Application web Flask qui permet de saisir des données via un formulaire et de les stocker dans MongoDB et Redis.

## Description

Le projet simule un système de supervision industrielle. Les données saisies sont enregistrées dans deux bases NoSQL :
- MongoDB pour garder l'historique complet
- Redis pour l'état en temps réel

## Installation

### Prérequis
- Docker et Docker Compose
- Git

### Lancement

1. Cloner le repo
```bash
git clone <url-du-repo>
cd projet_no-sql
```

2. Lancer avec docker compose
```bash
docker compose up
```

3. Ouvrir dans le navigateur
```
http://localhost:5000
```

## Utilisation

### Générer des données

Ouvrir le navigateur sur `http://localhost:5000`. Vous devriez voir l'interface "Supervision Industrielle".

Dans le formulaire "Saisie de données", faire un test avec une valeur critique :
- **Équipement** : Machine-A1
- **Type de mesure** : Température
- **Valeur mesurée** : 95 (valeur > 80, donc statut CRITICAL)

Cliquer sur "Enregistrer la mesure".

Résultat attendu : La carte Machine-A1 passe au rouge et une nouvelle ligne apparaît dans le tableau "Historique des mesures".

### Vérifier la persistance

Ouvrir deux terminaux pour vérifier que les données sont bien stockées dans les deux systèmes.

#### Redis (état temps réel)

Dans le premier terminal :
```bash
docker exec -it nosql_redis redis-cli HGETALL machine:Machine-A1
```

Vous devriez voir les champs avec `current_value` à "95" et `status` à "CRITICAL".

Pour voir le compteur d'alertes :
```bash
docker exec -it nosql_redis redis-cli GET global_alerts_count
```

#### MongoDB (historique)

Dans le second terminal :
```bash
docker exec -it nosql_mongo mongosh factory_db --eval "db.sensor_logs.find().sort({_id:-1}).limit(1)"
```

Vous devriez voir un document JSON avec `machine_id: "Machine-A1"`, `value: 95` et `status: "CRITICAL"`.

Si vous obtenez ces résultats, la persistance fonctionne correctement dans les deux bases.

## Architecture

3 containers Docker :
- web : app Flask sur le port 5000
- mongo : MongoDB sur le port 27017
- redis : Redis sur le port 6379

## Structure

```
projet_no-sql/
├── app/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── static/
│   │   └── css/
│   │       └── style.css
│   └── templates/
│       ├── base.html
│       └── dashboard.html
├── docker-compose.yml
└── README.md
```

## Technologies

- Python 3.9, Flask
- MongoDB, Redis
- HTML/CSS
- Docker

## Notes

- Les données sont sauvegardées dans les deux bases à chaque soumission
- MongoDB garde tout l'historique
- Redis stocke seulement la dernière valeur de chaque machine
- Le statut est calculé automatiquement :
  - > 80 : CRITICAL
  - > 50 : WARNING
  - sinon : NORMAL

## Arrêt

```bash
docker compose down
```

Pour supprimer aussi les volumes :
```bash
docker compose down -v
```
