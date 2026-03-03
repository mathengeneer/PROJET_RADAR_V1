import os
import time
import asyncio
from mistralai import Mistral
from telegram import Bot
from googlesearch import search

# Configuration des API
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

client = Mistral(api_key=MISTRAL_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)

def chercher_offres():
    print("🔎 Recherche d'offres réelles sur Google...")
    query = '"Génie Civil" (CDI OR "offre d\'emploi") France after:2026-02-20'
    liens = []
    try:
        for url in search(query, num_results=5, lang="fr"):
            liens.append(url)
    except Exception as e:
        print(f"Erreur recherche : {e}")
    return liens

async def analyser_avec_mistral(url):
    prompt = f"Analyse ce lien d'offre d'emploi en Génie Civil : {url}. Fais-moi un résumé très court (Poste, Lieu, Entreprise) et dis-moi si c'est pertinent."
    try:
        response = client.chat.complete(
            model="mistral-tiny",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Erreur Mistral sur {url}: {e}"

async def executer_radar():
    print("🚀 Démarrage du Radar...")
    offres = chercher_offres()
    
    if not offres:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="✅ Scan terminé : Aucune nouvelle offre trouvée.")
        return

    message_final = "🏗️ **NOUVELLES OFFRES GÉNIE CIVIL** 🏗️\n\n"
    
    for url in offres:
        analyse = await analyser_avec_mistral(url)
        message_final += f"🔗 {url}\n📝 {analyse}\n\n"
        time.sleep(1) # Sécurité pour ne pas saturer

    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message_final, parse_mode='Markdown')
    print("✅ Message envoyé sur Telegram !")

if __name__ == "__main__":
    asyncio.run(executer_radar())