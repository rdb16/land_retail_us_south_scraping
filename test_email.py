from utils import send_email_with_attachment
import os
from dotenv import load_dotenv


if __name__ == "__main__":
    load_dotenv()

    sender_email = "raymond.de.bernis@gmail.com"  # Remplacez par votre adresse e-mail
    sender_password = os.getenv("sender_password") # Remplacez par votre mot de passe ou un mot de passe d'application
    recipient_email = "0607514708@free.fr"  # Remplacez par l'adresse e-mail du destinataire
    subject = "Fichier Excel en pièce jointe"
    body = "Veuillez trouver ci-joint le fichier Excel."
    file_path = "Results/duwest-scrape-25-09-2024.xlsx"  # Chemin vers le fichier Excel à envoyer

    send_email_with_attachment(sender_email, sender_password, recipient_email, subject, body, file_path)
