import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from utils import send_email_with_attachment, export_to_excell


def scrape_page(local_driver):
    deals_data = []
    deals = local_driver.find_elements(By.CSS_SELECTOR, "div.col-md-6.col-12.mb-3")
    print("on a trouvé sur cette page: ", len(deals))

    for deal in deals:
        outer_html = deal.get_attribute("outerHTML")
        soup = BeautifulSoup(outer_html, "html.parser")
        # Extraire les informations
        detail_url = soup.find("a", href=True)["href"]
        address = soup.select_one("h5.mb-0.text-truncate.plugin-primary-color.font-weight-bold").get_text(strip=True)
        zip_code = soup.select_one("div.text-truncate").get_text(strip=True)
        table_rows = soup.select("table.mt-2.small tr")
        if len(table_rows) >= 3:
            price = table_rows[0].get_text(strip=True)
            built_area = table_rows[1].get_text(strip=True)
            property_type = table_rows[2].get_text(strip=True)
        else:
            price = built_area = property_type = "N/A"
        # Stocker les données
        deal_data = {
            "Detail URL and contact page": detail_url,
            "Address": address,
            "Zip_code": zip_code,
            "Price": price,
            "Built sqft or acres": built_area,
            "Property Type": property_type
        }
        deals_data.append(deal_data)
    return deals_data


if __name__ == "__main__":
    start_time = time.time()
    load_dotenv()
    site_url = "https://junctionusa.com/listings/"

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    service = Service('drivers/chromedriver-mac-arm64/chromedriver')  # Remplacez par le chemin de votre chromedriver
    driver = webdriver.Chrome(service=service, options=chrome_options)
    # wait = WebDriverWait(driver, 5)
    try:
        driver.get(site_url)
        time.sleep(3)
        # recherche de l'iframe
        iframe_element = driver.find_element(By.CSS_SELECTOR, "div#buildout iframe")
        iframe_url = iframe_element.get_attribute("src")
        print("URL: ", iframe_url)
        driver.get(iframe_url)
        time.sleep(3)

        all_sale_deals = []
        # Récupérer tous les boutons de pagination pour obtenir leur nombre
        pagination_buttons = driver.find_elements(By.CSS_SELECTOR, "div.js-paginate-btn.paginate-button.clickable")
        time.sleep(3)
        total_pages = len(pagination_buttons)
        print("total pages: ", total_pages)

        for page_index in range(total_pages):
            # Rafraîchir la liste des boutons de pagination à chaque fois (ils peuvent changer)
            pagination_buttons = driver.find_elements(By.CSS_SELECTOR,
                                                      "div.js-paginate-btn.paginate-button.clickable")

            # Cliquer sur le bouton de pagination correspondant
            pagination_buttons[page_index].click()
            time.sleep(3)  # Attendre que la nouvelle page soit chargée

            # Scraper les propriétés de la page actuelle
            page_properties = scrape_page(driver)
            all_sale_deals.extend(page_properties)

    finally:
        driver.quit()

    nb_properties = len(all_sale_deals)
    filename, file_path, current_date = export_to_excell(all_sale_deals, "Junction_USA")

    end_time = time.time()
    duration = (end_time - start_time)
    print("durée totale en secondes: ", int(duration), "pour: ", nb_properties)
    body = f"Le scraping du broker Junction USA au {current_date}, \nconcerne {nb_properties} terrains ou bâtiments à vendre.\nMerci de les consulter en fichier joint"

    sender_email = os.getenv("sender_email")
    sender_password = os.getenv("sender_password")
    recipient_email = os.getenv("recipient")
    subject = "[Junction usa Excel en pièce jointe]"
    cc_email = os.getenv("cc_email")

    send_email_with_attachment(sender_email, sender_password, recipient_email, subject, body, file_path, cc_email)
