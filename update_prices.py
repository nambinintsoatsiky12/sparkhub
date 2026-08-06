import requests
import datetime

# 🔑 TA CLÉ API PRICEAPI (Metoda) - IDENTIQUE À flask_app.py
API_KEY = "SFXOWLHAFMQOTHELWUXNHJUODIONWMPBVDJZAESHRBBUIPWOIKJFYZWALUYZQHTF"
API_URL = "https://priceapi.metoda.com/v1/prices"

# Webhook vers PythonAnywhere
WEBHOOK_URL = "https://sparkhub001.pythonanywhere.com/webhook-update"
SECRET_TOKEN = "SPARKHUB_SUPER_SECRET_2026"

def scrape_and_send():
    print(f"🔁 Mise à jour auto - {datetime.datetime.now()}")
    
    products = ["airpods", "iphone", "samsung", "ordinateur", "ps5", "montre"]
    all_results = []
    
    for product in products:
        try:
            # ✅ CORRECTION ICI : la clé dans les paramètres URL (comme dans flask_app.py)
            params = {
                "q": product,
                "country": "worldwide",
                "limit": 3,
                "apikey": API_KEY  # <-- C'EST LA BONNE LIGNE
            }
            headers = {"Content-Type": "application/json"}
            
            response = requests.get(API_URL, headers=headers, params=params, timeout=10)
            data = response.json()
            
            for item in data.get('results', []):
                title = item.get('title', 'Produit')
                price = item.get('price', 'N/A')
                currency = item.get('currency', 'USD')
                source = item.get('source', 'PriceAPI')
                
                all_results.append({
                    "keyword": product,
                    "title": title,
                    "price": f"{price} {currency}",
                    "source": f"{source} (Auto)"
                })
                print(f"✅ {product} -> {title}")
        except Exception as e:
            print(f"❌ Erreur {product}: {e}")
    
    if all_results:
        payload = {"updates": all_results}
        headers = {'X-Update-Token': SECRET_TOKEN, 'Content-Type': 'application/json'}
        response = requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=30)
        print(f"📡 Envoi terminé : {response.status_code}")
    else:
        print("⚠️ Aucun prix récupéré, rien à envoyer.")

if __name__ == "__main__":
    scrape_and_send()
