from google_apis import create_service

client_secret_file = 'client_secret.json'
API_NAME='places'
API_VERSION = 'v1'
SCOPES = ['https://www.googleapis.com/auth/cloud-platform']

service = create_service(client_secret_file,API_NAME,API_VERSION,SCOPES)

request_body = {
    'languageCode': 'en',
    'regionCode': 'FR',
    'includedPrimaryTypes': 'restaurant',
    'maxResultCount':20,
    'locationRestriction':{
        'circle':{
            'center':{
                'latitude': 45.792784,
                'longitude': 24.152069
            },
            'radius' : 500
        }
    },
    'rankPreference': 'DISTANCE'
}

response = service.places().searchNearby(
    body = request_body,
    fields = 'places(id,displayName,formattedAddress,location,rating,reviews)',
).execute()

print(response)
