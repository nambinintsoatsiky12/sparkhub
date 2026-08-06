import requests
from bs4 import BeautifulSoup
import datetime
import json

# ⚠️ Adresse de ton site (l'endroit où on va envoyer les prix)
WEBHOOK_URL = "https://sparkhub001.pythonanywhere.com/webhook-update"
SECRET_TOKEN = "SPARKHUB_SUPER_SECRET_2026"

def scrape_and_send():
    print(f"🔁 Début du scraping - {datetime.datetime.now()}")
    
    # Liste des produits à scraper
    products = ["riz", "huile", "sucre", "airpods", "iphone", "ordinateur"]
    all_results = []
    
    for product in products:
        try:
            url = f"https://www.jumia.mg/catalog/?q={product.replace(' ', '+')}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            articles = soup.find_all('article', class_='prd')[:2]
            for article in articles:
                title_tag = article.find('h3', class_='name')
                price_tag = article.find('div', class_='prc')
                if title_tag and price_tag:
                    title = title_tag.text.strip()
                    price = price_tag.text.strip() + " Ar"
                    all_results.append({
                        "keyword": product,
                        "title": title,
                        "price": price,
                        "source": "Jumia (GitHub Auto)"
                    })
                    print(f"✅ {product} -> {title} : {price}")
        except Exception as e:
            print(f"❌ Erreur pour {product} : {e}")
    
    # 2. Envoyer tous les résultats à PythonAnywhere
    if all_results:
        try:
            payload = {"updates": all_results}
            headers = {
                'X-Update-Token': SECRET_TOKEN,
                'Content-Type': 'application/json'
            }
            print(f"📡 Envoi de {len(all_results)} produits vers {WEBHOOK_URL}")
            response = requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=30)
            print(f"📡 Code HTTP : {response.status_code}")
            print(f"📡 Réponse : {response.text}")
            
            if response.status_code == 200:
                print("✅ Données envoyées avec succès !")
            else:
                print("💥 Échec de l'envoi, vérifie le token ou l'URL.")
        except Exception as e:
            print(f"💥 Erreur de connexion : {e}")
    else:
        print("⚠️ Aucun prix récupéré, rien à envoyer.")

if __name__ == "__main__":
    scrape_and_send()
