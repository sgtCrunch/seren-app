import requests
from random import choice, randint
from keys import Yelp_API_Key, IP_KEY
from ipinfo import getHandler
from geopy import distance
from urllib.parse import quote

# Yelp API constants
API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'  # Business ID will come after slash.
SEARCH_LIMIT = 50

def get_user_location(ip):
    """Use user IP to get user location lat and lon"""

    try:
        handler = getHandler(access_token=IP_KEY)
        details = handler.getDetails(ip_address=ip)
        print(details)
        return details.latitude, details.longitude
    except Exception as e:
        print('location was not found')
        return "Location not found"

def query_destinations(lat, lon):
    """Return a set of destinations from YELP api near user's location"""

    
    url = '{0}{1}'.format(API_HOST, SEARCH_PATH)
    
    headers = {
        'Authorization': 'Bearer %s' % Yelp_API_Key,
    }

    url_params = {
        'term': choice(['dinner', 'drink', 'fun'])+" "+choice(['good', 'bad', 'okay']),
        'latitude': lat,
        'longitude': lon,
        'sort_by': 'distance',
        'open_now': True,
        'limit': SEARCH_LIMIT
    }
    try:
        response = requests.request('GET', url, headers=headers, params=url_params)
    except Exception as e:
        raise e
    
    return response.json().get('businesses')

def request_destination_info(id):
    """Take business ID and request from Yelp its details"""

    url = '{0}{1}'.format(API_HOST, quote((BUSINESS_PATH+id).encode('utf8')))
    headers = {
        'Authorization': 'Bearer %s' % Yelp_API_Key,
    }

    response = requests.request('GET', url, headers=headers)
    return response.json()

def calc_dist(coor1, coor2):
    """Take two coordinates as tuples and return the distance in miles"""

    return distance.distance(coor1, coor2).mi

def calc_points(dist, business):
    """Given distance to business and business object return points value for completed quest"""

    return max(int(dist*10), 10) * len(business.get('price', "$"))

def fetch_quest(user_ip):
    """Query destinations and then randomly select a business and request its info from Yelp"""

    loc = get_user_location(user_ip)
    if type(loc) is str: return "INVALID IP"

    lat, lon = loc
    businesses = query_destinations(lat, lon)

    bus_idx = randint(0,len(businesses))
    print(businesses[bus_idx], flush=True)
    bus_id = businesses[bus_idx]['id']

    business = request_destination_info(bus_id)
    lat2, lon2 = business['coordinates']['latitude'], business['coordinates']['longitude']

    dist = calc_dist((lat, lon), (float(lat), float(lon)))
    business['points'] = calc_points(dist, business)

    return business

