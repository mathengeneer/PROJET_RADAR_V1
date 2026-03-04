import os
import asyncio
import requests
import time
from bs4 import BeautifulSoup
from mistralai import Mistral
from telegram import Bot

# --- CONFIGURATION DES ACCÈS ---
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")

client = Mistral(api_key=MISTRAL_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)

# --- FONCTION 1 : LE SNIPER UPWORK (Missions Freelance) ---
def scanner_upwork():
    # Recherche élargie : Civil Engineering, Structural, AutoCAD, Revit
    url = "https://www.upwork.com/ab/feed/jobs/rss?q=%22civil+engineering%22+OR+structural+OR+autocad+OR+revit&sort=recency"
    print("🎯 Scan des missions Upwork en cours...")
    missions = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'xml') # On utilise le parseur XML pour le RSS
        
        items = soup.find_all('item')[:3] # On prend les 3 plus récentes
        for item in items:
            missions.append({
                'source': 'Upwork (Freelance)',
                'titre': item.title.text if item.title else "Mission Upwork",
                'lien': item.link.text if item.link else "",
                'texte': item.description.text[:1000] if item.description else ""
            })
    except Exception as e:
        print(f"⚠️ Erreur Upwork: {e}")
    return missions

# --- FONCTION 2 : LE HACK LINKEDIN (Réseau B2B via DuckDuckGo) ---
def scanner_reseau_linkedin():
    print("🕵️‍♂️ Recherche d'opportunités sur les posts LinkedIn...")
    url = 'https://html.duckduckgo.com/html/'
    # Requête élargie : Génie Civil ou BTP + recherche d'indépendant/mission
    query = 'site:linkedin.com/posts "génie civil" OR "BTP" ("freelance" OR "mission" OR "indépendant" OR "recherche consultant")'
    payload = {'q': query}
    missions = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.post(url, data=payload, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = soup.find_all('div', class_='result__body')[:3]
        for res in results:
            link_tag = res.find('a', class_='result__url')
            snippet_tag = res.find('a', class_='result__snippet')
            if link_tag and snippet_tag:
                missions.append({
                    'source': 'LinkedIn (Réseau B2B)',
                    'titre': link_tag.text.strip()[:100],
                    'lien': link_tag.get('href'),
                    'texte': snippet_tag.text.strip()
                })
    except Exception as e:
        print(f"⚠️ Erreur LinkedIn via DDG: {e}")
    return missions

# --- FONCTION 3 : L'IA BUSINESS DEVELOPER ---
async def analyser_et_vendre(mission):
    prompt = f"""
    En tant qu'expert en business development BTP, analyse cette opportunité :
    Source: {mission['source']}
    Titre: {mission['titre']}
    Contenu: {mission['texte']}
    
    Réponds de manière concise (max 100 mots) :
    1. 🚨 BESOIN : Quel est le problème urgent du client ?
    2. 💡 ACCROCHE : Propose une phrase brise-glace percutante pour que je propose mes services de consultant/freelance.
    """
    try:
        response = client.chat.complete(model="mistral-tiny", messages=[{"role": "user", "content": prompt}])
        return response.choices[0].message.content
    except Exception as e:
        return f"Analyse indisponible : {e}"

# --- FONCTION PRINCIPALE : LE RADAR ---
async def executer_radar():
    print(f"🚀 Démarrage du Radar Chasseur de Primes... ID: {CHAT_ID}")
    
    # 1. CRÉATION D'UNE MISSION DE TEST (Pour vérifier que tout marche)
    missions_trouvees = [{
        'source': 'SYSTÈME (Test)',
        'titre': 'Consultant Structure Béton - Mission Urgente',
        'lien': 'https://www.linkedin.com',
        'texte': 'Besoin de renfort pour calculs de descentes de charges Eurocodes sur un projet résidentiel.'
    }]
    
    # 2. COLLECTE DES VRAIES MISSIONS
    missions_trouvees += scanner_upwork()
    missions_trouvees += scanner_reseau_linkedin()
    
    message_final = "💰 **RADAR BUSINESS : OPPORTUNITÉS DETECTÉES** 💰\n\n"
    
    # 3. ANALYSE ET ENVOI
    for mission in missions_trouvees:
        print(f"Analyse de : {mission['titre']}")
        analyse = await analyser_et_vendre(mission)
        
        bloc = f"🏢 **{mission['source']}**\n"
        bloc += f"📌 **{mission['titre']}**\n"
        bloc += f"🔗 {mission['lien']}\n"
        bloc += f"{analyse}\n"
        bloc += "───────────────────\n"
        
        # On vérifie la taille du message pour Telegram (max 4096 car.)
        if len(message_final + bloc) > 4000:
            await bot.send_message(chat_id=str(CHAT_ID), text=message_final, parse_mode='Markdown')
            message_final = ""
        
        message_final += bloc
        await asyncio.sleep(1) # Pause pour éviter le spam

    await bot.send_message(chat_id=str(CHAT_ID), text=message_final, parse_mode='Markdown')
    print("✅ Session terminée. Message envoyé !")

if __name__ == "__main__":
    asyncio.run(executer_radar())