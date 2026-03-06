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

def scanner_flux_rss():
    """Utilise les flux RSS (portes ouvertes) pour éviter les blocages anti-robots"""
    print("📡 Scan des flux RSS professionnels...")
    # Upwork est très fiable en RSS. On peut en ajouter d'autres ici.
    urls = [
        "https://www.upwork.com/ab/feed/jobs/rss?q=%22civil+engineering%22+OR+structural+OR+eurocodes&sort=recency"
    ]
    opportunites = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=15)
            # On utilise lxml pour parser le XML du flux RSS
            soup = BeautifulSoup(response.text, 'xml')
            items = soup.find_all('item')[:3]
            for item in items:
                opportunites.append({
                    'source': '📡 FLUX DIRECT (Upwork)',
                    'titre': item.title.text.strip(),
                    'lien': item.link.text.strip(),
                    'texte': item.description.text.strip()[:500]
                })
        except Exception as e:
            print(f"Erreur RSS: {e}")
    return opportunites

async def generer_prospect_ia():
    """Si le web est vide, Mistral génère une cible stratégique (Lead Generation)"""
    prompt = """
    Donne-moi une fiche stratégique pour un ingénieur structure indépendant. 
    Cible : Une entreprise majeure du BTP ou un Bureau d'Études en France (ex: Egis, Setec, Bouygues, Spie Batignolles).
    Inclus : 
    1. Pourquoi ils ont besoin de freelances en ce moment.
    2. Comment les aborder sur LinkedIn (phrase d'accroche).
    """
    try:
        response = client.chat.complete(model="mistral-tiny", messages=[{"role": "user", "content": prompt}])
        return {
            'source': '💡 CIBLE STRATÉGIQUE DU JOUR',
            'titre': "Prospection Directe - Bureau d'Études / Major du BTP",
            'lien': "https://www.linkedin.com",
            'texte': response.choices[0].message.content
        }
    except:
        return None

async def analyser_opportunite(item):
    """Analyse personnalisée par Mistral"""
    prompt = f"Opportunité : {item['titre']}. Contenu : {item['texte']}. Prépare une accroche courte et experte pour vendre mes services d'ingénieur structure."
    try:
        response = client.chat.complete(model="mistral-tiny", messages=[{"role": "user", "content": prompt}])
        return f"**{item['source']}**\n📌 {item['titre']}\n🔗 {item['lien']}\n\n{response.choices[0].message.content}"
    except:
        return f"**{item['source']}**\n📌 {item['titre']}\n🔗 {item['lien']}\n\n(Analyse IA indisponible)"

async def executer_radar():
    print(f"🚀 Sniper V4 (RSS + LeadGen) lancé...")
    
    # 1. On cherche les missions réelles via RSS
    missions_reelles = scanner_flux_rss()
    
    # 2. On génère toujours une cible stratégique pour ne pas repartir les mains vides
    prospect_ia = await generer_prospect_ia()
    
    # On combine tout
    data = missions_reelles
    if prospect_ia:
        data.append(prospect_ia)

    message_final = "🏗️ **RADAR BUSINESS : ÉDITION V4** 🏗️\n\n"
    for opport in data:
        analyse = await analyser_opportunite(opport)
        message_final += f"{analyse}\n\n──────────────\n\n"
        await asyncio.sleep(1)

    await bot.send_message(chat_id=str(CHAT_ID), text=message_final[:4000], parse_mode='Markdown')
    print("✅ Rapport V4 envoyé !")

if __name__ == "__main__":
    asyncio.run(executer_radar())