import os
import asyncio
import requests
from bs4 import BeautifulSoup
from mistralai import Mistral
from telegram import Bot

MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")

client = Mistral(api_key=MISTRAL_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)

def scanner_upwork():
    # Flux RSS public d'Upwork pour le Génie Civil / Autocad
    url = "https://www.upwork.com/ab/feed/jobs/rss?q=civil+engineering+OR+autocad&sort=recency"
    print("🎯 Scan des missions Upwork en cours...")
    missions = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Récupère les 2 offres les plus récentes
        items = soup.find_all('item')[:2]
        for item in items:
            title = item.title.text if item.title else "Mission"
            link = item.link.text if item.link else ""
            desc = item.description.text[:800] if item.description else ""
            missions.append({'source': 'Upwork (Plateforme Freelance)', 'titre': title, 'lien': link, 'texte': desc})
    except Exception as e:
        print(f"Erreur Upwork: {e}")
    return missions

def scanner_reseau_linkedin():
    # Technique "Dorking" via DuckDuckGo pour fouiller dans les posts LinkedIn sans être bloqué
    print("🕵️‍♂️ Hack Recherche LinkedIn en cours...")
    url = 'https://html.duckduckgo.com/html/'
    # La requête magique
    payload = {'q': 'site:linkedin.com/posts "génie civil" ("recherche" OR "freelance" OR "besoin")'}
    missions = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.post(url, data=payload, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Récupère les 2 premiers posts pertinents
        results = soup.find_all('div', class_='result__body')[:2]
        for res in results:
            title_tag = res.find('a', class_='result__url')
            snippet_tag = res.find('a', class_='result__snippet')
            if title_tag and snippet_tag:
                missions.append({
                    'source': 'LinkedIn (Réseau B2B)',
                    'titre': title_tag.text.strip(),
                    'lien': title_tag.get('href'),
                    'texte': snippet_tag.text.strip()
                })
    except Exception as e:
        print(f"Erreur DDG: {e}")
    return missions

async def analyser_et_vendre(mission):
    # Le nouveau rôle de Mistral : Ton Business Developer
    prompt = f"""
    Tu es mon assistant en Business Development. Voici une opportunité trouvée sur le web :
    Titre: {mission['titre']}
    Détails: {mission['texte']}
    
    Fais-moi un résumé ULTRA COURT :
    1. 🚨 Le vrai besoin du client (Ex: Il est bloqué sur des plans AutoCAD).
    2. 💡 Une idée de phrase d'accroche (brise-glace) très directe et percutante que je peux lui envoyer en message privé pour proposer mes services en freelance.
    Ne réponds que par ces deux points, sois concis et vendeur.
    """
    try:
        response = client.chat.complete(model="mistral-tiny", messages=[{"role": "user", "content": prompt}])
        analyse = response.choices[0].message.content
        return f"**{mission['titre']}**\n🔗 {mission['lien']}\n\n{analyse}"
    except Exception as e:
        return f"Erreur Mistral: {e}"

async def executer_radar():
    print(f"🚀 Démarrage du Radar Chasseur... ID: {CHAT_ID}")
    
    # On rassemble les missions d'Upwork et de LinkedIn
    toutes_les_missions = scanner_upwork() + scanner_reseau_linkedin()
    
    if not toutes_les_missions:
        await bot.send_message(chat_id=str(CHAT_ID), text="🕵️‍♂️ Radar actif : Aucune mission détectée sur cette session. Je relance au prochain cycle !")
        return

    message_final = "💰 **OPPORTUNITÉS FREELANCE/CONSULTING** 💰\n\n"
    
    for mission in toutes_les_missions:
        analyse = await analyser_et_vendre(mission)
        message_final += f"🏢 **SOURCE : {mission['source']}**\n{analyse}\n\n"
        message_final += "──────────────\n"
        await asyncio.sleep(2) # Stabilité

    # Sécurité pour ne pas dépasser la limite de texte de Telegram
    if len(message_final) > 4000:
        message_final = message_final[:4000] + "...\n(Tronqué)"

    await bot.send_message(chat_id=str(CHAT_ID), text=message_final, parse_mode='Markdown')
    print("✅ Rapport opportunités envoyé !")

if __name__ == "__main__":
    asyncio.run(executer_radar())