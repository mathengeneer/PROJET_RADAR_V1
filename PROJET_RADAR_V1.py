import os
import asyncio
import requests
from bs4 import BeautifulSoup
from mistralai import Mistral
from telegram import Bot

# --- CONFIGURATION DES SECRETS ---
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")

client = Mistral(api_key=MISTRAL_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)

# --- MOTEURS DE RECHERCHE ---

def scanner_jooble():
    """Cible les missions de sous-traitance sur Jooble"""
    print("🎯 Scan Jooble...")
    query = "ingénieur structure OR béton armé OR charpente OR étude de prix"
    url = f'https://fr.jooble.org/SearchResult?ukw={query}'
    opportunites = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('article')[:3]
        for art in articles:
            link = art.find('a')
            if link:
                opportunites.append({
                    'source': '🛠️ JOOBLE',
                    'titre': link.text.strip(),
                    'lien': link.get('href'),
                    'texte': art.text.strip()[:500]
                })
    except: pass
    return opportunites

def scanner_marches_publics():
    """Détecte les attributions de marchés (Potentiels clients)"""
    print("🎯 Scan Marchés Publics...")
    url = 'https://html.duckduckgo.com/html/'
    query = 'site:francemarches.com "attribution" ("gros oeuvre" OR "structure" OR "maçonnerie")'
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
                    'source': '🏢 MARCHÉ PUBLIC GAGNÉ',
                    'titre': link.text.strip(),
                    'lien': link.get('href'),
                    'texte': snippet.text.strip()
                })
    except: pass
    return opportunites

def scanner_freework_btp():
    """Cible les missions Freelance sur Free-Work France"""
    print("🎯 Scan Free-Work...")
    url = 'https://www.free-work.com/fr/tech-it/jobs?query=structure+btp'
    opportunites = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        jobs = soup.find_all('h2')[:2] 
        for job in jobs:
            link = job.find_parent('a')
            if link:
                opportunites.append({
                    'source': '🏗️ FREE-WORK (Mission)',
                    'titre': job.text.strip(),
                    'lien': "https://www.free-work.com" + link.get('href'),
                    'texte': "Besoin technique détecté sur Free-Work."
                })
    except: pass
    return opportunites

def scanner_reseau_linkedin():
    """Trouve des posts LinkedIn via DuckDuckGo"""
    print("🎯 Scan LinkedIn...")
    url = 'https://html.duckduckgo.com/html/'
    query = 'site:linkedin.com/posts "recherche freelance" OR "besoin renfort" ("structure" OR "BTP")'
    payload = {'q': query}
    missions = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.post(url, data=payload, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        results = soup.find_all('div', class_='result__body')[:3]
        for res in results:
            link = res.find('a', class_='result__url')
            snippet = res.find('a', class_='result__snippet')
            if link and snippet:
                missions.append({
                    'source': '👤 POST LINKEDIN',
                    'titre': link.text.strip()[:100],
                    'lien': link.get('href'),
                    'texte': snippet.text.strip()
                })
    except: pass
    return missions

def scanner_upwork():
    """Missions internationales sur Upwork"""
    print("🎯 Scan Upwork...")
    url = "https://www.upwork.com/ab/feed/jobs/rss?q=%22civil+engineering%22+OR+structural+OR+eurocodes&sort=recency"
    missions = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'xml')
        items = soup.find_all('item')[:2]
        for item in items:
            missions.append({
                'source': '🌍 UPWORK',
                'titre': item.title.text,
                'lien': item.link.text,
                'texte': item.description.text[:500]
            })
    except: pass
    return missions

# --- ANALYSE IA AVEC PROTECTION ---

async def analyser_opportunite(item):
    """Prépare le script de vente avec Mistral"""
    # Si le texte est vide (blocage LinkedIn), on envoie un message générique intelligent
    description = item['texte'] if len(item['texte']) > 30 else "Analyse basée sur le titre (Contenu protégé)."
    
    prompt = f"""
    Analyse cette opportunité BTP : {item['titre']}
    Source : {item['source']}
    Texte : {description}

    1. 🎯 L'ENJEU : Pourquoi ont-ils besoin d'un expert en structure/génie civil ?
    2. 💬 L'ACCROCHE : Une phrase d'expert pour décrocher un RDV.
    """
    try:
        response = client.chat.complete(model="mistral-tiny", messages=[{"role": "user", "content": prompt}])
        resultat = response.choices[0].message.content
        return f"**{item['source']}**\n📌 {item['titre']}\n🔗 {item['lien']}\n\n{resultat}"
    except:
        return f"**{item['source']}**\n📌 {item['titre']}\n🔗 {item['lien']}\n\n⚠️ IA indisponible. Foncez voir le lien !"

# --- EXÉCUTION PRINCIPALE ---

async def executer_radar():
    print(f"🚀 Lancement du Radar Turbo V3... ID: {CHAT_ID}")
    
    # On vide le filet et on le remplit avec les 5 moteurs
    toutes_les_missions = (scanner_marches_publics() + 
                           scanner_upwork() + 
                           scanner_jooble() + 
                           scanner_freework_btp() + 
                           scanner_reseau_linkedin())
    
    if not toutes_les_missions:
        toutes_les_missions = [{
            'source': '💡 TEST SYSTÈME',
            'titre': 'Expert Structure - Audit Express',
            'lien': 'http://google.com',
            'texte': 'Vérification périodique du radar. Tout est OK.'
        }]

    print(f"📈 {len(toutes_les_missions)} pistes trouvées. Analyse en cours...")

    # On envoie chaque mission dans UN MESSAGE SÉPARÉ
    for m in toutes_les_missions:
        rapport = await analyser_opportunite(m)
        
        # On ajoute un petit header pour chaque message
        message_complet = f"🏗️ **NOUVELLE ALERTE BTP** 🏗️\n\n{rapport}"
        
        try:
            # On tronque quand même à 4000 au cas où l'IA bavarde trop
            await bot.send_message(
                chat_id=str(CHAT_ID), 
                text=message_complet[:4000], 
                parse_mode='Markdown'
            )
            print(f"✅ Message envoyé pour : {m['titre'][:30]}...")
        except Exception as e:
            print(f"❌ Erreur envoi Telegram : {e}")
            
        await asyncio.sleep(1) # Pause de 1s entre les messages pour Telegram

if __name__ == "__main__":
    asyncio.run(executer_radar())