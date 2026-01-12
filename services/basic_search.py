import json
from pathlib import Path
from typing import Optional, Dict, Any
from google_apis import create_service


def basic_search(
    latitude: float,
    longitude: float,
    place_type: str,
    output_path: Optional[str] = None,
    radius: float = 500.0,
    max_results: int = 20,
    region_code: str = 'FR',
    language_code: str = 'en',
    rank_preference: str = 'DISTANCE'
) -> Dict[str, Any]:
    """
    Search for nearby places using Google Places API and save results to a JSON file.
    
    Args:
        latitude: Center point latitude for the search
        longitude: Center point longitude for the search
        place_type: Type of place to search for (e.g., 'restaurant', 'cafe', 'hotel')
        output_path: Path where to save the JSON file. If None, uses auto-generated name
        radius: Search radius in meters (default: 500)
        max_results: Maximum number of results to return (default: 20, max: 20)
        region_code: Region code for the search (default: 'FR')
        language_code: Language code for results (default: 'en')
        rank_preference: Ranking preference - 'DISTANCE' or 'POPULARITY' (default: 'DISTANCE')
    
    Returns:
        Dictionary containing the API response
        
    Raises:
        ValueError: If parameters are invalid
        Exception: If API call fails
    """
    # Validate inputs
    if not -90 <= latitude <= 90:
        raise ValueError(f"Latitude must be between -90 and 90, got {latitude}")
    if not -180 <= longitude <= 180:
        raise ValueError(f"Longitude must be between -180 and 180, got {longitude}")
    if radius <= 0:
        raise ValueError(f"Radius must be positive, got {radius}")
    if not 1 <= max_results <= 20:
        raise ValueError(f"max_results must be between 1 and 20, got {max_results}")
    if rank_preference not in ['DISTANCE', 'POPULARITY']:
        raise ValueError(f"rank_preference must be 'DISTANCE' or 'POPULARITY', got {rank_preference}")
    
    # Initialize the Google Places API service
    client_secret_file = 'client_secret.json'
    API_NAME = 'places'
    API_VERSION = 'v1'
    SCOPES = ['https://www.googleapis.com/auth/cloud-platform']
    
    service = create_service(client_secret_file, API_NAME, API_VERSION, SCOPES)
    
    # Build request body
    request_body = {
        'languageCode': language_code,
        'regionCode': region_code,
        'includedPrimaryTypes': place_type,
        'maxResultCount': max_results,
        'locationRestriction': {
            'circle': {
                'center': {
                    'latitude': latitude,
                    'longitude': longitude
                },
                'radius': radius
            }
        },
        'rankPreference': rank_preference
    }
    
    # Execute API request
    try:
        response = service.places().searchNearby(
            body=request_body,
            fields='places(id,displayName,formattedAddress,location,rating,reviews)',
        ).execute()
    except Exception as e:
        raise Exception(f"API request failed: {str(e)}")
    
    # Generate output filename if not provided
    if output_path is None:
        output_path = f"places_{place_type}_{latitude}_{longitude}.json"
    
    # Save to JSON file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(response, f, indent=2, ensure_ascii=False)
    
    print(f"Results saved to: {output_file}")
    print(f"Found {len(response.get('places', []))} places")
    
    return response


# Example usage
if __name__ == "__main__":
    # Example 1: Basic search with defaults
    results = basic_search(
        latitude=45.792784,
        longitude=24.152069,
        place_type='restaurant'
    )
    
    # Example 2: Custom search with all parameters
    results = basic_search(
        latitude=45.792784,
        longitude=24.152069,
        place_type='cafe',
        output_path='data/cafes_sibiu.json',
        radius=1000,
        max_results=15,
        region_code='RO',
        rank_preference='POPULARITY'
    )
    
    # Access the data
    for place in results.get('places', []):
        print(f"{place['displayName']['text']}: {place.get('rating', 'N/A')}")
