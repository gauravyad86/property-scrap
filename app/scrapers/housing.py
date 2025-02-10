import time
import json
import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
from app.utils.chrome_driver import get_chrome_driver

def generate_housing_url(city, locality):
    city_encoded = quote(city.replace(" ", "_").lower())
    locality_encoded = quote(locality.replace(" ", "_").lower())
    return f"https://housing.com/in/buy/{city_encoded}/{locality_encoded}"

def extract_lat_lon_second_image(url):
    response = requests.get(url)
    if response.status_code != 200:
        return None, None, None

    soup = BeautifulSoup(response.text, 'html.parser')
    json_script = soup.find("script", {"type": "application/ld+json"})
    latitude = longitude = None
    if json_script:
        try:
            json_data = json.loads(json_script.string)
            if isinstance(json_data, list):
                for item in json_data:
                    if "@type" in item and "geo" in item:
                        latitude = item["geo"].get("latitude")
                        longitude = item["geo"].get("longitude")
                        break
            elif isinstance(json_data, dict):
                if "geo" in json_data:
                    latitude = json_data["geo"].get("latitude")
                    longitude = json_data["geo"].get("longitude")
        except Exception:
            pass

    second_image = None
    gallery_section = soup.find("div", {"data-q": "gallery"})
    if gallery_section:
        all_images = gallery_section.find_all("img", src=True)
        if len(all_images) > 1:
            second_image = all_images[1]["src"]
            if second_image.startswith("//"):
                second_image = "https:" + second_image

    return latitude, longitude, second_image

def scrape_housing(city: str, locality: str, page: int = 1):
    """Scrapes Housing.com listings for given city and locality.
    Returns 10 properties based on the requested page.
    """
    url = generate_housing_url(city, locality)
    driver = get_chrome_driver()
    driver.get(url)
    SCROLL_PAUSE_TIME = 2

    # Scroll a few times to load listings; adjust the count if necessary.
    for _ in range(10):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)

    # Force images to load if they are lazy-loaded.
    driver.execute_script("""
        let images = document.querySelectorAll('img');
        images.forEach(img => {
            if (img.getAttribute('data-src')) {
                img.setAttribute('src', img.getAttribute('data-src'));
            }
        });
    """)
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    properties = []
    
    for card in soup.find_all('article', {'data-testid': 'card-container'}):
        # Stop if we already have enough for the requested page
        if len(properties) >= page * 10:
            break
        name = card.find('h2', class_='T_4d93cd45').text if card.find('h2', class_='T_4d93cd45') else None
        emi_starts = card.find('span', class_='_9jtlke').text if card.find('span', class_='_9jtlke') else None
        price = card.find('div', {'data-testid': 'priceid'}).text if card.find('div', {'data-testid': 'priceid'}) else None
        by = card.find('div', class_='_c81fwx').text if card.find('div', class_='_c81fwx') else None
        link = card.find('a', {'data-q': 'title'}, href=True)
        link = link['href'] if link else None
        possession_date = None
        avg_price = None
        possession_status = None
        # You can add logic to extract possession_date, avg_price, etc. if needed.
        
        full_link = f"https://housing.com{link}" if link else None
        latitude, longitude, image = extract_lat_lon_second_image(full_link) if full_link else (None, None, None)
        if name and link:
            property_details = {
                'name': name,
                'emi_starts': emi_starts,
                'price': price,
                'by': by,
                'link': full_link,
                'possession_date': possession_date,
                'avg_price': avg_price,
                'possession_status': possession_status,
                'latitude': latitude,
                'longitude': longitude,
                'image': image
            }
            properties.append(property_details)
    
    driver.quit()
    # Return only the slice corresponding to the page
    start = (page - 1) * 10
    end = page * 10
    return properties[start:end]
