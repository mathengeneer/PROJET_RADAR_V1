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

def scanner_marches_publics():
    """Cible les entreprises qui viennent de gagner des chantiers (Gros Portefeuille)"""
    print("🎯 Recherche d'attributions de marchés publics (Génie Civil)...")
    url = 'https://html.duckduckgo.com/html/'
    # Recherche ciblée sur les attributions 2026 de gros oeuvre et génie civil
    query = 'site:francemarches.com "attribution" ("génie civil" OR "gros oeuvre") 2026'
    payload = {'q': query}
    opportunites = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.post(url, data=payload, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        results = soup.find_all('div', class_='result__body')[:3]
        for res in results:
            link = res.find('a', class_='result__url')
            snippet = res.find('a', class_='result__snippet')
            if link and snippet:
                opportunites.append({
                    'source': '🏢 MARCHÉ PUBLIC GAGNÉ (Client Potentiel)',
                    'titre': link.text.strip(),
                    'lien': link.get('href'),
                    'texte': snippet.text.strip()
                })
    except Exception as e:
        print(f"Erreur Marchés Publics: {e}")
    return opportunites

def scanner_upwork():
    """Cible les missions freelance mondiales (Revenu Immédiat)"""
    url = "https://www.upwork.com/ab/feed/jobs/rss?q=%22civil+engineering%22+OR+structural+OR+eurocodes&sort=recency"
    missions = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'xml') # 'xml' car c'est un flux RSS
        items = soup.find_all('item')[:2]
        for item in items:
            missions.append({
                'source': '🌍 MISSION FREELANCE (Upwork)',
                'titre': item.title.text,
                'lien': item.link.text,
                'texte': item.description.text[:800]
            })
    except Exception as e:
        print(f"Erreur Upwork: {e}")
    return missions

async def analyser_opportunite(item):
    """L'IA prépare ton approche commerciale"""
    prompt = f"""
    Analyse cette opportunité BTP :
    Source : {item['source']}
    Titre : {item['titre']}
    Contenu : {item['texte']}
    
    Réponds brièvement :
    1. 🎯 **L'ENJEU** : Pourquoi ont-ils besoin d'un expert maintenant ?
    2. 💬 **L'ACCROCHE** : Une phrase d'expert (Eurocodes, calcul de structure, plans d'exécution) pour décrocher un rdv.
    """
    try:
        response = client.chat.complete(model="mistral-tiny", messages=[{"role": "user", "content": prompt}])
        return f"**{item['source']}**\n📌 {item['titre']}\n🔗 {item['lien']}\n\n{response.choices[0].message.content}"
    except Exception as e:
        return f"Erreur IA: {e}"

async def executer_radar():
    print(f"🚀 Lancement du Sniper V2... ID: {CHAT_ID}")
    
    # Mix de "Contrats Gagnés" et "Missions Freelance"
    data = scanner_marches_publics() + scanner_upwork()
    
    if not data:
        # On garde une mission de test "Fictive" pour toujours valider la connexion
        data = [{
            'source': '💡 MISSION TEST (Auto-générée)',
            'titre': 'Calculateur de Structure (Freelance) - Béton Armé',
            'lien': 'https://www.google.com',
            'texte': 'Besoin de renfort sur une étude de bâtiment R+5 à Lyon. Eurocodes 2.'
        }]

    message_final = "🏗️ **RADAR BUSINESS : OPPORTUNITÉS GÉNIE CIVIL** 🏗️\n\n"
    for opport in data:
        analyse = await analyser_opportunite(opport)
        message_final += f"{analyse}\n\n"
        message_final += "──────────────\n\n"
        await asyncio.sleep(2)

    await bot.send_message(chat_id=str(CHAT_ID), text=message_final, parse_mode='Markdown')
    print("✅ Rapport Sniper envoyé sur Telegram !")

if __name__ == "__main__":
    asyncio.run(executer_radar())