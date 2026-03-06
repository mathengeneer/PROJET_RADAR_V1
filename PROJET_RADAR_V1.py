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
    """Version Turbo : Balaye large sur le BTP et la Structure"""
    print("🎯 Scan Jooble élargi...")
    query = "ingénieur structure OR béton armé OR charpente OR étude de prix"
    url = f'https://fr.jooble.org/SearchResult?ukw={query}'
    opportunites = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('article')[:3]
        for art in articles:
            link = art.find('a')
            if link:
                opportunites.append({
                    'source': '🛠️ JOOBLE (Besoin Technique)',
                    'titre': link.text.strip(),
                    'lien': link.get('href'),
                    'texte': art.text.strip()[:500]
                })
    except Exception as e:
        print(f"Erreur Jooble: {e}")
    return opportunites

def scanner_marches_publics():
    """Version Turbo : Cherche les attributions RÉCENTES sans limite d'année"""
    print("🎯 Scan Marchés Publics (Attributions récentes)...")
    url = 'https://html.duckduckgo.com/html/'
    query = 'site:francemarches.com "attribution" ("gros oeuvre" OR "structure" OR "maçonnerie")'
    payload = {'q': query}
    opportunites = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.post(url, data=payload, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        results = soup.find_all('div', class_='result__body')[:3]
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

def scanner_reseau_linkedin():
    """Recherche de posts LinkedIn 'Besoin/Urgent'"""
    print("🕵️‍♂️ Recherche de posts LinkedIn...")
    url = 'https://html.duckduckgo.com/html/'
    query = 'site:linkedin.com/posts "recherche freelance" OR "besoin renfort" ("structure" OR "BTP")'
    payload = {'q': query}
    missions = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.post(url, data=payload, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        results = soup.find_all('div', class_='result__body')[:2]
        for res in results:
            link = res.find('a', class_='result__url')
            snippet = res.find('a', class_='result__snippet')
            if link and snippet:
                missions.append({
                    'source': '👤 POST LINKEDIN (Direct)',
                    'titre': link.text.strip()[:100],
                    'lien': link.get('href'),
                    'texte': snippet.text.strip()
                })
    except Exception as e:
        print(f"Erreur LinkedIn: {e}")
    return missions

def scanner_upwork():
    """Cible les missions freelance mondiales"""
    print("🌍 Scan Upwork...")
    url = "https://www.upwork.com/ab/feed/jobs/rss?q=%22civil+engineering%22+OR+structural+OR+eurocodes&sort=recency"
    missions = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
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
    """Mistral analyse et prépare l'argumentaire"""
    prompt = f"""
    Analyse cette opportunité BTP :
    Source : {item['source']}
    Titre : {item['titre']}
    Contenu : {item['texte']}
    
    Réponds de manière très concise :
    1. 🎯 **L'ENJEU** : Pourquoi un freelance/consultant en structure est vital ici (risques, délais) ?
    2. 💬 **L'ACCROCHE** : Une phrase d'expert percutante pour décrocher un RDV avec le décideur.
    """
    try:
        response = client.chat.complete(model="mistral-tiny", messages=[{"role": "user", "content": prompt}])
        return f"**{item['source']}**\n📌 {item['titre']}\n🔗 {item['lien']}\n\n{response.choices[0].message.content}"
    except Exception as e:
        return f"Erreur IA sur {item['titre']}: {e}"

async def executer_radar():
    print(f"🚀 Lancement du Radar Turbo... ID: {CHAT_ID}")
    
    # On lance les 4 filets en même temps
    data = scanner_marches_publics() + scanner_upwork() + scanner_jooble() + scanner_reseau_linkedin()
    
    if not data:
        # La mission de test pour être sûr que la machine tourne
        data = [{
            'source': '💡 TEST SYSTÈME',
            'titre': 'Ingénieur Structure Indépendant - Mission de Test',
            'lien': 'http://google.com',
            'texte': 'Ceci est un test pour vérifier que le radar de prospection B2B fonctionne correctement.'
        }]

    message_final = "🏗️ **RADAR BUSINESS : ÉDITION TURBO** 🏗️\n\n"
    for opport in data:
        analyse = await analyser_opportunite(opport)
        message_final += f"{analyse}\n\n──────────────\n\n"
        await asyncio.sleep(2) # Pause pour ne pas brusquer l'API Telegram

    # Envoi final
    await bot.send_message(chat_id=str(CHAT_ID), text=message_final[:4000], parse_mode='Markdown')
    print("✅ Rapport envoyé sur Telegram !")

if __name__ == "__main__":
    asyncio.run(executer_radar())