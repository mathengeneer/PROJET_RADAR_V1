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
    print(f"🚀 Sniper V4.1 (Correctif Telegram) lancé...")
    
    # 1. Collecte des données
    missions_reelles = scanner_flux_rss()
    prospect_ia = await generer_prospect_ia()
    
    data = missions_reelles
    if prospect_ia:
        data.append(prospect_ia)

    # 2. Envoi des messages UN PAR UN (évite les bugs de limite et de Markdown)
    await bot.send_message(chat_id=str(CHAT_ID), text="🏗️ **NOUVEAU RAPPORT RADAR BTP** 🏗️", parse_mode='Markdown')
    
    for opport in data:
        try:
            analyse = await analyser_opportunite(opport)
            # On envoie chaque opportunité dans sa propre bulle Telegram
            await bot.send_message(
                chat_id=str(CHAT_ID), 
                text=analyse, 
                parse_mode='Markdown'
            )
            print(f"✅ Message envoyé pour : {opport['titre'][:30]}")
            await asyncio.sleep(1) # Petite pause pour respecter les limites de Telegram
        except Exception as e:
            print(f"⚠️ Erreur d'envoi pour une opportunité : {e}")
            # En cas d'erreur Markdown, on envoie en texte brut pour ne rien rater
            await bot.send_message(chat_id=str(CHAT_ID), text=f"Lien : {opport['lien']}\n(Erreur de formatage sur cette fiche)")

    print("✅ Session terminée !")

if __name__ == "__main__":
    asyncio.run(executer_radar())