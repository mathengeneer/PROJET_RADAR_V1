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
    """Scan Jooble sur des termes techniques"""
    print("🎯 Scan Jooble...")
    query = "ingénieur structure OR béton armé OR diagnostic solidité"
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
                    'source': '🛠️ JOOBLE',
                    'titre': link.text.strip(),
                    'lien': link.get('href'),
                    'texte': art.text.strip()[:500]
                })
    except Exception as e:
        print(f"Erreur Jooble: {e}")
    return opportunites

def scanner_marches_publics():
    """Scan les attributions de marchés publics récents"""
    print("🎯 Scan Marchés Publics...")
    url = 'https://html.duckduckgo.com/html/'
    query = 'site:francemarches.com "attribution" ("gros oeuvre" OR "structure")'
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
    """Recherche de posts LinkedIn via DuckDuckGo"""
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
            if link:
                missions.append({
                    'source': '👤 POST LINKEDIN',
                    'titre': link.text.strip()[:100],
                    'lien': link.get('href'),
                    'texte': "Post LinkedIn détecté. Vérifiez le contenu en cliquant."
                })
    except:
        pass
    return missions

def scanner_archeologue_btp():
    """NOUVEAU : Scan profond des missions de la semaine sur Free-Work"""
    print("🔍 Scan Archéologue (Missions semaine)...")
    query = "structure+freelance"
    url = f'https://www.free-work.com/fr/tech-it/jobs?query={query}'
    missions = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        # On cible les cartes de job sur Free-Work
        articles = soup.find_all('h2')[:5] 
        for art in articles:
            link = art.find_parent('a')
            if link:
                missions.append({
                    'source': '🕵️‍♂️ ARCHÉOLOGUE (Free-Work)',
                    'titre': art.text.strip(),
                    'lien': "https://www.free-work.com" + link.get('href') if not link.get('href').startswith('http') else link.get('href'),
                    'texte': "Mission en stock détectée. Opportunité à saisir pour renfort structure."
                })
    except Exception as e:
        print(f"Erreur Archéologue: {e}")
    return missions

def scanner_upwork():
    """Scan Upwork via flux RSS"""
    print("🌍 Scan Upwork...")
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
    except:
        pass
    return missions

async def analyser_opportunite(item):
    """Analyse IA avec Mistral"""
    prompt = f"""
    Analyse cette opportunité BTP :
    Source : {item['source']}
    Titre : {item['titre']}
    Contenu : {item['texte']}
    
    1. 🎯 L'ENJEU : Pourquoi ont-ils besoin d'un expert maintenant ?
    2. 💬 L'ACCROCHE : Une phrase d'expert courte pour décrocher un RDV.
    """
    try:
        response = client.chat.complete(model="mistral-tiny", messages=[{"role": "user", "content": prompt}])
        return f"**{item['source']}**\n📌 {item['titre']}\n🔗 {item['lien']}\n\n{response.choices[0].message.content}"
    except:
        return f"**{item['source']}**\n📌 {item['titre']}\n🔗 {item['lien']}\n\n⚠️ Analyse indisponible."

async def executer_radar():
    print(f"🚀 Lancement du Radar Scan Complet...")
    
    # Récupération des données
    data = (
        scanner_marches_publics() + 
        scanner_upwork() + 
        scanner_jooble() + 
        scanner_reseau_linkedin() + 
        scanner_archeologue_btp()
    )
    
    # Préparation du rapport
    message_final = "🏗️ **RAPPORT RADAR BTP** 🏗️\n\n"
    
    if not data:
        message_final += "Aucune nouvelle opportunité détectée lors de ce cycle."
    else:
        for opport in data[:5]: # On prend les 5 meilleurs
            analyse_result = await analyser_opportunite(opport)
            # Ajout de sécurité : si l'analyse est vide, on force un affichage minimal
            if not analyse_result:
                analyse_result = f"📌 {opport['titre']}\n🔗 {opport['lien']}\n⚠️ Analyse IA indisponible, consultez le lien directement."
            
            ajout = f"{analyse_result}\n\n──────────────\n\n"
            if len(message_final) + len(ajout) < 3800:
                message_final += ajout
            else:
                break

    # Envoi final sécurisé
    try:
        # On tente l'envoi avec Markdown
        await bot.send_message(chat_id=str(CHAT_ID), text=message_final, parse_mode='Markdown')
    except Exception:
        # Si le Markdown échoue (souvent à cause de caractères spéciaux dans les liens), on envoie en texte simple
        await bot.send_message(chat_id=str(CHAT_ID), text=message_final)
    
    print("✅ Rapport envoyé !")

if __name__ == "__main__":
    asyncio.run(executer_radar())