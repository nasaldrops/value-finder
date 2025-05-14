# daft_analyzer.py

import requests
from bs4 import BeautifulSoup
import json
import time
import re # For case-insensitive keyword matching

# Base URL for Daft.ie searches
DAFT_BASE_URL = "https://www.daft.ie"

# Headers to mimic a browser visit
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
}

# --- Analysis Keywords (from daft_scraping_strategy.md) ---
FIXER_UPPER_KEYWORDS = [
    "fixer-upper", "fixer upper", "needs renovation", "requires modernization", "tlc", 
    "tender loving care", "handyman special", "renovation project", 
    "refurbishment opportunity", "blank canvas", "in need of updating", 
    "sold as seen", "shell and core"
]

LAND_DEVELOPMENT_KEYWORDS = [
    "site for sale", "land for sale", "development potential", "development opportunity", 
    "planning permission", "fpp", "full planning permission", "outline planning permission", 
    "opp", "zoned residential", "zoned commercial", "subject to planning permission", "site"
]

QUICK_SALE_KEYWORDS = [
    "motivated seller", "priced to sell", "quick sale required", "open to offers", 
    "must be sold", "reduced for quick sale", "auction", "back on market", 
    "chain free", "vacant possession", "price reduced", "significant reduction"
]
# --- End Analysis Keywords ---

def analyze_property_description(property_data):
    """Analyzes property title and description for keywords and adds tags."""
    if not property_data or not isinstance(property_data, dict):
        return property_data

    description = property_data.get("description", "").lower()
    title = property_data.get("title", "").lower()
    text_to_analyze = description + " " + title
    
    property_data["analysis_tags"] = []

    for keyword in FIXER_UPPER_KEYWORDS:
        if re.search(r'\b' + re.escape(keyword) + r'\b', text_to_analyze):
            if "Tag: Fixer-Upper" not in property_data["analysis_tags"]:
                property_data["analysis_tags"].append("Tag: Fixer-Upper")
            # No need to break, a property might have multiple relevant keywords for the same tag

    for keyword in LAND_DEVELOPMENT_KEYWORDS:
        if re.search(r'\b' + re.escape(keyword) + r'\b', text_to_analyze):
            if "Tag: Development Land" not in property_data["analysis_tags"]:
                property_data["analysis_tags"].append("Tag: Development Land")
    # Also check property type if available from scrape (e.g. if type is 'Site')
    if "site" in property_data.get("property_type", "").lower() and "Tag: Development Land" not in property_data["analysis_tags"]:
         property_data["analysis_tags"].append("Tag: Development Land")

    for keyword in QUICK_SALE_KEYWORDS:
        if re.search(r'\b' + re.escape(keyword) + r'\b', text_to_analyze):
            if "Tag: Potential Quick Sale" not in property_data["analysis_tags"]:
                property_data["analysis_tags"].append("Tag: Potential Quick Sale")
    
    if not property_data["analysis_tags"]:
        property_data["analysis_tags"].append("Tag: Standard Listing")
        
    return property_data

def construct_search_url(filters):
    """Constructs a Daft.ie search URL based on the provided filters."""
    location = filters.get("location", "ireland")
    keywords = filters.get("keywords", "")
    # property_type_filter = filters.get("propertyType", "") # e.g. "houses", "apartments", "sites"
    min_price = filters.get("minPrice", "")
    max_price = filters.get("maxPrice", "")
    # min_beds = filters.get("minBeds", "")
    # max_beds = filters.get("maxBeds", "")

    # Daft.ie URL structure for sales: /property-for-sale/{county}/{area}/{sub-area}?
    # Parameters: salePrice_from, salePrice_to, keywords, numBeds_from, numBeds_to, propertyType (e.g. houses, apartments, sites)
    # Location needs careful handling. For simplicity, we'll use a general location path.
    # A robust solution would map user input to Daft's specific location slugs.
    
    location_slug = location.lower().replace(", ", "/").replace(" ", "-")
    if location_slug == "ireland": # Special case for nationwide search
        base_search_path = "/property-for-sale/ireland"
    else:
        base_search_path = f"/property-for-sale/{location_slug}"

    url_parts = [f"{DAFT_BASE_URL}{base_search_path}"]
    query_params = []

    if keywords:
        query_params.append(f"keywords={keywords.replace(' ', '+')}")
    if min_price:
        query_params.append(f"salePrice_from={min_price}")
    if max_price:
        query_params.append(f"salePrice_to={max_price}")
    # Add other filters like propertyType, numBeds_from, numBeds_to as per Daft's structure
    # e.g., if property_type_filter: query_params.append(f"propertyType={property_type_filter}")
    
    if query_params:
        url_parts.append("?" + "&".join(query_params))
        
    return "".join(url_parts)

