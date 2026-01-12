# Tool DEMO version

The demo has for purpose to showcase the conceptualized use of the final tool and does not feature the full implementaion of all the planned features.

The demo code uses a pre-scraped and processed database of all restaurants in the area of Strasbourg. This data has been obtained using the *full_size_strasbourg_scraper.py* code and processed using the *data_process.py* code (both are available in the `services` directory. The processed data was pre-encoded by the semantic model to optimize execution time. 

## Quick start

1. Install dependencies
```
pip install -r requirements.txt
```

2. Run the application
```
python app.py
```

*Note : When running the app for the first time, charging all the packages can take up to several minutes* 

3. Open http://localhost:5000

## What It Does

- Semantic Search: Enter natural language queries (e.g., "cozy italian restaurant") to find matching restaurants using sentence embeddings
- Similarity Scoring: Ranks all restaurants by semantic similarity (0.0-1.0)
- Interactive Heatmap: Visualizes restaurant density on Google Maps with dynamic grid system
- Threshold Filtering: Adjust similarity threshold to filter results in real-time

## Files

- RestaurantSearchEngine.py - Core search engine with pre-encoded embeddings
- app.py - Flask web application with search and map endpoints
- heatmap_service.py - Standalone heatmap service (alternative to app.py)
- requirements.txt - Python dependencies

## Requirements

- db_restaurants_encoded.parquet - Pre-encoded restaurant database with embeddings
- Google Maps API key (update in templates)

## Features

- Fast searches using pre-computed embeddings
- Real-time heatmap updates based on map bounds
- Toggle markers and grid overlay
- Multi-language support (paraphrase-multilingual-mpnet model)

