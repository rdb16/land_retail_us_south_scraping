import json
import os
import subprocess
import time
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from utils import export_to_excell, send_email_with_attachment


# Utiliser curl pour télécharger la page
def download_page(url, out_file):
    try:
        # Télécharger le HTML avec wget
        command = ["curl", "-L", url, "-o", out_file]
        subprocess.run(command, check=True)
        print(f"Page downloaded successfully: {out_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error downloading page: {e}")


def scrape_json_from_html(file_path):
    # Lire le contenu du fichier HTML téléchargé
    with open(file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()
    # Parse le HTML avec BeautifulSoup
    # print(html_content)
    soup = BeautifulSoup(html_content, 'html.parser')
    # Trouver toutes le balise qui contient la var window.properties
    script_tagg = soup.find('script', class_='not-delay')
    script_text = script_tagg.string
    start = script_text.find('window.properties = ') + len('window.properties = ')
    end = script_text.find('];') + 1
    json_text = script_text[start:end].strip()
    data = json.loads(json_text)
    return data


def parse_json_data(properties):
    properties_list = []
    for property in properties:
        property_dict = {
            'title': property['primary_location']['title'],
            'address': property['primary_location']['location_text'],
            'url': property['url'],
            'acres_min': property['property_detail']['size_acres']['min'],
            'acres_max': property['property_detail']['size_acres']['Max'],
            'sqf_min': property['property_detail']['size_square_feet']['min'],
            'sqf_max': property['property_detail']['size_square_feet']['Max'],
            'latitude': property['primary_location']['map']['lat'],
            'longitude': property['primary_location']['map']['lng'],
            'contacts': property['broker']
        }
        # print(property_dict)
        properties_list.append(property_dict)
    return properties_list


if __name__ == "__main__":
    start_time = time.time()
    url = 'https://www.newquest.com/properties/find-a-property/?propertyType=Land&propertyType=Retail&deal_type=Sale'
    output_file = 'tmp/curl_page.html'
    # Télécharger la page HTML
    download_page(url, output_file)
    # # Analyser le fichier HTML téléchargé et extraire les données
    json_data = scrape_json_from_html(output_file)
    result_list = parse_json_data(json_data)
    nb_properties = len(result_list)
    print("Nb properties: ", nb_properties)
    filename, file_path, current_date = export_to_excell(result_list, "NewQuest")
    #
    # Supprimer le fichier temporaire après utilisation
    try:
        os.remove(output_file)
        print(f"Fichier temporaire supprimé : {output_file}")
    except OSError as e:
        print(f"Erreur lors de la suppression du fichier : {e}")

    end_time = time.time()
    duration = (end_time - start_time)
    print("durée totale en secondes: ", int(duration), "pour: ", nb_properties)
    body = f"Le scraping du broker Newquest au {current_date}, \nconcerne {nb_properties} terrains & retails à vendre.\nTemps d'exécution du scraping en secondes: {int(duration)}\nMerci de les consulter en fichier joint"

    load_dotenv()

    sender_email = os.getenv("sender_email")
    sender_password = os.getenv("sender_password")
    recipient_email = os.getenv("recipient")
    subject = "[Newquest-LandExcel en pièce jointe]"
    cc_email = os.getenv("cc_email")

    send_email_with_attachment(sender_email, sender_password, recipient_email, subject, body, file_path, cc_email)
