"""
update_db.py
Met à jour la base de données restaurants avec l'API Google Places
"""

import pandas as pd
import requests
import os
from typing import Dict, List

# Clé API Google Places
GOOGLE_API_KEY = os.environ.get('GOOGLE_PLACES_API_KEY', 'YOUR_API_KEY_HERE')


def basic_scrape(coord: tuple, type: str, fields: List[str]) -> List[Dict]:
    """
    Scraping de base via Google Places API
    
    Args:
        coord: (latitude, longitude) du centre de recherche
        type: type de lieu (ex: "restaurant")
        fields: champs à récupérer
    
    Returns:
        Liste de max 20 restaurants avec leurs données
    """
    lat, lng = coord
    
    # 1. Nearby Search pour obtenir les restaurants
    nearby_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    nearby_params = {
        'location': f"{lat},{lng}",
        'radius': 1000,
        'type': type,
        'key': GOOGLE_API_KEY
    }
    
    response = requests.get(nearby_url, params=nearby_params)
    if response.status_code != 200:
        print(f"❌ Erreur API: {response.status_code}")
        return []
    
    places = response.json().get('results', [])[:20]
    
    restaurants = []
    for place in places:
        place_id = place.get('place_id')
        
        # Place Details pour reviews
        details_url = "https://maps.googleapis.com/maps/api/place/details/json"
        details_params = {
            'place_id': place_id,
            'fields': 'name,place_id,geometry,reviews,url',
            'key': GOOGLE_API_KEY
        }
        
        details_response = requests.get(details_url, params=details_params)
        details = details_response.json().get('result', {})
        
        # Extraire reviews (max 5)
        reviews = details.get('reviews', [])[:5]
        review_texts = [r.get('text', '') for r in reviews]
        
        location = details.get('geometry', {}).get('location', {})
        
        restaurants.append({
            'place_id': place_id,
            'name': details.get('name', ''),
            'latitude': location.get('lat', 0),
            'longitude': location.get('lng', 0),
            'google_maps_uri': f"https://maps.google.com/?cid={place_id}",
            'reviews_uri': details.get('url', ''),
            'review_text': '\n'.join(review_texts),
            'review_count': len(reviews)
        })
    
    return restaurants


def geocode_zone(zone_name: str) -> tuple:
    """
    Convertit un nom de zone en coordonnées via Geocoding API
    """
    geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        'address': zone_name,
        'key': GOOGLE_API_KEY
    }
    
    response = requests.get(geocode_url, params=params)
    if response.status_code == 200:
        results = response.json().get('results', [])
        if results:
            location = results[0]['geometry']['location']
            return (location['lat'], location['lng'])
    
    raise ValueError(f"Impossible de géocoder: {zone_name}")


def zone_exists(db: pd.DataFrame, zone_name: str) -> bool:
    """
    Vérifie si une zone existe déjà dans la base
    """
    if 'zone' not in db.columns or db.empty:
        return False
    return zone_name.lower() in db['zone'].str.lower().values


def format_restaurant_data(raw_data: List[Dict], zone_name: str) -> pd.DataFrame:
    """
    Formate les données brutes en DataFrame
    """
    formatted_data = []
    
    for item in raw_data:
        formatted_data.append({
            'place_id': item.get('place_id', ''),
            'place_name': item.get('name', ''),
            'latitude': item.get('latitude', 0),
            'longitude': item.get('longitude', 0),
            'google_maps_uri': item.get('google_maps_uri', ''),
            'reviews_uri': item.get('reviews_uri', ''),
            'review_text': item.get('review_text', ''),
            'review_count': item.get('review_count', 0),
            'zone': zone_name
        })
    
    return pd.DataFrame(formatted_data)


def update_db(db: pd.DataFrame, zone_name: str = None) -> pd.DataFrame:
    """
    Met à jour la base de données avec de nouveaux restaurants
    
    Args:
        db: DataFrame base actuelle
        zone_name: Zone à rechercher (ex: "Esplanade Strasbourg")
    
    Returns:
        DataFrame mis à jour
    """
    if not zone_name:
        print("⚠️ Aucune zone spécifiée")
        return db
    
    # Vérifier si la zone existe déjà
    if zone_exists(db, zone_name):
        print(f"✅ Zone '{zone_name}' déjà présente, pas d'appel API")
        return db
    
    print(f"🔍 Récupération des restaurants pour: {zone_name}")
    
    try:
        # Géocoder la zone
        coord = geocode_zone(zone_name)
        print(f"📍 Coordonnées: {coord}")
        
        # Scraper les restaurants
        fields = ["name", "location", "place_id", "reviews", "url"]
        raw_data = basic_scrape(coord, "restaurant", fields)
        
        if not raw_data:
            print("❌ Aucune donnée récupérée")
            return db
        
        print(f"✅ {len(raw_data)} restaurants récupérés")
        
        # Formater les données
        new_data = format_restaurant_data(raw_data, zone_name)
        
        # Ajouter la colonne zone si elle n'existe pas
        if 'zone' not in db.columns:
            db['zone'] = ''
        
        # Fusionner avec la base existante
        updated_db = pd.concat([db, new_data], ignore_index=True)
        
        print(f"{len(new_data)} nouveaux restaurants ajoutés")
        return updated_db
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return db


def load_db(path: str = "db_restaurants_aggregated.csv") -> pd.DataFrame:
    """
    Charge la base de données
    """
    try:
        return pd.read_csv(path)
    except FileNotFoundError:
        return pd.DataFrame(columns=[
            'place_id', 'place_name', 'latitude', 'longitude',
            'google_maps_uri', 'reviews_uri', 'review_text', 
            'review_count', 'zone'
        ])


def save_db(db: pd.DataFrame, path: str = "db_restaurants_aggregated.csv"):
    """
    Sauvegarde la base de données
    """
    db.to_csv(path, index=False)
    print(f"✅ Base sauvegardée: {path}")


if __name__ == "__main__":
    # Exemple d'utilisation
    db = load_db()
    print(f"📂 Base chargée: {len(db)} entrées")
    
    # Mettre à jour avec une nouvelle zone
    db = update_db(db, "Esplanade Strasbourg")
    
    # Sauvegarder
    save_db(db)