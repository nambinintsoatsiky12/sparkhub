import requests
import datetime
import time
import json

# 🔑 TA CLÉ API
API_KEY = "SFXOWLHAFMQOTHELWUXNHJUODIONWMPBVDJZAESHRBBUIPWOIKJFYZWALUYZQHTF"
API_BASE = "https://priceapi.metoda.com/v2"

WEBHOOK_URL = "https://sparkhub001.pythonanywhere.com/webhook-update"
SECRET_TOKEN = "SPARKHUB_SUPER_SECRET_2026"

def scrape_and_send():
    print(f"🔁 Mise à jour auto - {datetime.datetime.now()}")
    
    products = ["airpods", "iphone", "samsung", "ordinateur", "ps5", "montre"]
    all_results = []
    
    for product in products:
        try:
            # ✅ ICI LA CORRECTION : la clé s'appelle "token"
            params = {
                "token": API_KEY,  # <-- PARAMÈTRE "token" EXIGÉ PAR METODA
                "topic": "search",
                "q": product,
                "country": "worldwide",
                "limit": 3
            }
            headers = {"Content-Type": "application/json"}
            
            # Créer le job avec la clé dans l'URL
            job_response = requests.post(
                f"{API_BASE}/jobs",
                params=params,
                headers=headers,
                timeout=10
            )
            
            if job_response.status_code != 200:
                print(f"❌ Erreur job {product}: {job_response.status_code} - {job_response.text}")
                continue
                
            job_data = job_response.json()
            job_id = job_data.get('id')
            
            if not job_id:
                print(f"❌ Pas d'ID pour {product}: {job_data}")
                continue
            
            print(f"✅ Job créé pour {product} (ID: {job_id})")
            
            # Attendre que le job soit traité
            time.sleep(3)
            
            # Récupérer les résultats
            results_response = requests.get(
                f"{API_BASE}/jobs/{job_id}",
                params={"token": API_KEY},  # token aussi ici
                headers=headers,
                timeout=10
            )
            
            if results_response.status_code != 200:
                print(f"❌ Erreur récupération {product}: {results_response.status_code}")
                continue
                
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
                print(f"  ✅ {product} -> {title}")
                
        except Exception as e:
            print(f"❌ Exception {product}: {e}")
    
    if all_results:
        payload = {"updates": all_results}
        headers = {'X-Update-Token': SECRET_TOKEN, 'Content-Type': 'application/json'}
        response = requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=30)
        print(f"📡 Envoi terminé : {response.status_code}")
    else:
        print("⚠️ Aucun prix récupéré.")

if __name__ == "__main__":
    scrape_and_send()
