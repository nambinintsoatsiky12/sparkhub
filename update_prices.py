import requests
import datetime
import json

# 🔑 TA CLÉ API PRICEAPI (Metoda)
API_KEY = "SFXOWLHAFMQOTHELWUXNHJUODIONWMPBVDJZAESHRBBUIPWOIKJFYZWALUYZQHTF"

# Essayons plusieurs endpoints (Metoda a changé)
ENDPOINTS = [
    "https://priceapi.metoda.com/v1/prices",
    "https://priceapi.metoda.com/api/v1/prices",
    "https://priceapi.metoda.com/prices",
]

# Webhook vers PythonAnywhere
WEBHOOK_URL = "https://sparkhub001.pythonanywhere.com/webhook-update"
SECRET_TOKEN = "SPARKHUB_SUPER_SECRET_2026"

def test_api_endpoint(product, endpoint):
    """Test un endpoint et retourne les résultats"""
    print(f"🧪 Test avec {endpoint}")
    
    # Méthode 1 : clé dans le header
    headers1 = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    params1 = {"q": product, "country": "worldwide", "limit": 3}
    
    try:
        resp1 = requests.get(endpoint, headers=headers1, params=params1, timeout=10)
        print(f"  Header auth → Code {resp1.status_code}")
        if resp1.status_code == 200:
            return resp1.json(), "header"
    except:
        pass
    
    # Méthode 2 : clé dans l'URL (comme avant)
    params2 = {
        "q": product,
        "country": "worldwide",
        "limit": 3,
        "apikey": API_KEY
    }
    try:
        resp2 = requests.get(endpoint, params=params2, timeout=10)
        print(f"  URL auth → Code {resp2.status_code}")
        if resp2.status_code == 200:
            return resp2.json(), "url"
    except:
        pass
    
    return None, None

def scrape_and_send():
    print(f"🔁 Mise à jour auto - {datetime.datetime.now()}")
    
    products = ["airpods", "iphone", "samsung"]
    all_results = []
    
    # On essaie chaque endpoint jusqu'à ce que ça marche
    for endpoint in ENDPOINTS:
        print(f"\n📡 Tentative avec {endpoint}")
        
        for product in products:
            data, method = test_api_endpoint(product, endpoint)
            if data and 'results' in data:
                print(f"✅ Succès avec {method} sur {endpoint}")
                
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
                
                # Si on a trouvé un endpoint qui fonctionne, on s'arrête
                if all_results:
                    break
            else:
                print(f"❌ Pas de données pour {product} sur {endpoint}")
        
        if all_results:
            break
    
    # Envoi des résultats à PythonAnywhere
    if all_results:
        payload = {"updates": all_results}
        headers = {'X-Update-Token': SECRET_TOKEN, 'Content-Type': 'application/json'}
        try:
            response = requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=30)
            print(f"\n📡 Envoi terminé : {response.status_code}")
        except Exception as e:
            print(f"\n💥 Erreur d'envoi : {e}")
    else:
        print("\n⚠️ Aucun prix récupéré sur aucun endpoint.")

if __name__ == "__main__":
    scrape_and_send()
