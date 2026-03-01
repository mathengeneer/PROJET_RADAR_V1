import os
import asyncio
import google.generativeai as genai
from telegram import Bot

# ==========================================================
# 1. CONFIGURATION (Lecture des Secrets)
# ==========================================================
# Sur GitHub, il lira les "Secrets". Sur PC, il cherchera tes variables d'environnement.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Vérification de sécurité
if not all([GEMINI_API_KEY, TELEGRAM_TOKEN, CHAT_ID]):
    print("⚠️ Erreur : L'un des secrets (Gemini, Telegram ou Chat_ID) est absent !")

# Initialisation de l'IA
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# ==========================================================
# 2. LOGIQUE DU RADAR
# ==========================================================

async def envoyer_alerte(message):
    """Envoie la notification finale sur Telegram."""
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=f"🏗️ ALERTE GÉNIE CIVIL :\n\n{message}")
        print("✅ Message envoyé à Telegram.")
    except Exception as e:
        print(f"❌ Erreur Telegram : {e}")

def simulation_scan():
    """Simule des offres pour tester que tout le circuit fonctionne."""
    return """
    - Mission A : Ingénieur Structure Béton (Freelance) - Paris.
    - Mission B : Chef de chantier (CDI) - Lyon.
    - Mission C : Calculateur Charpente Métallique - Bordeaux.
    """

async def executer_radar():
    print("🔎 Scan en cours...")
    offres_brutes = simulation_scan()

    prompt = f"""
    Analyse ces offres : {offres_brutes}
    Garde uniquement celles liées au Génie Civil ou aux Structures.
    Fais un résumé très court par offre.
    Si rien ne correspond, réponds : RIEN.
    """

    try:
        response = model.generate_content(prompt)
        analyse = response.text

        if "RIEN" not in analyse.upper():
            await envoyer_alerte(analyse)
        else:
            print("📭 Aucune mission pertinente aujourd'hui.")
    except Exception as e:
        print(f"❌ Erreur Gemini : {e}")

if __name__ == "__main__":
    asyncio.run(executer_radar())