import requests
import datetime

BUYWHERE_API_KEY = "bw_1c9d31d53fe04975b2448ed6cd87450d"  # <-- Ta clé ici

WEBHOOK_URL = "https://sparkhub001.pythonanywhere.com/webhook-update"
SECRET_TOKEN = "SPARKHUB_SUPER_SECRET_2026"

def scrape_and_send():
    print(f"🔁 Mise à jour auto - {datetime.datetime.now()}")
    
    products = ["airpods", "iphone", "samsung", "ordinateur", "ps5", "montre"]
    all_results = []
    
    for product in products:
        try:
            url = "https://api.buywhere.ai/v1/search"
            headers = {
                "Authorization": f"Bearer {BUYWHERE_API_KEY}",
                "Content-Type": "application/json"
            }
            params = {"q": product, "country": "worldwide", "limit": 3}
            response = requests.get(url, headers=headers, params=params, timeout=10)
            data = response.json()
            
            for item in data.get('results', []):
                title = item.get('title', 'Produit')
                price = item.get('price', 'N/A')
                currency = item.get('currency', 'USD')
                source = item.get('source', 'BuyWhere')
                
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

if __name__ == "__main__":
    scrape_and_send()
