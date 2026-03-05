import os
import asyncio
import requests
from bs4 import BeautifulSoup
from mistralai import Mistral
from telegram import Bot

# --- CONFIGURATION ---
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")

client = Mistral(api_key=MISTRAL_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)

def scanner_jooble():
    """Aspire les offres de sous-traitance et missions BTP via Jooble"""
    print("🎯 Recherche sur Jooble (Sous-traitance BTP)...")
    url = 'https://fr.jooble.org/SearchResult?ukw=g%C3%A9nie%20civil%20sous-traitance'
    opportunites = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        # On cherche les blocs d'offres (sélecteur simplifié pour la robustesse)
        articles = soup.find_all('article')[:2]
        for art in articles:
            link = art.find('a')
            if link:
                opportunites.append({
                    'source': '🛠️ JOOBLE (Missions & Sous-traitance)',
                    'titre': link.text.strip(),
                    'lien': link.get('href'),
                    'texte': art.text.strip()[:500]
                })
    except Exception as e:
        print(f"Erreur Jooble: {e}")
    return opportunites

def scanner_marches_publics():
    print("🎯 Recherche d'attributions de marchés publics...")
    url = 'https://html.duckduckgo.com/html/'
    query = 'site:francemarches.com "attribution" ("génie civil" OR "gros oeuvre") 2026'
    payload = {'q': query}
    opportunites = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.post(url, data=payload, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        results = soup.find_all('div', class_='result__body')[:2]
        for res in results:
            link = res.find('a', class_='result__url')
            snippet = res.find('a', class_='result__snippet')
            if link and snippet:
                opportunites.append({
                    'source': '🏢 MARCHÉ PUBLIC GAGNÉ',
                    'titre': link.text.strip(),
                    'lien': link.get('href'),
                    'texte': snippet.text.strip()
                })
    except Exception as e:
        print(f"Erreur Marchés Publics: {e}")
    return opportunites

def scanner_upwork():
    url = "https://www.upwork.com/ab/feed/jobs/rss?q=%22civil+engineering%22+OR+structural+OR+eurocodes&sort=recency"
    missions = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'xml')
        items = soup.find_all('item')[:2]
        for item in items:
            missions.append({
                'source': '🌍 MISSION UPWORK',
                'titre': item.title.text,
                'lien': item.link.text,
                'texte': item.description.text[:500]
            })
    except Exception as e:
        print(f"Erreur Upwork: {e}")
    return missions

async def analyser_opportunite(item):
    prompt = f"""Analyse cette opportunité BTP ({item['source']}) : {item['titre']} - {item['texte']}.
    1. 🎯 L'ENJEU : Pourquoi un freelance/consultant est utile ici ?
    2. 💬 L'ACCROCHE : Une phrase d'expert pour décrocher un RDV."""
    try:
        response = client.chat.complete(model="mistral-tiny", messages=[{"role": "user", "content": prompt}])
        return f"**{item['source']}**\n📌 {item['titre']}\n🔗 {item['lien']}\n\n{response.choices[0].message.content}"
    except:
        return f"Erreur IA sur {item['titre']}"

async def executer_radar():
    print(f"🚀 Sniper V3 (Jooble + MP + Upwork) lancé...")
    data = scanner_marches_publics() + scanner_upwork() + scanner_jooble()
    
    if not data:
        data = [{'source': '💡 TEST', 'titre': 'Ingénieur Structure', 'lien': 'http://google.com', 'texte': 'Test système'}]

    message_final = "🏗️ **RADAR BUSINESS : ÉDITION 3H** 🏗️\n\n"
    for opport in data:
        analyse = await analyser_opportunite(opport)
        message_final += f"{analyse}\n\n──────────────\n\n"
        await asyncio.sleep(2)

    await bot.send_message(chat_id=str(CHAT_ID), text=message_final, parse_mode='Markdown')

if __name__ == "__main__":
    asyncio.run(executer_radar())