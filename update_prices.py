import requests
import datetime
import time
from bs4 import BeautifulSoup
import re

# 🔑 TA CLÉ SCRAPERAPI
SCRAPERAPI_KEY = "f554d91dca9a43b2b06744478422a674"

# Webhook vers PythonAnywhere
WEBHOOK_URL = "https://sparkhub001.pythonanywhere.com/webhook-update"
SECRET_TOKEN = "SPARKHUB_SUPER_SECRET_2026"

def scrape_amazon(product, country="US"):
    """Scraper Amazon via ScraperAPI"""
    try:
        if country == "US":
            url = f"https://www.amazon.com/s?k={product.replace(' ', '+')}"
        elif country == "FR":
            url = f"https://www.amazon.fr/s?k={product.replace(' ', '+')}"
        else:
            url = f"https://www.amazon.com/s?k={product.replace(' ', '+')}"

        scraperapi_url = f"https://api.allorigins.win/raw?url={search_url}"

        response = requests.get(scraperapi_url, timeout=30, proxies={"http": None, "https": None})
        soup = BeautifulSoup(response.text, 'html.parser')

        products = soup.find_all('div', {'data-component-type': 's-search-result'})
        results = []

        for item in products[:3]:
            title_tag = item.find('h2')
            if not title_tag:
                continue
            title = title_tag.text.strip()

            price_tag = item.find('span', class_='a-price-whole')
            if not price_tag:
                continue
            price = price_tag.text.strip()

            results.append({
                'title': title,
                'price': f"{price} USD",
                'source': f"Amazon ({country})"
            })

        return results
    except Exception as e:
        print(f"❌ Erreur Amazon {product}: {e}")
        return []

def scrape_jumia(product):
    """Scraper Jumia Madagascar via ScraperAPI"""
    try:
        url = f"https://www.jumia.mg/catalog/?q={product.replace(' ', '+')}"
        scraperapi_url = f"https://api.scraperapi.com?api_key={SCRAPERAPI_KEY}&url={url}"

        response = requests.get(scraperapi_url, timeout=30, proxies={"http": None, "https": None})
        soup = BeautifulSoup(response.text, 'html.parser')

        products = soup.find_all('article', class_='prd')
        results = []

        for item in products[:3]:
            title_tag = item.find('h3', class_='name')
            price_tag = item.find('div', class_='prc')
            if title_tag and price_tag:
                results.append({
                    'title': title_tag.text.strip(),
                    'price': f"{price_tag.text.strip()} Ar",
                    'source': "Jumia (MG)"
                })

        return results
    except Exception as e:
        print(f"❌ Erreur Jumia {product}: {e}")
        return []

def scrape_and_send():
    print(f"🔁 Mise à jour auto - {datetime.datetime.now()}")

    products = ["airpods", "iphone", "samsung", "ordinateur", "ps5", "montre"]
    all_results = []

    for product in products:
        # Amazon US
        results = scrape_amazon(product, "US")
        for r in results:
            all_results.append({
                "keyword": product,
                "title": r['title'],
                "price": r['price'],
                "source": r['source']
            })
            print(f"✅ {product} (US) -> {r['title'][:30]}")

        # Jumia Madagascar
        results = scrape_jumia(product)
        for r in results:
            all_results.append({
                "keyword": product,
                "title": r['title'],
                "price": r['price'],
                "source": r['source']
            })
            print(f"✅ {product} (MG) -> {r['title'][:30]}")

        time.sleep(2)  # Éviter de surcharger ScraperAPI

    if all_results:
        payload = {"updates": all_results}
        headers = {'X-Update-Token': SECRET_TOKEN, 'Content-Type': 'application/json'}
        response = requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=30)
        print(f"\n📡 Envoi terminé : {response.status_code}")
    else:
        print("\n⚠️ Aucun prix récupéré.")

if __name__ == "__main__":
    scrape_and_send()
