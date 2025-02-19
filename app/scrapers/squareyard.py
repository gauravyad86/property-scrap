import time
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from app.utils.chrome_driver import get_chrome_driver

def get_lat_lon(details_url):
    headers = {
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/91.0.4472.124 Safari/537.36')
    }
    response = requests.get(details_url, headers=headers)
    if response.status_code != 200:
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

def scrape_squareyard(city: str, locality: str):
    desired_count = 500
    properties = []
    current_site_page = 1
    while len(properties) < desired_count:
        city_slug = city.lower().replace(" ", "-")
        locality_slug = locality.lower().replace(" ", "-")
        base_url = f"https://www.squareyards.com/sale/property-for-sale-in-{locality_slug}-{city_slug}"
        url = base_url if current_site_page == 1 else f"{base_url}?page={current_site_page}"
        driver = get_chrome_driver()
        driver.get(url)
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        page_properties = []
        listings = soup.find_all('div', class_='clubListingsItem')
        for listing in listings:
            name_tag = listing.find('a', class_='strong')
            name = name_tag.get_text(strip=True) if name_tag else None
            location_tag = listing.find('div', class_='npDeveloperLocation')
            location = location_tag.get_text(strip=True) if location_tag else None
            type_tag = listing.find('h2', class_='npListingLink')
            type_name = type_tag.get_text(strip=True) if type_tag else None
            price_tag = listing.find('div', class_='npListingPrice')
            price = price_tag.find('strong').get_text(strip=True) if price_tag and price_tag.find('strong') else None
            built_up_tag = listing.find('li', class_='npListingInfo')
            built_up_area = built_up_tag.find_all('span')[1].get_text(strip=True) if built_up_tag and len(built_up_tag.find_all('span')) > 1 else None
            possession_tag = listing.find('li', class_='npListingInfo')
            possession_status = possession_tag.find('span').get_text(strip=True) if possession_tag and possession_tag.find('span') else None
            desc_tag = listing.find('div', class_='npDescBox')
            description = desc_tag.find('p').get_text(strip=True) if desc_tag and desc_tag.find('p') else None
            agent_tag = listing.find('div', class_='npUserName')
            agent_name = agent_tag.find('strong').get_text(strip=True) if agent_tag and agent_tag.find('strong') else None
            img_tag = listing.find('img', class_='img-responsive')
            image_link = (img_tag.get('src') or img_tag.get('data-src')) if img_tag else None
            details_link_tag = listing.find('a', href=True)
            details_link = details_link_tag['href'] if details_link_tag else None
            listing_obj = {
                'city': city,
                'locality': locality,
                'name': name,
                'address': location,
                'link': details_link,
                'price': price,
                'perSqftPrice': None,
                'emi': None,
                'builtUp': built_up_area,
                'facing': None,
                'apartmentType': type_name,
                'bathrooms': None,
                'parking': None,
                'image': [image_link] if image_link else None,
                'latitude': None,
                'longitude': None,
                'possessionStatus': possession_status,
                'possessionDate': None,
                'agentName': agent_name,
                'description': description,
                'source': "squareyard",
                'createdAt': datetime.now().isoformat(),
                'updatedAt': datetime.now().isoformat()
            }
            page_properties.append(listing_obj)
        scrollable_listings = soup.find_all('div', class_='npListingTile')
        for listing in scrollable_listings:
            name_tag = listing.find('h2', class_='npListingLink')
            name = name_tag.get_text(strip=True) if name_tag else None
            location_tag = listing.find('div', class_='npListingUnit')
            location = location_tag.find('span').get_text(strip=True) if location_tag and location_tag.find('span') else None
            price_tag = listing.find('div', class_='npListingPrice')
            price = price_tag.find('strong').get_text(strip=True) if price_tag and price_tag.find('strong') else None
            built_up_tag = listing.find('li', class_='npListingInfo')
            built_up_area = built_up_tag.find_all('span')[1].get_text(strip=True) if built_up_tag and len(built_up_tag.find_all('span')) > 1 else None
            possession_tag = listing.find('li', class_='npListingInfo')
            possession_status = possession_tag.find('span').get_text(strip=True) if possession_tag and possession_tag.find('span') else None
            desc_tag = listing.find('div', class_='npDescBox')
            description = desc_tag.find('p').get_text(strip=True) if desc_tag and desc_tag.find('p') else None
            agent_tag = listing.find('div', class_='npUserName')
            agent_name = agent_tag.find('strong').get_text(strip=True) if agent_tag and agent_tag.find('strong') else None
            img_tag = listing.find('img', class_='img-responsive')
            image_link = (img_tag.get('src') or img_tag.get('data-src')) if img_tag else None
            details_link = None
            onclick_attr = listing.find('ul', class_='npTagBox')
            if onclick_attr:
                onclick_value = onclick_attr.get('onclick')
                if onclick_value:
                    parts = onclick_value.split("'")
                    if len(parts) > 1:
                        details_link = parts[1]
            listing_obj = {
                'city': city,
                'locality': locality,
                'name': name,
                'address': location,
                'link': details_link,
                'price': price,
                'perSqftPrice': None,
                'emi': None,
                'builtUp': built_up_area,
                'facing': None,
                'apartmentType': None,
                'bathrooms': None,
                'parking': None,
                'image': [image_link] if image_link else None,
                'latitude': None,
                'longitude': None,
                'possessionStatus': possession_status,
                'possessionDate': None,
                'agentName': agent_name,
                'description': description,
                'source': "squareyard",
                'createdAt': datetime.now().isoformat(),
                'updatedAt': datetime.now().isoformat()
            }
            page_properties.append(listing_obj)
        driver.quit()
        for prop in page_properties:
            if prop.get('link'):
                lat, lon = get_lat_lon(prop['link'])
            else:
                lat, lon = None, None
            prop['latitude'] = lat
            prop['longitude'] = lon
        if not page_properties:
            break
        properties.extend(page_properties)
        current_site_page += 1
    return properties[:desired_count]
