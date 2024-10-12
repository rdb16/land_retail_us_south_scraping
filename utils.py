import time
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import os
import openpyxl


def export_to_excell(data: list, broker):
    broker = broker.replace(' ', '_')
    df = pd.DataFrame(data)
    current_date = time.strftime("%d-%m-%Y")
    filename = f"{broker}-scrape-{current_date}.xlsx"
    file_path_export = f"Results/{broker}-scrape-{current_date}.xlsx"
    df.to_excel(file_path_export)
    print(f"Les données ont été exportées avec succès dans le fichier {file_path_export}")
    return filename, file_path_export, current_date


def send_email_with_attachment(sender_email, sender_password, recipient_email, subject, body, file_path, cc_email=None):
    # Créer le message de l'e-mail
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    if cc_email:
        msg['Cc'] = cc_email

    # Ajouter le corps de l'e-mail
    msg.attach(MIMEText(body, 'plain'))

    # Ajouter la pièce jointe (le fichier Excel)
    filename = os.path.basename(file_path)
    attachment = MIMEBase('application', 'octet-stream')
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Le fichier {file_path} n'existe pas.")

        with open(file_path, 'rb') as file:
            attachment.set_payload(file.read())

            encoders.encode_base64(attachment)
            attachment.add_header('Content-Disposition', f'attachment; filename={filename}')
            msg.attach(attachment)
    except FileNotFoundError as e:
        print(f"Erreur : {e}")
        return  # Arrêter la fonction si le fichier n'est pas trouvé

    except Exception as e:
        print(f"Erreur lors du traitement de la pièce jointe : {e}")
        return  # Arrêter la fonction si une autre erreur survient

    # Connexion au serveur SMTP
    server = None
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)  # Utilisez le serveur SMTP de votre choix
        server.starttls()  # Utiliser le TLS pour sécuriser la connexion
        server.login(sender_email, sender_password)

        # Envoyer l'e-mail
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        print(f"E-mail envoyé avec succès à {recipient_email}")

    except Exception as e:
        print(f"Erreur lors de l'envoi de l'e-mail : {e}")

    finally:
        # Fermer la connexion au serveur SMTP
        server.quit()
