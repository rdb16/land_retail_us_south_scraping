import os
import subprocess
import time
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from utils import export_to_excell, send_email_with_attachment


# Utiliser wget pour télécharger la page
def download_page(url, output_file):
    try:
        # Télécharger le HTML avec wget
        command = ["wget", "-O", output_file, url]
        subprocess.run(command, check=True)
        print(f"Page downloaded successfully: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error downloading page: {e}")


# Fonction pour extraire les informations de chaque section HTML
def extract_listing_data(modal, details_soup, modal_soup):
    # Extraction des informations demandées
    data = {}

    # Extraire les attributs data-lat, data-lng et data-url directement depuis la balise
    data['latitude'] = modal.get('data-lat')
    data['longitude'] = modal.get('data-lng')
    data['url'] = "https://theblueoxgroup.com/" + modal.get('data-url')

    # Pré-titre, titre, adresse, code postal, prix
    pretitle = details_soup.find('p', class_='pretitle')
    title = details_soup.find('p', class_='title')
    address = details_soup.find('p', class_='csz')
    price = details_soup.find('p', class_='price')

    data['pretitle'] = pretitle.get_text(strip=True) if pretitle else None
    data['title'] = title.get_text(strip=True) if title else None
    data['address'] = address.get_text(strip=True) if address else None
    data['price'] = price.get_text(strip=True) if price else None

    # Description - concaténation du contenu des balises <p> et <ul> du modal
    description_parts = []

    # Ajout du texte des <p> dans le modal
    for p_tag in modal_soup.find_all('p'):
        description_parts.append(p_tag.get_text(strip=True))

    # Ajout du texte des <li> (liste) dans le modal
    for li_tag in modal_soup.find_all('li'):
        description_parts.append(li_tag.get_text(strip=True))

    # Concaténer tous les morceaux de la description
    data['description'] = ' '.join(description_parts)

    return data


# Fonction principale pour traiter la page téléchargée avec BeautifulSoup
def scrape_listings_from_html(file_path):
    listings_data = []

    # Lire le contenu du fichier HTML téléchargé
    with open(file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()
    # print(html_content)
    # Parse le HTML avec BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    # print(soup.prettify())
    # Trouver toutes les balises .bucket.jbmodal
    modals = soup.find_all('div', class_=['bucket', 'jbmodal'])
    print(f"Nombre d'affaires trouvées : {len(modals)}")

    # Boucle à travers chaque modal pour extraire les données
    for modal in modals:
        # Extraire les détails associés
        details_div = modal.find('div', class_='details')
        details_soup = BeautifulSoup(str(details_div), 'html.parser') if details_div else None

        # Récupérer le contenu de la balise modale associée (jbmodal-listing-X)
        modal_id = modal.get('data-jbmodal-html')
        modal_content_div = soup.find('div', id=modal_id)
        modal_soup = BeautifulSoup(str(modal_content_div), 'html.parser') if modal_content_div else None

        # Extraire les données
        data = extract_listing_data(modal, details_soup, modal_soup)
        listings_data.append(data)

    return listings_data

if __name__ == "__main__":
    start_time = time.time()
    url = 'https://theblueoxgroup.com/listings/sale/'
    output_file = 'listing_page.html'
    # Télécharger la page HTML
    download_page(url, output_file)

    # Analyser le fichier HTML téléchargé et extraire les données
    result_list = scrape_listings_from_html(output_file)
    nb_properties = len(result_list)
    filename, file_path, current_date = export_to_excell(result_list, "Blue-ox")

    # Supprimer le fichier temporaire après utilisation
    try:
        os.remove(output_file)
        print(f"Fichier temporaire supprimé : {output_file}")
    except OSError as e:
        print(f"Erreur lors de la suppression du fichier : {e}")

    end_time = time.time()
    duration = (end_time - start_time)
    print("durée totale en secondes: ", int(duration), "pour: ", nb_properties )
    body = f"Le scraping du broker Blue-ox au {current_date}, \nconcerne {nb_properties} terrains ou bâtiments à vendre.\nMerci de les consulter en fichier joint"

    load_dotenv()

    sender_email = os.getenv("sender_email")
    sender_password = os.getenv("sender_password")
    recipient_email = os.getenv("recipient")
    subject = "[Blue-ox Excel en pièce jointe]"
    cc_email = os.getenv("cc_email")

    send_email_with_attachment(sender_email, sender_password, recipient_email, subject, body, file_path, cc_email)



