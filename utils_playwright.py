import asyncio
from playwright.async_api import async_playwright
import re
import os
import time


async def save_page(url_page, out_file):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Accéder à l'URL cible
        await page.goto(url_page)

        # Attendre que le contenu soit chargé (tu peux ajuster en fonction des éléments spécifiques)
        await page.wait_for_load_state("networkidle")
        time.sleep(3)
        content = await page.content()

        # Créer le répertoire tmp s'il n'existe pas
        if not os.path.exists('tmp'):
            os.makedirs('tmp')

        # Enregistrer le contenu HTML dans le fichier
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(content)

        # Fermer le navigateur
        await browser.close()


async def filter_requests(url, filter_list):
    async with async_playwright() as p:
        # Lancer le navigateur en mode headless
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        # Liste pour capturer les requêtes JS
        filtered_req = []

        # Intercepter toutes les requêtes
        async def log_request(request):
            low_url = request.url.lower()  # Convertir l'URL en minuscules pour éviter les problèmes de casse
            if filter_list[0] in low_url and filter_list[1] in low_url:
                filtered_req.append(request.url)

        page.on('request', log_request)

        # Aller à la page cible
        await page.goto(url)

        # Fermer le navigateur
        await browser.close()
        return filtered_req



