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
        articles = soup.find_all('article')[:3]
        for art in articles:
            link = art.find('a')
            if link:
                opportunites.append({
                    'source': '🛠️ JOOBLE (Sous-traitance)',
                    'titre': link.text.strip(),
                    'lien': link.get('href'),
                    'texte': art.text.strip()[:500]
                })
    except Exception as e:
        print(f"Erreur Jooble: {e}")
    return opportunites

def scanner_marches_publics():
    """Cible les entreprises qui viennent de gagner des chantiers"""
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
    """Cible les missions freelance mondiales"""
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
    """L'IA prépare ton approche commerciale de façon SYNTHÉTIQUE"""
    prompt = f"""Analyse RAPIDEMENT (max 500 caractères) cette opportunité BTP : {item['titre']} - {item['texte']}.
    1. 🎯 L'ENJEU : Pourquoi un expert est utile ?
    2. 💬 L'ACCROCHE : Une phrase d'expert pour décrocher un RDV."""
    try:
        response = client.chat.complete(model="mistral-tiny", messages=[{"role": "user", "content": prompt}])
        content = response.choices[0].message.content
        return f"**{item['source']}**\n📌 {item['titre']}\n🔗 {item['lien']}\n\n{content}"
    except:
        return f"**{item['source']}**\n📌 {item['titre']}\n🔗 {item['lien']}\n\n(Analyse IA indisponible)"

async def executer_radar():
    print(f"🚀 Sniper V3.1 (Correctif Anti-Crash) lancé...")
    
    # Récupération des données
    data = scanner_marches_publics() + scanner_upwork() + scanner_jooble()
    
    # Mission de test si rien n'est trouvé
    if not data:
        data = [{
            'source': '💡 TEST SYSTÈME', 
            'titre': 'Ingénieur Structure Indépendant', 
            'lien': 'http://google.com', 
            'texte': 'Vérification de notes de calcul béton armé.'
        }]

    # On limite à 4 résultats pour ne pas saturer le workflow
    data = data[:4]

    for opport in data:
        analyse = await analyser_opportunite(opport)
        
        # Envoi d'un message par opportunité (évite l'erreur "Message too long")
        header = "🏗️ **RADAR BUSINESS : OPPORTUNITÉ** 🏗️\n\n"
        
        try:
            # Sécurité : on tronque à 3800 caractères au cas où
            texte_final = (header + analyse)[:3800]
            await bot.send_message(
                chat_id=str(CHAT_ID), 
                text=texte_final, 
                parse_mode='Markdown'
            )
            print(f"✅ Alerte envoyée : {opport['titre'][:30]}...")
        except Exception as e:
            # En cas d'erreur de formatage Markdown, on envoie en texte brut
            print(f"⚠️ Erreur Markdown, envoi en texte brut : {e}")
            await bot.send_message(chat_id=str(CHAT_ID), text=texte_final)
        
        # Pause pour respecter les limites de Telegram
        await asyncio.sleep(2)

    print("✅ Session de scan terminée !")

if __name__ == "__main__":
    asyncio.run(executer_radar())