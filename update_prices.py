import requests
import datetime

WEBHOOK_URL = "https://sparkhub001.pythonanywhere.com/webhook-update"
SECRET_TOKEN = "SPARKHUB_SUPER_SECRET_2026"

def send_fallback_prices():
    print("🔄 Envoi des prix de secours à PythonAnywhere...")
    
    # Prix de secours (ce sont des données réalistes, mais "fixes" pour l'instant)
    fallback_data = [
        {"keyword": "riz", "title": "Riz local (1kg)", "price": "2 500 Ar", "source": "Marché Tana"},
        {"keyword": "riz", "title": "Riz importé (1kg)", "price": "3 200 Ar", "source": "Marché Tana"},
        {"keyword": "huile", "title": "Huile de table (1L)", "price": "8 500 Ar", "source": "Grands magasins"},
        {"keyword": "sucre", "title": "Sucre (1kg)", "price": "4 200 Ar", "source": "Marché local"},
        {"keyword": "essence", "title": "Essence (Super)", "price": "6 500 Ar/L", "source": "Station Total"},
        {"keyword": "airpods", "title": "AirPods Pro (2ème gén)", "price": "1 200 000 Ar", "source": "Apple Store"},
        {"keyword": "iphone", "title": "iPhone 15 Pro (128Go)", "price": "5 200 000 Ar", "source": "Amazon DE"},
        {"keyword": "ordinateur", "title": "PC Portable Dell XPS 13", "price": "7 100 000 Ar", "source": "Dell France"},
    ]
    
    # Envoyer les données
    try:
        payload = {"updates": fallback_data}
        headers = {
            'X-Update-Token': SECRET_TOKEN,
            'Content-Type': 'application/json'
        }
        response = requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=30)
        print(f"📡 Code HTTP : {response.status_code}")
        print(f"📡 Réponse : {response.text}")
        if response.status_code == 200:
            print("✅ Les prix de secours ont été envoyés avec succès !")
        else:
            print("💥 Échec de l'envoi.")
    except Exception as e:
        print(f"💥 Erreur de connexion : {e}")

if __name__ == "__main__":
    send_fallback_prices()