def scrape_property_details(property_url):
    """Scrapes detailed information from a single property page."""
    print(f"Scraping details from: {property_url}")
    time.sleep(1) 
    try:
        response = requests.get(property_url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        details = {
            "url": property_url,
            "title": "",
            "price": "",
            "description": "",
            "ber": "",
            "features": [],
            "property_type": "",
            "date_listed": "", 
            "analysis_tags": [] 
        }

        # Selectors need to be verified and updated by inspecting Daft.ie's live HTML.
        # These are common patterns but are likely to change.
        title_tag = soup.find('h1', {'data-testid': 'title-block'}) 
        if title_tag: details["title"] = title_tag.get_text(strip=True)
        else: # Fallback
            title_tag = soup.find('h1')
            if title_tag: details["title"] = title_tag.get_text(strip=True)

        price_tag = soup.find('strong', {'data-testid': 'price'}) 
        if price_tag: details["price"] = price_tag.get_text(strip=True)
        else: # Fallback
            price_tag = soup.find('span', class_=re.compile(r'price', re.I))
            if price_tag: details["price"] = price_tag.get_text(strip=True)

        description_tag = soup.find('div', {'data-testid': 'description'}) 
        if description_tag: details["description"] = description_tag.get_text(separator='\n', strip=True)
        
        ber_tag = soup.find('span', {'data-testid': 'ber-rating'}) 
        if ber_tag: details["ber"] = ber_tag.get_text(strip=True)
        else: # Fallback for BER, often near 'Energy Rating'
            ber_parent = soup.find(string=re.compile(r'BER Details', re.I))
            if ber_parent:
                ber_info = ber_parent.find_next_sibling()
                if ber_info : details["ber"] = ber_info.get_text(strip=True).split("\n")[0]
        
        # Property Type (often near title or in a summary section)
        ptype_tag = soup.find('p', {'data-testid': 'property-type'})
        if ptype_tag: details["property_type"] = ptype_tag.get_text(strip=True)

        # Features (often in a <ul> or specific divs)
        features_section = soup.find('div', {'data-testid': 'features'}) 
        if features_section:
            features_list = features_section.find_all('li') # Or 'p' or 'span' depending on structure
            if features_list:
                details["features"] = [f.get_text(strip=True) for f in features_list if f.get_text(strip=True)]
        
        print(f"Successfully scraped: {details['title'][:50]}...")
        # Analyze the scraped data before returning
        details = analyze_property_description(details)
        return details
    except requests.exceptions.RequestException as e:
        print(f"Error scraping {property_url}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while scraping {property_url}: {e}")
        return None

def search_daft_properties(filters):
    """Searches Daft.ie based on filters and scrapes results."""
    search_url = construct_search_url(filters)
    print(f"Constructed search URL: {search_url}")
    
    properties = []
    page_num = 1
    # Max pages should ideally be configurable or removed for full search
    max_pages_to_scrape = filters.get("max_pages", 1) # Default to 1 page for testing, can be overridden

    current_url = search_url 

    while page_num <= max_pages_to_scrape:
        print(f"Scraping search results page: {page_num} from {current_url}")
        time.sleep(2) 
        try:
            response = requests.get(current_url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Selector for property cards on search results page (NEEDS VERIFICATION)
            # Daft.ie uses `data-testid` attributes extensively.
            listing_cards = soup.find_all('li', {'data-testid': re.compile(r'search-result-card_')})
            if not listing_cards: # Fallback to a more generic structure if the above fails
                listing_cards = soup.find_all('div', class_=re.compile(r'Card__Content'))
            
            if not listing_cards:
                print("No listing cards found on page. Scraper might need updating or page structure changed.")
                break

            print(f"Found {len(listing_cards)} listings on page {page_num}.")

            for card_item in listing_cards: # Renamed to avoid conflict
                link_tag = card_item.find('a', href=True)
                property_page_url = None
                if link_tag and link_tag['href']:
                    if link_tag['href'].startswith('/'):
                        property_page_url = DAFT_BASE_URL + link_tag['href']
                    elif link_tag['href'].startswith('http'):
                        property_page_url = link_tag['href']
                
                if property_page_url:
                    # Avoid re-scraping if URL already processed (can happen with complex layouts)
                    if not any(p['url'] == property_page_url for p in properties):
                        detailed_info = scrape_property_details(property_page_url)
                        if detailed_info:
                            properties.append(detailed_info)
                    else:
                        print(f"Skipping already processed URL: {property_page_url}")
            
            # Pagination logic (NEEDS VERIFICATION)
            next_page_tag = soup.find('a', {'data-testid': 'next-button', 'aria-label': 'Next page'})
            if not next_page_tag: # Fallback
                 next_page_tag = soup.find('li', class_='next')
                 if next_page_tag: next_page_tag = next_page_tag.find('a', href=True)

            if next_page_tag and next_page_tag.get('href'):
                next_page_href = next_page_tag['href']
                if next_page_href.startswith('/'):
                    current_url = DAFT_BASE_URL + next_page_href
                elif next_page_href.startswith('http'):
                    current_url = next_page_href
                else:
                    print("Next page link found, but format is not absolute or recognized. Stopping pagination.")
                    break
                page_num += 1
            else:
                print("No 'next page' link found or end of results.")
                break

        except requests.exceptions.RequestException as e:
            print(f"Error fetching search results page {page_num}: {e}")
            break
        except Exception as e:
            print(f"An unexpected error occurred on search page {page_num}: {e}")
            break
            
    return properties

if __name__ == '__main__':
    print("Testing Daft.ie scraper and analyzer...")
    
    # Test 1: Single Property Scrape and Analysis
    # Use a known, potentially complex URL. Replace with a current one if this is outdated.
    test_property_url = "https://www.daft.ie/for-sale/detached-house-ballintages-ford-wexford/5600483" 
    print(f"\n--- Test 1: Scraping and Analyzing Single Property --- \nURL: {test_property_url}")
    single_result = scrape_property_details(test_property_url)
    if single_result:
        print("--- Single Property Result (Analyzed) ---")
        print(json.dumps(single_result, indent=2))
    else:
        print("Failed to scrape single property.")

    # Test 2: Search multiple properties (limited pages for testing)
    print("\n--- Test 2: Searching and Analyzing Multiple Properties ---")
    test_filters_multi = {
        "location": "Wexford", 
        "keywords": "detached", # Broad keyword for more results
        "maxPrice": "500000",
        "max_pages": 1 # Limit to 1 page of results for this test
    }
    multi_results = search_daft_properties(test_filters_multi)
    print(f"\nFound and analyzed {len(multi_results)} properties matching filters (max {test_filters_multi['max_pages']} page(s)).")
    if multi_results:
        print("--- Multi-Property Results (Analyzed) Sample ---")
        for i, prop in enumerate(multi_results[:2]): # Print sample of 2
            print(f"--- Property {i+1} ---")
            print(json.dumps(prop, indent=2))
    else:
        print("No properties found or error during multi-property search.")

    # Test 3: Example with fixer-upper keywords
    print("\n--- Test 3: Searching for Fixer-Uppers ---")
    test_filters_fixer = {
        "location": "Cork", 
        "keywords": "fixer upper",
        "max_pages": 1
    }
    fixer_results = search_daft_properties(test_filters_fixer)
    print(f"\nFound and analyzed {len(fixer_results)} 'fixer upper' properties in {test_filters_fixer['location']} (max {test_filters_fixer['max_pages']} page(s)).")
    if fixer_results:
        print("--- Fixer-Upper Results Sample ---")
        for i, prop in enumerate(fixer_results[:2]):
            print(f"--- Property {i+1} ---")
            print(json.dumps(prop, indent=2))
    else:
        print("No 'fixer upper' properties found or error during search.")

