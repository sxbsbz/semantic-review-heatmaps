const MAPS_API_KEY = "API";

// Initial map view
const INITIAL_VIEW_STATE = {
  latitude: 48.579621,   // Strasbourg
  longitude: 7.758358,
  zoom: 13,
};

// Heatmap tuning
const HEATMAP_RADIUS_PIXELS = 250;
const HEATMAP_INTENSITY = 1.2;

// Global state
let map;
let overlay;
let restaurantData = [];
let pointsVisible = false;
let markers = [];

/**
 * Load similarity data (local JSON file)
 */
async function loadRestaurantData() {
  const response = await fetch("restaurants_similarity.json");
  restaurantData = await response.json();
  console.log(`Loaded ${restaurantData.length} restaurants`);
}

/**
 * Create heatmap layer directly from restaurant points
 */
function createHeatmapLayer(data) {
  return new deck.HeatmapLayer({
    id: "semantic-heatmap",
    data: data,
    getPosition: d => [d.lng, d.lat],
    getWeight: d => d.similarity, // 🔥 THIS IS THE CORE
    radiusPixels: HEATMAP_RADIUS_PIXELS,
    intensity: HEATMAP_INTENSITY,
    threshold: 0.01,
    colorRange: [
      [0, 0, 0, 0],
      [50, 205, 50, 80],
      [255, 255, 0, 120],
      [255, 165, 0, 160],
      [255, 0, 0, 200],
    ],
    aggregation: "SUM",
  });
}

/**
 * Toggle restaurant markers (debug)
 */
function togglePoints() {
  const button = document.getElementById("toggleGrid");
  pointsVisible = !pointsVisible;

  if (pointsVisible) {
    button.textContent = "Hide Points";
    restaurantData.forEach(r => {
      const marker = new google.maps.Marker({
        position: { lat: r.lat, lng: r.lng },
        map: map,
        title: `${r.name} (${r.similarity.toFixed(2)})`
      });
      markers.push(marker);
    });
  } else {
    button.textContent = "Show Points";
    markers.forEach(m => m.setMap(null));
    markers = [];
  }
}

/**
 * Initialize map
 */
async function initMap() {
  await loadRestaurantData();

  map = new google.maps.Map(document.getElementById("map"), {
    center: {
      lat: INITIAL_VIEW_STATE.latitude,
      lng: INITIAL_VIEW_STATE.longitude,
    },
    zoom: INITIAL_VIEW_STATE.zoom,
    gestureHandling: "greedy",
  });

  overlay = new deck.GoogleMapsOverlay({
    layers: [createHeatmapLayer(restaurantData)],
  });

  overlay.setMap(map);

  document
    .getElementById("toggleGrid")
    .addEventListener("click", togglePoints);
}

window.initMap = initMap;
