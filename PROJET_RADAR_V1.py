import os
import asyncio
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from telegram import Bot

# --- 1. CONFIGURATION DES ACCÈS ---
# Ces variables récupèrent les "Secrets" que tu as configurés sur GitHub
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Configuration de l'IA Gemini
genai.configure(api_key=GEMINI_API_KEY)

# --- 2. FONCTIONS DE RÉCUPÉRATION (LE SCAN) ---

def fetch_rekrute():
    """Scanne Rekrute pour le Génie Civil au Maroc"""
    url = "https://www.rekrute.com/offres-emploi-maroc.html?keyword=genie+civil"
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        # On extrait le texte principal pour l'analyse
        return "SOURCE REKRUTE:\n" + soup.get_text()[:3000]
    except Exception as e:
        return f"Erreur Rekrute: {e}\n"

def fetch_indeed():
    """Scanne Indeed Maroc pour le Génie Civil"""
    url = "https://ma.indeed.com/jobs?q=g%C3%A9nie+civil&l=Maroc"
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        return "SOURCE INDEED:\n" + soup.get_text()[:3000]
    except Exception as e:
        return f"Erreur Indeed: {e}\n"

def fetch_linkedin():
    """Scanne la page publique des jobs LinkedIn Maroc"""
    url = "https://www.linkedin.com/jobs/search/?keywords=G%C3%A9nie%20Civil&location=Morocco"
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        return "SOURCE LINKEDIN:\n" + soup.get_text()[:3000]
    except Exception as e:
        return f"Erreur LinkedIn: {e}\n"

# --- 3. LOGIQUE PRINCIPALE DU RADAR ---

async def run_radar():
    print("🚀 Démarrage du Radar Génie Civil...")
    
    # Étape A : Collecte des données brute
    data_brute = fetch_rekrute() + fetch_indeed() + fetch_linkedin()
    
    # Étape B : Analyse intelligente par Gemini
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        prompt = f"""
        Tu es un expert en recrutement BTP et Génie Civil au Maroc. 
        Voici des données brutes de sites d'emploi :
        {data_brute}
        
        TA MISSION :
        1. Identifie les offres sérieuses en Génie Civil (Ingénieur, Chef de projet, Bureau d'études, Travaux).
        2. Si tu trouves des offres : Donne le titre du Poste, la Ville, l'Entreprise et un mini-résumé.
        3. SI ET SEULEMENT SI aucune offre n'est pertinente, réponds UNIQUEMENT par le mot : RAS
        """
        
        response = model.generate_content(prompt)
        resultat_ia = response.text.strip()
    except Exception as e:
        resultat_ia = f"⚠️ Erreur lors de l'analyse IA : {e}"

    # Étape C : Envoi du message sur Telegram
    bot = Bot(token=TELEGRAM_TOKEN)
    
    if "RAS" in resultat_ia:
        message_final = "✅ **Radar Opérationnel** : RAS (Rien à signaler pour le Génie Civil à cette heure)."
    else:
        message_final = f"🏗️ **NOUVELLES OFFRES GÉNIE CIVIL** 🏗️\n\n{resultat_ia}"
    
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message_final, parse_mode='Markdown')
        print("✅ Message envoyé avec succès sur Telegram !")
    except Exception as e:
        print(f"❌ Erreur d'envoi Telegram : {e}")

# --- 4. LANCEMENT DU SCRIPT ---
if __name__ == "__main__":
    if not GEMINI_API_KEY or not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ ERREUR : Les Secrets ne sont pas détectés. Vérifie GitHub Settings.")
    else:
        asyncio.run(run_radar())