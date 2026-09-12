# Mettre SparkHub en ligne — guide simple

Ce guide explique exactement quoi remplir. Tu n'as besoin que de GitHub, Render et ta clé ScraperAPI.

## 1. Les trois clés expliquées

### `SCRAPERAPI_KEY` — obligatoire pour les vrais prix
C'est la clé que tu possèdes déjà. Elle permet à Scout de demander des pages de produits à ScraperAPI.

### `SPARKHUB_SECRET_KEY` — obligatoire pour sécuriser les sessions
Ce n'est pas une clé à acheter. Render peut la créer automatiquement avec `render.yaml`. En local, tu peux mettre n'importe quelle longue phrase aléatoire, par exemple :

```text
SPARKHUB_SECRET_KEY=SparkHub-une-phrase-longue-et-secrete-2026
```

### `SPARKHUB_WEBHOOK_TOKEN` — optionnel pour l'instant
Il protège la route `/webhook-update`. Tu peux laisser Render la générer automatiquement. Tu n'as rien à utiliser dans le site pour le moment.

Ne publie jamais ces trois valeurs dans un dépôt GitHub public.

## 2. Mise en ligne automatique avec Render

1. Va sur **render.com** et connecte-toi avec GitHub.
2. Clique sur **New +**, puis **Blueprint**.
3. Choisis le dépôt `sparkhub` et la branche `arena/01a094cc-sparkhub`.
4. Render lit automatiquement `render.yaml`.
5. Quand Render affiche les variables, ouvre `SCRAPERAPI_KEY` et colle ta clé ScraperAPI.
6. Clique sur **Apply**.
7. Attends la fin du déploiement. Render donnera une adresse du type `https://sparkhub-xxxx.onrender.com`.

Les deux autres variables sont générées automatiquement :
- `SPARKHUB_SECRET_KEY` ;
- `SPARKHUB_WEBHOOK_TOKEN`.

## 3. Si tu crées le service Render manuellement

Choisis :

- **Runtime** : Python 3
- **Build Command** : `pip install -r requirements.txt`
- **Start Command** : `gunicorn app:app`
- **Plan** : Free

Puis ajoute ces variables dans **Settings > Environment** :

| Nom | Valeur |
|---|---|
| `SCRAPERAPI_KEY` | ta clé ScraperAPI |
| `SPARKHUB_SECRET_KEY` | une phrase secrète longue |
| `SPARKHUB_WEBHOOK_TOKEN` | une autre phrase secrète |

## 4. Tester après le déploiement

Ouvre ces adresses en remplaçant `TON-URL` :

```text
https://TON-URL.onrender.com/
https://TON-URL.onrender.com/scout?query=iphone&country=US
https://TON-URL.onrender.com/api/scout?query=iphone&country=US
```

La première visite peut prendre 30 à 60 secondes : le service gratuit Render était probablement en veille.

## 5. Test en local (facultatif)

Dans un terminal, depuis le dossier du projet :

```bash
python -m venv .venv
source .venv/bin/activate       # macOS / Linux
# .venv\\Scripts\\activate    # Windows
pip install -r requirements.txt
cp .env.example .env            # macOS / Linux
python app.py
```

Ensuite visite `http://localhost:5000`.

Dans `.env`, remplace seulement :

```text
SCRAPERAPI_KEY=ta-vraie-cle
```

Le fichier `.env` est ignoré par Git et ne sera pas publié.

## 6. Ce qu'il faut savoir sur la base de données

La version actuelle utilise SQLite. C'est suffisant pour démarrer et tester, mais le disque du service Render gratuit n'est pas une base de données permanente garantie. Les annonces et comptes peuvent donc être perdus après un redéploiement ou un nettoyage.

Avant d'avoir de vrais utilisateurs, il faudra connecter SparkHub à une base PostgreSQL gratuite, par exemple Neon ou Supabase. Cette étape n'est pas nécessaire pour lancer le prototype.

## 7. À propos du réveil automatique

Un service Render gratuit s'endort après une période sans trafic. C'est normal. La première requête suivante le réveille.

Ne configure pas encore de système de ping automatique : cela consomme des ressources et n'est pas nécessaire pour tester le produit. Nous pourrons ajouter un GitHub Action de réveil si le projet a besoin d'être disponible en permanence.
