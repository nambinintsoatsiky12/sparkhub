import requests
import datetime
import time

# 🔑 TA CLÉ API PRICEAPI (METODA) - VERSION 2
API_KEY = "SFXOWLHAFMQOTHELWUXNHJUODIONWMPBVDJZAESHRBBUIPWOIKJFYZWALUYZQHTF"
API_BASE = "https://priceapi.metoda.com/v2"

# Webhook vers PythonAnywhere
WEBHOOK_URL = "https://sparkhub001.pythonanywhere.com/webhook-update"
SECRET_TOKEN = "SPARKHUB_SUPER_SECRET_2026"

def scrape_and_send():
    print(f"🔁 Mise à jour auto - {datetime.datetime.now()}")
    
    products = ["airpods", "iphone", "samsung", "ordinateur", "ps5", "montre"]
    all_results = []
    
    for product in products:
        try:
            # ÉTAPE 1 : Créer le job
            job_payload = {
                "topic": "search",
                "q": product,
                "country": "worldwide",
                "limit": 3
            }
            headers = {
                "apikey": API_KEY,
                "Content-Type": "application/json"
            }
            
            job_response = requests.post(
                f"{API_BASE}/jobs",
                json=job_payload,
                headers=headers,
                timeout=10
            )
            job_data = job_response.json()
            job_id = job_data.get('id')
            
            if not job_id:
                print(f"❌ Pas d'ID de job pour {product}")
                continue
            
            # ÉTAPE 2 : Récupérer les résultats
            time.sleep(2)  # Laisser le temps au job de se traiter
            
            results_response = requests.get(
                f"{API_BASE}/jobs/{job_id}",
                headers=headers,
                timeout=10
            )
            data = results_response.json()
            
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
        print("⚠️ Aucun prix récupéré.")

if __name__ == "__main__":
    scrape_and_send()
