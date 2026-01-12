import json
import numpy as np
from flask import Flask, render_template, jsonify, request, redirect, url_for
from typing import List, Dict, Tuple
import os
from RestaurantSearchEngine import RestaurantSearchEngine

app = Flask(__name__)

# Global variables
restaurant_data = []
search_engine = None

# Initialize search engine on startup
def init_search_engine():
    global search_engine
    print("Initializing search engine...")
    search_engine = RestaurantSearchEngine("db_restaurants_encoded.parquet")
    print("Search engine ready!")

# Load restaurant data from JSON
def load_restaurant_data(json_file_path: str = "restaurants_similarity.json"):
    global restaurant_data
    if os.path.exists(json_file_path):
        with open(json_file_path, 'r', encoding='utf-8') as f:
            restaurant_data = json.load(f)
        print(f"Loaded {len(restaurant_data)} restaurants")

def calculate_dynamic_grid_heatmap(
    similarity_threshold: float,
    bounds: Dict,
    grid_size: int = 100
) -> Tuple[List[Dict], List[Dict]]:
    """Calculate heatmap data using dynamic grid system based on map bounds."""
    filtered = [
        r for r in restaurant_data 
        if r.get('similarity', 0) >= similarity_threshold
    ]
    
    min_lat = bounds['min_lat']
    max_lat = bounds['max_lat']
    min_lng = bounds['min_lng']
    max_lng = bounds['max_lng']
    
    tiles_per_side = int(np.sqrt(grid_size))
    lat_tile_size = (max_lat - min_lat) / tiles_per_side
    lng_tile_size = (max_lng - min_lng) / tiles_per_side
    
    heatmap_points = []
    tiles_data = []
    
    for i in range(tiles_per_side):
        for j in range(tiles_per_side):
            tile_min_lat = min_lat + i * lat_tile_size
            tile_max_lat = min_lat + (i + 1) * lat_tile_size
            tile_min_lng = min_lng + j * lng_tile_size
            tile_max_lng = min_lng + (j + 1) * lng_tile_size
            
            count = sum(
                1 for r in filtered
                if tile_min_lat <= r['lat'] < tile_max_lat
                and tile_min_lng <= r['lng'] < tile_max_lng
            )
            
            center_lat = (tile_min_lat + tile_max_lat) / 2
            center_lng = (tile_min_lng + tile_max_lng) / 2
            
            tiles_data.append({
                'bounds': [
                    [tile_min_lat, tile_min_lng],
                    [tile_min_lat, tile_max_lng],
                    [tile_max_lat, tile_max_lng],
                    [tile_max_lat, tile_min_lng]
                ],
                'center': [center_lat, center_lng],
                'count': count
            })
            
            if count > 0:
                heatmap_points.append({
                    'lat': center_lat,
                    'lng': center_lng,
                    'weight': count
                })
    
    return heatmap_points, tiles_data

@app.route('/')
def index():
    """Serve the search page."""
    return render_template('search.html')

@app.route('/map')
def map_view():
    """Serve the map page."""
    return render_template('map.html')

