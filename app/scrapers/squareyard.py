import time
import json
import requests
from bs4 import BeautifulSoup
from app.utils.chrome_driver import get_chrome_driver

def get_lat_lon(details_url):
    headers = {
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/91.0.4472.124 Safari/537.36')
    }
    response = requests.get(details_url, headers=headers)
    if response.status_code != 200:
        print("Failed to retrieve the webpage:", details_url)
        return None, None

    sp = BeautifulSoup(response.text, 'html.parser')
    lat, lon = None, None
    ul = sp.find('ul', class_='nearLocation scrollBarHide')
    if ul:
        li = ul.find('li', class_='locatedLi')
        if li:
            lat = li.get('data-latitude')
            lon = li.get('data-longitude')
    return lat, lon

def scrape_squareyard(city: str, locality: str, page: int = 1):
    """Scrapes Squareyard property listings for given city and locality.
    Returns a slice of 10 items based on the page parameter.
    """
    # Build URL slug
    city_slug = city.lower().replace(" ", "-")
    locality_slug = locality.lower().replace(" ", "-")
    base_url = f"https://www.squareyards.com/sale/property-for-sale-in-{locality_slug}-{city_slug}"
    
    driver = get_chrome_driver()
    driver.get(base_url)
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    properties = []
    
    # Scrape clubListingsItem listings
    listings = soup.find_all('div', class_='clubListingsItem')
    for listing in listings:
        try:
            name = listing.find('a', class_='strong').get_text(strip=True)
        except AttributeError:
            name = None
        try:
            location = listing.find('div', class_='npDeveloperLocation').get_text(strip=True)
        except AttributeError:
            location = None
        try:
            type_name = listing.find('h2', class_='npListingLink').get_text(strip=True)
        except AttributeError:
            type_name = None
        try:
            price = listing.find('div', class_='npListingPrice').find('strong').get_text(strip=True)
        except AttributeError:
            price = None
        try:
            built_up_area = listing.find('li', class_='npListingInfo').find_all('span')[1].get_text(strip=True)
        except (AttributeError, IndexError):
            built_up_area = None
        try:
            possession_status = listing.find('li', class_='npListingInfo').find('span').get_text(strip=True)
        except AttributeError:
            possession_status = None
        try:
            description = listing.find('div', class_='npDescBox').find('p').get_text(strip=True)
        except AttributeError:
            description = None
        try:
            agent_name = listing.find('div', class_='npUserName').find('strong').get_text(strip=True)
        except AttributeError:
            agent_name = None
        try:
            img_tag = listing.find('img', class_='img-responsive')
            image_link = img_tag.get('src') or img_tag.get('data-src')
        except AttributeError:
            image_link = None
        try:
            details_link = listing.find('a', href=True)['href']
        except (AttributeError, TypeError):
            details_link = None
        properties.append({
            'name': name,
            'location': location,
            'type_name': type_name,
            'price': price,
            'built_up_area': built_up_area,
            'possession_status': possession_status,
            'description': description,
            'agent_name': agent_name,
            'image_link': image_link,
            'details_link': details_link
        })
    
    # Scrape npListingTile listings (scrollable listings)
    scrollable_listings = soup.find_all('div', class_='npListingTile')
    for listing in scrollable_listings:
        try:
            name = listing.find('h2', class_='npListingLink').get_text(strip=True)
        except AttributeError:
            name = None
        try:
            location = listing.find('div', class_='npListingUnit').find('span').get_text(strip=True)
        except AttributeError:
            location = None
        try:
            price = listing.find('div', class_='npListingPrice').find('strong').get_text(strip=True)
        except AttributeError:
            price = None
        try:
            built_up_area = listing.find('li', class_='npListingInfo').find_all('span')[1].get_text(strip=True)
        except (AttributeError, IndexError):
            built_up_area = None
        try:
            possession_status = listing.find('li', class_='npListingInfo').find('span').get_text(strip=True)
        except AttributeError:
            possession_status = None
        try:
            description = listing.find('div', class_='npDescBox').find('p').get_text(strip=True)
        except AttributeError:
            description = None
        try:
            agent_name = listing.find('div', class_='npUserName').find('strong').get_text(strip=True)
        except AttributeError:
            agent_name = None
        try:
            img_tag = listing.find('img', class_='img-responsive')
            image_link = img_tag.get('src') or img_tag.get('data-src')
        except AttributeError:
            image_link = None
        try:
            details_link = listing.find('ul', class_='npTagBox').get('onclick')
            details_link = details_link.split("'")[1] if details_link else None
        except (AttributeError, TypeError, IndexError):
            details_link = None
        properties.append({
            'name': name,
            'location': location,
            'price': price,
            'built_up_area': built_up_area,
            'possession_status': possession_status,
            'description': description,
            'agent_name': agent_name,
            'image_link': image_link,
            'details_link': details_link
        })
    
    driver.quit()
    
    # For each property that has a details_link, retrieve latitude and longitude
    for prop in properties:
        if prop.get('details_link'):
            lat, lon = get_lat_lon(prop['details_link'])
        else:
            lat, lon = None, None
        prop['latitude'] = lat
        prop['longitude'] = lon

    # Return only the slice for the given page (10 items per page)
    start = (page - 1) * 10
    end = page * 10
    return properties[start:end]
