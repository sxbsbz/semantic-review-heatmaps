Restaurant Semantic Search & Heatmap DEMO version

Semantic search engine for restaurants using multilingual embeddings with interactive heatmap visualization.
Quick Start
bash

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py

Open http://localhost:5000
What It Does

    Semantic Search: Enter natural language queries (e.g., "cozy italian restaurant") to find matching restaurants using sentence embeddings
    Similarity Scoring: Ranks all restaurants by semantic similarity (0.0-1.0)
    Interactive Heatmap: Visualizes restaurant density on Google Maps with dynamic grid system
    Threshold Filtering: Adjust similarity threshold to filter results in real-time

Files

    RestaurantSearchEngine.py - Core search engine with pre-encoded embeddings
    app.py - Flask web application with search and map endpoints
    heatmap_service.py - Standalone heatmap service (alternative to app.py)
    requirements.txt - Python dependencies

Requirements

    db_restaurants_encoded.parquet - Pre-encoded restaurant database with embeddings
    Google Maps API key (update in templates)

Features

    Fast searches using pre-computed embeddings
    Real-time heatmap updates based on map bounds
    Toggle markers and grid overlay
    Multi-language support (paraphrase-multilingual-mpnet model)

