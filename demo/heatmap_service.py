import json
import numpy as np
from flask import Flask, render_template, jsonify, request
from typing import List, Dict, Tuple
import os

app = Flask(__name__)

# Global variable to store restaurant data
restaurant_data = []


def load_restaurant_data(json_file_path: str = "restaurants_similarity.json"):
    """Load restaurant data from JSON file."""
    global restaurant_data
    with open(json_file_path, 'r', encoding='utf-8') as f:
        restaurant_data = json.load(f)
    print(f"Loaded {len(restaurant_data)} restaurants")


def calculate_dynamic_grid_heatmap(
    similarity_threshold: float,
    bounds: Dict,
    grid_size: int = 100
) -> Tuple[List[Dict], List[Dict]]:
    """
    Calculate heatmap data using dynamic grid system based on map bounds.
    
    Parameters:
    -----------
    similarity_threshold : float
        Minimum similarity score (0.0 to 1.0)
    bounds : dict
        Map bounds {'min_lat', 'max_lat', 'min_lng', 'max_lng'}
    grid_size : int
        Target number of grid tiles
    
    Returns:
    --------
    Tuple of (heatmap_points, tiles_data)
    """
    # Filter by threshold
    filtered = [
        r for r in restaurant_data 
        if r.get('similarity', 0) >= similarity_threshold
    ]
    
    min_lat = bounds['min_lat']
    max_lat = bounds['max_lat']
    min_lng = bounds['min_lng']
    max_lng = bounds['max_lng']
    
    # Calculate tile size
    tiles_per_side = int(np.sqrt(grid_size))
    lat_tile_size = (max_lat - min_lat) / tiles_per_side
    lng_tile_size = (max_lng - min_lng) / tiles_per_side
    
    # Generate grid and count restaurants
    heatmap_points = []
    tiles_data = []
    
    for i in range(tiles_per_side):
        for j in range(tiles_per_side):
            tile_min_lat = min_lat + i * lat_tile_size
            tile_max_lat = min_lat + (i + 1) * lat_tile_size
            tile_min_lng = min_lng + j * lng_tile_size
            tile_max_lng = min_lng + (j + 1) * lng_tile_size
            
            # Count restaurants in tile
            count = sum(
                1 for r in filtered
                if tile_min_lat <= r['lat'] < tile_max_lat
                and tile_min_lng <= r['lng'] < tile_max_lng
            )
            
            # Calculate tile center
            center_lat = (tile_min_lat + tile_max_lat) / 2
            center_lng = (tile_min_lng + tile_max_lng) / 2
            
            # Store tile data
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
            
            # Add heatmap point at tile center (only if count > 0)
            if count > 0:
                heatmap_points.append({
                    'lat': center_lat,
                    'lng': center_lng,
                    'weight': count
                })
    
    return heatmap_points, tiles_data


@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')


@app.route('/api/restaurants')
def get_restaurants():
    """Get all restaurant data."""
    return jsonify(restaurant_data)


@app.route('/api/heatmap')
def get_heatmap():
    """Calculate and return heatmap data based on threshold and bounds."""
    threshold = float(request.args.get('threshold', 0.0))
    
    # Get bounds from request (required for dynamic grid)
    if not all(k in request.args for k in ['min_lat', 'max_lat', 'min_lng', 'max_lng']):
        return jsonify({'error': 'Map bounds required'}), 400
    
    bounds = {
        'min_lat': float(request.args.get('min_lat')),
        'max_lat': float(request.args.get('max_lat')),
        'min_lng': float(request.args.get('min_lng')),
        'max_lng': float(request.args.get('max_lng'))
    }
    
    heatmap_data, tiles_data = calculate_dynamic_grid_heatmap(threshold, bounds, grid_size=100)
    
    # Also return filtered count
    filtered_count = sum(1 for r in restaurant_data if r.get('similarity', 0) >= threshold)
    
    return jsonify({
        'heatmap': heatmap_data,
        'tiles': tiles_data,
        'count': filtered_count,
        'threshold': threshold
    })


