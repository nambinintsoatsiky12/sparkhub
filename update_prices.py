import requests
import datetime
import json

API_KEY = "SFXOWLHAFMQOTHELWUXNHJUODIONWMPBVDJZAESHRBBUIPWOIKJFYZWALUYZQHTF"
API_BASE = "https://priceapi.metoda.com/v2"

WEBHOOK_URL = "https://sparkhub001.pythonanywhere.com/webhook-update"
SECRET_TOKEN = "SPARKHUB_SUPER_SECRET_2026"

def test_job_creation(product):
    """Tente de créer un job et affiche la réponse brute"""
    print(f"\n🧪 Test avec {product}")
    
    # Méthode 1 : clé dans le header
    headers1 = {
        "apikey": API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "topic": "search",
        "q": product,
        "country": "worldwide",
        "limit": 3
    }
    
    try:
        # Tentative avec header
        resp = requests.post(f"{API_BASE}/jobs", json=payload, headers=headers1, timeout=10)
        print(f"  → Header auth : statut {resp.status_code}")
        print(f"  → Réponse brute : {resp.text[:200]}")  # Affiche les 200 premiers caractères
        
        if resp.status_code == 200:
            data = resp.json()
            job_id = data.get('id')
            if job_id:
                print(f"  ✅ Job créé avec ID : {job_id}")
                return job_id
            else:
                print(f"  ❌ Pas d'ID dans la réponse : {data}")
        else:
            print(f"  ❌ Erreur HTTP {resp.status_code}")
    except Exception as e:
        print(f"  ❌ Exception : {e}")
    
    # Méthode 2 : clé dans l'URL (paramètre)
    try:
        params = {
            "apikey": API_KEY,
            "topic": "search",
            "q": product,
            "country": "worldwide",
            "limit": 3
        }
        resp = requests.post(f"{API_BASE}/jobs", params=params, timeout=10)
        print(f"  → URL auth : statut {resp.status_code}")
        print(f"  → Réponse brute : {resp.text[:200]}")
        
        if resp.status_code == 200:
            data = resp.json()
            job_id = data.get('id')
            if job_id:
                print(f"  ✅ Job créé avec ID : {job_id}")
                return job_id
    except Exception as e:
        print(f"  ❌ Exception : {e}")
    
    return None

def scrape_and_send():
    print(f"🔁 Mise à jour auto - {datetime.datetime.now()}")
    
    products = ["airpods", "iphone"]
    all_results = []
    
    for product in products:
        job_id = test_job_creation(product)
        if not job_id:
            continue
        
        # Si on a un job, on récupère les résultats
        try:
            headers = {"apikey": API_KEY}
            time.sleep(2)  # Attendre que le job soit traité
            resp = requests.get(f"{API_BASE}/jobs/{job_id}", headers=headers, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
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
            else:
                print(f"  ❌ Erreur récupération job {job_id} : {resp.status_code}")
        except Exception as e:
            print(f"  ❌ Exception récupération : {e}")
    
    if all_results:
        payload = {"updates": all_results}
        headers = {'X-Update-Token': SECRET_TOKEN, 'Content-Type': 'application/json'}
        response = requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=30)
        print(f"\n📡 Envoi terminé : {response.status_code}")
    else:
        print("\n⚠️ Aucun prix récupéré.")

if __name__ == "__main__":
    scrape_and_send()