@app.route('/api/search', methods=['POST'])
def search():
    """Handle search requests."""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Query cannot be empty'}), 400
        
        # Perform search using the search engine
        results = search_engine.search(
            user_input=query,
            output_path="restaurants_similarity.json"
        )
        
        # Load the new results
        load_restaurant_data("restaurants_similarity.json")
        
        return jsonify({
            'success': True,
            'count': len(results),
            'query': query
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/restaurants')
def get_restaurants():
    """Get all restaurant data."""
    return jsonify(restaurant_data)

@app.route('/api/heatmap')
def get_heatmap():
    """Calculate and return heatmap data based on threshold and bounds."""
    threshold = float(request.args.get('threshold', 0.0))
    
    if not all(k in request.args for k in ['min_lat', 'max_lat', 'min_lng', 'max_lng']):
        return jsonify({'error': 'Map bounds required'}), 400
    
    bounds = {
        'min_lat': float(request.args.get('min_lat')),
        'max_lat': float(request.args.get('max_lat')),
        'min_lng': float(request.args.get('min_lng')),
        'max_lng': float(request.args.get('max_lng'))
    }
    
    heatmap_data, tiles_data = calculate_dynamic_grid_heatmap(threshold, bounds, grid_size=100)
    
    filtered_count = sum(1 for r in restaurant_data if r.get('similarity', 0) >= threshold)
    
    return jsonify({
        'heatmap': heatmap_data,
        'tiles': tiles_data,
        'count': filtered_count,
        'threshold': threshold
    })

def create_templates():
    """Create the HTML template files."""
    os.makedirs('templates', exist_ok=True)
    
    # Search page
    search_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Restaurant Search</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 60px 50px;
            max-width: 600px;
            width: 100%;
            text-align: center;
        }
        
        h1 {
            color: #333;
            font-size: 36px;
            margin-bottom: 15px;
            font-weight: 700;
        }
        
        .subtitle {
            color: #666;
            font-size: 16px;
            margin-bottom: 40px;
        }
        
        .search-box {
            position: relative;
            margin-bottom: 30px;
        }
        
        #searchInput {
            width: 100%;
            padding: 18px 25px;
            font-size: 16px;
            border: 2px solid #e0e0e0;
            border-radius: 50px;
            outline: none;
            transition: all 0.3s ease;
        }
        
        #searchInput:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
        }
        
        #searchBtn {
            width: 100%;
            padding: 18px 25px;
            font-size: 18px;
            font-weight: 600;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        
        #searchBtn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }
        
        #searchBtn:active {
            transform: translateY(0);
        }
        
        #searchBtn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .loading {
            display: none;
            margin-top: 20px;
            color: #667eea;
            font-weight: 500;
        }
        
        .loading.active {
            display: block;
        }
        
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            vertical-align: middle;
            margin-right: 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .error {
            display: none;
            margin-top: 20px;
            padding: 15px;
            background: #fee;
            border: 1px solid #fcc;
            border-radius: 10px;
            color: #c33;
        }
        
        .error.active {
            display: block;
        }
        
        .examples {
            margin-top: 40px;
            text-align: left;
        }
        
        .examples h3 {
            color: #667eea;
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            margin-bottom: 15px;
        }
        
        .example-tag {
            display: inline-block;
            padding: 8px 16px;
            margin: 5px;
            background: #f5f5f5;
            border-radius: 20px;
            font-size: 14px;
            color: #555;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .example-tag:hover {
            background: #667eea;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1> Restaurant Search</h1>
        <p class="subtitle">Find the perfect restaurant based on your preferences</p>
        
        <div class="search-box">
            <input type="text" 
                   id="searchInput" 
                   placeholder="e.g., romantic italian restaurant with great wine"
                   autofocus>
        </div>
        
        <button id="searchBtn">Search Restaurants</button>
        
        <div class="loading" id="loading">
            <span class="spinner"></span>
            Searching for restaurants...
        </div>
        
        <div class="error" id="error"></div>
        
        <div class="examples">
            <h3>Try these examples:</h3>
            <span class="example-tag" data-query="cozy italian restaurant">Cozy Italian</span>
            <span class="example-tag" data-query="authentic asian cuisine">Authentic Asian</span>
            <span class="example-tag" data-query="romantic dinner spot">Romantic Dinner</span>
            <span class="example-tag" data-query="family friendly pizza">Family Pizza</span>
            <span class="example-tag" data-query="vegetarian options">Vegetarian</span>
            <span class="example-tag" data-query="seafood restaurant">Seafood</span>
        </div>
    </div>
    
    <script>
        const searchInput = document.getElementById('searchInput');
        const searchBtn = document.getElementById('searchBtn');
        const loading = document.getElementById('loading');
        const error = document.getElementById('error');
        
        // Example tags
        document.querySelectorAll('.example-tag').forEach(tag => {
            tag.addEventListener('click', () => {
                searchInput.value = tag.dataset.query;
                searchInput.focus();
            });
        });
        
        // Search function
        async function performSearch() {
            const query = searchInput.value.trim();
            
            if (!query) {
                showError('Please enter a search query');
                return;
            }
            
            // Show loading
            loading.classList.add('active');
            error.classList.remove('active');
            searchBtn.disabled = true;
            
            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ query })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    showError(data.error);
                    return;
                }
                
                // Redirect to map view
                window.location.href = '/map';
                
            } catch (err) {
                showError('An error occurred. Please try again.');
                console.error(err);
            } finally {
                loading.classList.remove('active');
                searchBtn.disabled = false;
            }
        }
        
        function showError(message) {
            error.textContent = message;
            error.classList.add('active');
            setTimeout(() => {
                error.classList.remove('active');
            }, 5000);
        }
        
        // Event listeners
        searchBtn.addEventListener('click', performSearch);
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
    </script>