# Create templates directory and HTML file
def create_template():
    """Create the HTML template file."""
    os.makedirs('templates', exist_ok=True)
    
    html_content = '''<!DOCTYPE html>
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
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            z-index: 1000;
            min-width: 300px;
        }
        
        h3 {
            margin: 0 0 15px 0;
            font-size: 18px;
            color: #333;
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
            background: #4CAF50;
            cursor: pointer;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        }
        
        #thresholdSlider::-moz-range-thumb {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #4CAF50;
            cursor: pointer;
            border: none;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        }
        
        .value-display {
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            color: #4CAF50;
            margin: 10px 0;
        }
        
        .info-text {
            font-size: 13px;
            color: #666;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #eee;
        }
        
        #legend {
            position: absolute;
            bottom: 30px;
            left: 20px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            z-index: 1000;
            min-width: 200px;
        }
        
        .legend-title {
            font-weight: bold;
            margin-bottom: 10px;
            font-size: 14px;
        }
        
        .legend-gradient {
            height: 20px;
            background: linear-gradient(to right, 
                rgba(50,205,50,0.3), 
                #FFFF00, 
                #FFA500, 
                #FF0000);
            border: 1px solid #999;
            border-radius: 3px;
            margin: 8px 0;
        }
        
        .legend-labels {
            display: flex;
            justify-content: space-between;
            font-size: 11px;
            color: #666;
        }
        
        .toggle-btn {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
            margin-top: 10px;
            width: 100%;
        }
        
        .toggle-btn:hover {
            background: #45a049;
        }
        
        .toggle-btn.active {
            background: #f44336;
        }
    </style>
</head>
<body>
    <div id="map"></div>
    
    <div id="controls">
        <h3>🗺️ Similarity Heatmap</h3>
        
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
        // REPLACE WITH YOUR GOOGLE MAPS API KEY
        const GOOGLE_MAPS_API_KEY = "AIzaSyAnmmOvxYRrR1FnVBK7t1fKaC7jmGmOZcU";
        
        const TARGET_TILE_COUNT = 100;
        const POINT_SPACING_METERS = 100;
        const HEATMAP_RADIUS_PIXELS = 300;
        
        // Configuration
        const INITIAL_VIEW = {
            lat: 48.579621,
            lng: 7.758358,
            zoom: 13
        };
        
        // Global variables
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
        
        /**
         * Generates a grid of points within a tile for heatmap visualization
         */
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
            
            const latSpacing = POINT_SPACING_METERS / 111111;
            const lngSpacing = POINT_SPACING_METERS / (111111 * Math.cos((bounds.north * Math.PI) / 180));
            
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
        
        /**
         * Load restaurant data
         */
        async function loadRestaurants() {
            const response = await fetch('/api/restaurants');
            restaurantData = await response.json();
            console.log(`Loaded ${restaurantData.length} restaurants`);
        }
        
        /**
         * Create heatmap layer from tile data
         */
        function createHeatmapLayer(heatmapData) {
            if (!heatmapData || heatmapData.length === 0) {
                return null;
            }
            
            // Convert tile data to multiple heatmap points for smooth visualization
            const heatmapPoints = [];
            
            heatmapData.forEach(tile => {
                if (tile.weight > 0) {
                    // Create a small polygon around the tile center for point generation
                    const tilePolygon = [
                        [tile.lat, tile.lng]
                    ];
                    
                    // Generate multiple points for this tile
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
        
        /**
         * Debounce function
         */
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
        
        /**
         * Update heatmap based on current map bounds and threshold
         */
        async function updateHeatmap() {
            try {
                if (!map || !map.getBounds()) {
                    return;
                }
                
                const bounds = map.getBounds();
                const ne = bounds.getNorthEast();
                const sw = bounds.getSouthWest();
                
                const threshold = parseFloat(document.getElementById('thresholdSlider').value);
                
                const url = `/api/heatmap?threshold=${threshold}&min_lat=${sw.lat()}&max_lat=${ne.lat()}&min_lng=${sw.lng()}&max_lng=${ne.lng()}`;
                const response = await fetch(url);
                const data = await response.json();
                
                // Update count display
                document.getElementById('restaurantCount').textContent = data.count;
                
                // Store tiles data
                currentTilesData = data.tiles;
                
                // Update heatmap layer
                const heatmapLayer = createHeatmapLayer(data.heatmap);
                
                if (overlay) {
                    if (heatmapLayer) {
                        overlay.setProps({ layers: [heatmapLayer] });
                    } else {
                        overlay.setProps({ layers: [] });
                    }
                }
                
                // Update markers if visible
                if (showMarkers) {
                    updateMarkers(threshold);
                }
                
                // Update grid if visible
                if (showGrid) {
                    updateGrid();
                }
            } catch (error) {
                console.error('Error updating heatmap:', error);
            }
        }
        
        /**
         * Update markers
         */
        function updateMarkers(threshold) {
            // Clear existing markers
            markers.forEach(m => m.setMap(null));
            markers = [];
            
            if (!showMarkers) return;
            
            // Filter restaurants
            const filtered = restaurantData.filter(r => r.similarity >= threshold);
            
            // Create new markers
            filtered.forEach(restaurant => {
                const marker = new google.maps.Marker({
                    position: { lat: restaurant.lat, lng: restaurant.lng },
                    map: map,
                    title: `${restaurant.name} (${restaurant.similarity.toFixed(2)})`,
                    icon: {
                        path: google.maps.SymbolPath.CIRCLE,
                        scale: 5,
                        fillColor: '#4CAF50',
                        fillOpacity: 0.7,
                        strokeColor: '#fff',
                        strokeWeight: 1
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
        
        /**
         * Update grid visualization
         */
        function updateGrid() {
            // Clear existing grid
            tileRectangles.forEach(r => r.setMap(null));
            tileLabels.forEach(l => l.setMap(null));
            tileRectangles = [];
            tileLabels = [];
            
            if (!showGrid || !currentTilesData) return;
            
            // Draw tiles
            currentTilesData.forEach(tile => {
                // Draw rectangle
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
                
                // Add label with count (only if count > 0)
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
        
        /**
         * Toggle markers
         */
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
        
        /**
         * Toggle grid
         */
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
        
        /**
         * Slider event listener
         */
        document.getElementById('thresholdSlider').addEventListener('input', function(e) {
            const value = parseFloat(e.target.value);
            document.getElementById('thresholdValue').textContent = value.toFixed(1);
            updateHeatmap();
        });
        
        /**
         * Button event listeners
         */
        document.getElementById('toggleMarkers').addEventListener('click', toggleMarkers);
        document.getElementById('toggleGrid').addEventListener('click', toggleGrid);
        
        /**
         * Initialize map
         */
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
            
            // Create debounced update function
            debouncedUpdateHeatmap = debounce(updateHeatmap, 500);
            
            // Initial load
            let initialIdleFired = false;
            google.maps.event.addListenerOnce(map, 'idle', () => {
                if (!initialIdleFired) {
                    console.log('Map idle (once), initial updateHeatmap call.');
                    updateHeatmap();
                    initialIdleFired = true;
                }
            });
            
            // Update on map move/zoom
            map.addListener('idle', () => {
                if (debouncedUpdateHeatmap) {
                    debouncedUpdateHeatmap();
                }
            });
            
            // Initialize data
            (async function() {
                await loadRestaurants();
            })();
        }
        
        /**
         * Load Google Maps API
         */
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
    
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("Created templates/index.html")


if __name__ == "__main__":
    # Create template
    create_template()
    
    # Load restaurant data
    load_restaurant_data("restaurants_similarity.json")
    
    print("\n" + "="*50)
    print("🚀 Starting Restaurant Heatmap Server")
    print("="*50)
    print("\n📍 Open your browser and go to:")
    print("   http://localhost:5000")
    print("\n⚙️  Features:")
    print("   • Dynamic grid that adjusts on zoom/pan")
    print("   • Heatmap points at tile centers")
    print("   • Interactive threshold slider (0.0 - 1.0)")
    print("   • Show/Hide markers and grid\n")
    
    # Run Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)
