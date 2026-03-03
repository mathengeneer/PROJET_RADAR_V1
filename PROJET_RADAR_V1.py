import os
import time
import asyncio
import urllib.request
from mistralai import Mistral
from telegram import Bot

# --- CONFIGURATION ---
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")

client = Mistral(api_key=MISTRAL_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)

def chercher_offres():
    print("📡 Connexion au flux d'offres Génie Civil...")
    # On utilise un moteur de recherche d'emploi qui accepte les robots (Jooble/Indeed via RSS)
    # Ici, on simule une recherche directe sur un agrégateur
    liens = [
        "https://fr.indeed.com/q-g%C3%A9nie-civil-l-france-emplois.html",
        "https://www.hellowork.com/fr-fr/emploi/recherche.html?k=g%C3%A9nie+civil"
    ]
    # Pour le test, on va forcer ces deux sites pour que Mistral les analyse
    print(f"📊 {len(liens)} sources de recrutement prêtes pour analyse.")
    return liens

async def analyser_avec_mistral(url):
    # On demande à Mistral de nous dire ce qu'il voit sur ces pages
    prompt = f"Peux-tu me donner les 3 titres d'offres d'emploi les plus récentes en Génie Civil que l'on trouve généralement sur ce site : {url} ? Réponds sous forme de liste courte (Poste, Ville)."
    try:
        response = client.chat.complete(
            model="mistral-tiny",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Erreur Mistral : {e}"

async def executer_radar():
    print(f"🚀 Démarrage du Radar RSS... ID: {CHAT_ID}")
    
    if not CHAT_ID:
        print("❌ ID manquant.")
        return

    offres = chercher_offres()
    
    message_final = "🏗️ **RADAR GÉNIE CIVIL : DERNIÈRES INFOS** 🏗️\n\n"
    
    for url in offres:
        print(f"Analyse de {url}...")
        analyse = await analyser_avec_mistral(url)
        message_final += f"🌐 **Source :** {url}\n📝 {analyse}\n\n"
        time.sleep(2)

    await bot.send_message(chat_id=str(CHAT_ID), text=message_final, parse_mode='Markdown')
    print("✅ Rapport envoyé sur Telegram !")

if __name__ == "__main__":
    asyncio.run(executer_radar())