</body>
</html>'''
    
    with open('templates/search.html', 'w', encoding='utf-8') as f:
        f.write(search_html)
    
    # Map page (reuse existing heatmap code)
    map_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Restaurant Similarity Heatmap</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            height: 100vh;
            overflow: hidden;
        }
        
        #map {
            width: 100%;
            height: 100vh;
        }
        
        #controls {
            position: absolute;
            top: 20px;
            left: 20px;
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            z-index: 1000;
            min-width: 320px;
        }
        
        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 15px;
        }
        
        h3 {
            margin: 0;
            font-size: 20px;
            color: #333;
        }
        
        .back-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.2s ease;
        }
        
        .back-btn:hover {
            background: #5568d3;
            transform: translateY(-1px);
        }
        
        .slider-container {
            margin: 15px 0;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #555;
            font-size: 14px;
        }
        
        #thresholdSlider {
            width: 100%;
            height: 6px;
            border-radius: 3px;
            background: linear-gradient(to right, #32CD32, #FFFF00, #FFA500, #FF0000);
            outline: none;
            -webkit-appearance: none;
        }
        
        #thresholdSlider::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #667eea;
            cursor: pointer;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        }
        
        #thresholdSlider::-moz-range-thumb {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #667eea;
            cursor: pointer;
            border: none;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        }
        
        .value-display {
            text-align: center;
            font-size: 28px;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }
        
        .info-text {
            font-size: 14px;
            color: #666;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #eee;
        }
        
        .toggle-btn {
            background: #f5f5f5;
            color: #333;
            border: 1px solid #ddd;
            padding: 10px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            margin-top: 8px;
            width: 100%;
            transition: all 0.2s ease;
        }
        
        .toggle-btn:hover {
            background: #e8e8e8;
        }
        
        .toggle-btn.active {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
        
        #legend {
            position: absolute;
            bottom: 30px;
            left: 20px;
            background: white;
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            z-index: 1000;
            min-width: 200px;
        }
        
        .legend-title {
            font-weight: 600;
            margin-bottom: 10px;
            font-size: 14px;
            color: #333;
        }
        
        .legend-gradient {
            height: 20px;
            background: linear-gradient(to right, 
                rgba(50,205,50,0.3), 
                #FFFF00, 
                #FFA500, 
                #FF0000);
            border: 1px solid #ddd;
            border-radius: 4px;
            margin: 8px 0;
        }
        
        .legend-labels {
            display: flex;
            justify-content: space-between;
            font-size: 11px;
            color: #666;
        }
    </style>
</head>
<body>
    <div id="map"></div>
    
    <div id="controls">
        <div class="header">
            <h3>🗺️ Results</h3>
            <button class="back-btn" onclick="window.location.href='/'">New Search</button>
        </div>
        
        <div class="slider-container">
            <label for="thresholdSlider">Similarity Threshold</label>
            <div class="value-display" id="thresholdValue">0.0</div>
            <input type="range" id="thresholdSlider" 
                   min="0.0" max="1.0" step="0.1" value="0.0">
        </div>
        
        <div class="info-text">
            <strong id="restaurantCount">0</strong> restaurants shown
        </div>
        
        <button class="toggle-btn" id="toggleMarkers">Show Markers</button>
        <button class="toggle-btn" id="toggleGrid">Show Grid</button>
    </div>
    
    <div id="legend">
        <div class="legend-title">Restaurant Density</div>
        <div class="legend-gradient"></div>
        <div class="legend-labels">
            <span>Low</span>
            <span>Medium</span>
            <span>High</span>
        </div>
    </div>
    
    <script src="https://unpkg.com/deck.gl@8.8.0/dist.min.js"></script>
    <script>
        const GOOGLE_MAPS_API_KEY = "AIzaSyAnmmOvxYRrR1FnVBK7t1fKaC7jmGmOZcU";
        const HEATMAP_RADIUS_PIXELS = 300;
        
        const INITIAL_VIEW = {
            lat: 48.579621,
            lng: 7.758358,
            zoom: 13
        };
        
        let map = null;
        let overlay = null;
        let restaurantData = [];
        let currentTilesData = [];
        let showMarkers = false;
        let showGrid = false;
        let markers = [];
        let tileRectangles = [];
        let tileLabels = [];
        let debouncedUpdateHeatmap;
        
        function generatePointsInTile(tilePolygon, count) {
            const points = [];
            const bounds = {
                north: Math.max(...tilePolygon.map(p => p[0])),
                south: Math.min(...tilePolygon.map(p => p[0])),
                east: Math.max(...tilePolygon.map(p => p[1])),
                west: Math.min(...tilePolygon.map(p => p[1]))
            };
            
            const latSize = bounds.north - bounds.south;
            const lngSize = bounds.east - bounds.west;
            const padding = 0.2;
            const paddedBounds = {
                north: bounds.north - latSize * padding,
                south: bounds.south + latSize * padding,
                east: bounds.east - lngSize * padding,
                west: bounds.west + lngSize * padding
            };
            
            const latSpacing = 100 / 111111;
            const lngSpacing = 100 / (111111 * Math.cos((bounds.north * Math.PI) / 180));
            
            for (let lat = paddedBounds.south; lat <= paddedBounds.north; lat += latSpacing) {
                for (let lng = paddedBounds.west; lng <= paddedBounds.east; lng += lngSpacing) {
                    points.push({
                        position: [lng, lat],
                        weight: count
                    });
                }
            }
            return points;
        }
        
        async function loadRestaurants() {
            const response = await fetch('/api/restaurants');
            restaurantData = await response.json();
            console.log(`Loaded ${restaurantData.length} restaurants`);
        }
        
        function createHeatmapLayer(heatmapData) {
            if (!heatmapData || heatmapData.length === 0) {
                return null;
            }
            
            const heatmapPoints = [];
            
            heatmapData.forEach(tile => {
                if (tile.weight > 0) {
                    const tilePolygon = [[tile.lat, tile.lng]];
                    const points = generatePointsInTile(tilePolygon, tile.weight);
                    heatmapPoints.push(...points);
                }
            });
            
            return new deck.HeatmapLayer({
                id: 'heatmap-layer-' + Date.now(),
                data: heatmapPoints,
                getPosition: d => d.position,
                getWeight: d => d.weight,
                radiusPixels: HEATMAP_RADIUS_PIXELS,
                intensity: 1,
                threshold: 0.01,
                colorRange: [
                    [0, 0, 0, 0],
                    [50, 205, 50, 80],
                    [255, 255, 0, 100],
                    [255, 165, 0, 120],
                    [255, 0, 0, 140]
                ],
                aggregation: 'SUM'
            });
        }
        
        function debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        }
        
        async function updateHeatmap() {
            try {
                if (!map || !map.getBounds()) return;
                
                const bounds = map.getBounds();
                const ne = bounds.getNorthEast();
                const sw = bounds.getSouthWest();
                const threshold = parseFloat(document.getElementById('thresholdSlider').value);
                
                const url = `/api/heatmap?threshold=${threshold}&min_lat=${sw.lat()}&max_lat=${ne.lat()}&min_lng=${sw.lng()}&max_lng=${ne.lng()}`;
                const response = await fetch(url);
                const data = await response.json();
                
                document.getElementById('restaurantCount').textContent = data.count;
                currentTilesData = data.tiles;
                
                const heatmapLayer = createHeatmapLayer(data.heatmap);
                
                if (overlay) {
                    if (heatmapLayer) {
                        overlay.setProps({ layers: [heatmapLayer] });
                    } else {
                        overlay.setProps({ layers: [] });
                    }
                }
                
                if (showMarkers) updateMarkers(threshold);
                if (showGrid) updateGrid();
            } catch (error) {
                console.error('Error updating heatmap:', error);
            }
        }
        
        function updateMarkers(threshold) {
            markers.forEach(m => m.setMap(null));
            markers = [];
            
            if (!showMarkers) return;
            
            const filtered = restaurantData.filter(r => r.similarity >= threshold);
            
            filtered.forEach(restaurant => {
                const marker = new google.maps.Marker({
                    position: { lat: restaurant.lat, lng: restaurant.lng },
                    map: map,
                    title: `${restaurant.name} (${restaurant.similarity.toFixed(2)})`,
                    icon: {
                        path: google.maps.SymbolPath.CIRCLE,
                        scale: 5,
                        fillColor: '#667eea',
                        fillOpacity: 0.8,
                        strokeColor: '#fff',
                        strokeWeight: 2
                    }
                });
                
                const infoWindow = new google.maps.InfoWindow({
                    content: `<strong>${restaurant.name}</strong><br>Similarity: ${restaurant.similarity.toFixed(2)}`
                });
                
                marker.addListener('click', () => {
                    infoWindow.open(map, marker);
                });
                
                markers.push(marker);
            });
        }
        
        function updateGrid() {
            tileRectangles.forEach(r => r.setMap(null));
            tileLabels.forEach(l => l.setMap(null));
            tileRectangles = [];
            tileLabels = [];
            
            if (!showGrid || !currentTilesData) return;
            
            currentTilesData.forEach(tile => {
                const rectangle = new google.maps.Polygon({
                    paths: tile.bounds.map(coord => ({ lat: coord[0], lng: coord[1] })),
                    strokeColor: '#000000',
                    strokeOpacity: 1,
                    strokeWeight: 1,
                    fillColor: '#000000',
                    fillOpacity: 0,
                    map: map
                });
                tileRectangles.push(rectangle);
                
                if (tile.count > 0) {
                    const label = new google.maps.Marker({
                        position: { lat: tile.center[0], lng: tile.center[1] },
                        map: map,
                        label: {
                            text: tile.count.toString(),
                            fontSize: '11px',
                            fontWeight: 'bold'
                        },
                        icon: {
                            path: google.maps.SymbolPath.CIRCLE,
                            scale: 0
                        }
                    });
                    tileLabels.push(label);
                }
            });
        }
        
        function toggleMarkers() {
            const btn = document.getElementById('toggleMarkers');
            showMarkers = !showMarkers;
            
            if (showMarkers) {
                btn.textContent = 'Hide Markers';
                btn.classList.add('active');
                const threshold = parseFloat(document.getElementById('thresholdSlider').value);
                updateMarkers(threshold);
            } else {
                btn.textContent = 'Show Markers';
                btn.classList.remove('active');
                markers.forEach(m => m.setMap(null));
                markers = [];
            }
        }
        
        function toggleGrid() {
            const btn = document.getElementById('toggleGrid');
            showGrid = !showGrid;
            
            if (showGrid) {
                btn.textContent = 'Hide Grid';
                btn.classList.add('active');
                updateGrid();
            } else {
                btn.textContent = 'Show Grid';
                btn.classList.remove('active');
                tileRectangles.forEach(r => r.setMap(null));
                tileLabels.forEach(l => l.setMap(null));
                tileRectangles = [];
                tileLabels = [];
            }
        }
        
        document.getElementById('thresholdSlider').addEventListener('input', function(e) {
            const value = parseFloat(e.target.value);
            document.getElementById('thresholdValue').textContent = value.toFixed(1);
            updateHeatmap();
        });
        
        document.getElementById('toggleMarkers').addEventListener('click', toggleMarkers);
        document.getElementById('toggleGrid').addEventListener('click', toggleGrid);
        
        function initMap() {
            map = new google.maps.Map(document.getElementById('map'), {
                center: { lat: INITIAL_VIEW.lat, lng: INITIAL_VIEW.lng },
                zoom: INITIAL_VIEW.zoom,
                gestureHandling: 'greedy',
                mapTypeId: 'roadmap'
            });
            
            overlay = new deck.GoogleMapsOverlay({
                layers: []
            });
            overlay.setMap(map);
            
            debouncedUpdateHeatmap = debounce(updateHeatmap, 500);
            
            let initialIdleFired = false;
            google.maps.event.addListenerOnce(map, 'idle', () => {
                if (!initialIdleFired) {
                    updateHeatmap();
                    initialIdleFired = true;
                }
            });
            
            map.addListener('idle', () => {
                if (debouncedUpdateHeatmap) {
                    debouncedUpdateHeatmap();
                }
            });
            
            (async function() {
                await loadRestaurants();
            })();
        }
        
        function loadGoogleMapsAPI() {
            const script = document.createElement('script');
            script.src = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_MAPS_API_KEY}&callback=initMap`;
            script.async = true;
            script.defer = true;
            document.head.appendChild(script);
        }
        
        window.initMap = initMap;
        loadGoogleMapsAPI();
    </script>
</body>
</html>'''
    
    with open('templates/map.html', 'w', encoding='utf-8') as f:
        f.write(map_html)
    
    print("✓ Created templates/search.html and templates/map.html")

if __name__ == "__main__":
    # Create templates
    create_templates()
    
    # Initialize search engine
    init_search_engine()
    
    # Load initial data if exists
    if os.path.exists("restaurants_similarity.json"):
        load_restaurant_data("restaurants_similarity.json")
    
    print("\n" + "="*50)
    print("🚀 Starting Restaurant Search Application")
    print("="*50)
    print("\n🔍 Open your browser and go to:")
    print("   http://localhost:5000")
    print("\n⚙️  Features:")
    print("   • Search restaurants by description")
    print("   • View results on interactive heatmap")
    print("   • Adjust similarity threshold")
    print("   • Show/Hide markers and grid\n")
    
    # Run Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)
