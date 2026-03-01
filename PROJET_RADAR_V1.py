import google.generativeai as genai
import os
import asyncio
from telegram import Bot

# --- CONFIGURATION DES APIS ---
# On utilise os.getenv pour récupérer les Secrets que tu as configurés sur GitHub
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Configuration de Google Gemini (Version stable forcée)
genai.configure(api_key=GEMINI_API_KEY, transport='rest')
model = genai.GenerativeModel('models/gemini-1.5-flash')
async def envoyer_alerte(message):
    """Envoie le message de l'IA sur ton Telegram."""
    bot = Bot(token=TELEGRAM_TOKEN)
    try:
        await bot.send_message(chat_id=CHAT_ID, text=f"🏗️ NOUVELLES OFFRES GÉNIE CIVIL 🏗️\n\n{message}")
        print("✅ Message envoyé sur Telegram !")
    except Exception as e:
        print(f"❌ Erreur Telegram : {e}")

def simulation_scan():
    """
    Simule des offres pour tester que tout le circuit fonctionne.
    Plus tard, on remplacera cela par un vrai scan de sites web.
    """
    return """
    - Mission A : Ingénieur Structure Béton (Freelance) - Paris.
    - Mission B : Chef de chantier (CDI) - Lyon.
    - Mission C : Calculateur Charpente Métallique - Bordeaux.
    - Mission D : Vendeur de fleurs - Nice (Ne devrait pas être retenu).
    """
async def executer_radar():
    print("🔎 Scan en cours...")
    offres_brutes = simulation_scan()

    prompt = f"""
    Analyse ces offres : {offres_brutes}
    Garde uniquement celles liées au Génie Civil ou aux Structures.
    Fais un résumé très court par offre (Poste et Ville).
    Si rien ne correspond, réponds : RIEN.
    """

    try:
        # Configuration du modèle validé par ton diagnostic
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        
        response = model.generate_content(prompt)
        analyse = response.text

        if "RIEN" not in analyse.upper():
            await envoyer_alerte(analyse)
        else:
            print("📭 Aucune mission pertinente aujourd'hui.")
            
    except Exception as e:
        error_msg = f"⚠️ Erreur lors de l'analyse IA : {str(e)}"
        print(error_msg)
        # On envoie l'erreur sur Telegram pour être alerté immédiatement
        await envoyer_alerte(error_msg)

if __name__ == "__main__":
    # Lancement du script en mode asynchrone
    asyncio.run(executer_radar())