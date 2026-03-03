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

def extraire_texte_url(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        # On prend les 2000 premiers caractères pour ne pas saturer l'IA
        return soup.get_text()[:2000]
    except:
        return "Impossible de lire la page directement."

async def analyser_reelle(url):
    contenu = extraire_texte_url(url)
    prompt = f"Voici le texte d'un site d'emploi : {contenu}. Liste-moi UNIQUEMENT les 3 titres de postes les plus récents en Génie Civil et leur ville. Sois précis sur les noms."
    try:
        response = client.chat.complete(model="mistral-tiny", messages=[{"role": "user", "content": prompt}])
        return response.choices[0].message.content
    except Exception as e:
        return f"Erreur : {e}"

async def executer_radar():
    sources = [
        "https://www.hellowork.com/fr-fr/emploi/recherche.html?k=g%C3%A9nie+civil",
        "https://www.linkedin.com/jobs/search/?keywords=genie%20civil"
    ]
    
    message = "🏗️ **RADAR LIVE : OFFRES RÉELLES** 🏗️\n\n"
    for url in sources:
        analyse = await analyser_reelle(url)
        message += f"📍 **Source :** {url}\n✅ {analyse}\n\n"
    
    await bot.send_message(chat_id=str(CHAT_ID), text=message, parse_mode='Markdown')

if __name__ == "__main__":
    asyncio.run(executer_radar())