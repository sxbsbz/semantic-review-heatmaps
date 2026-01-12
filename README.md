# Semantic heatmap generation tool

This project explores how semantic analysis of user reviews can be combined with geospatial visualization to reveal qualitative patterns in a city’s restaurant landscape.

Instead of showing where restaurants are dense, the goal is to highlight where specific experiences, sentiments, or themes are concentrated, based on what people actually write in reviews.

# DISCLAIMER 

**The project is far from finished as a substential number of implementation issues have slowed down the developement of the final tool.**
**A DEMO model is available to preview the the main final functions namely the heatmap generation and the semantic embedding tools. For more information check the README.md file in the demo directory.** 


# Project Overview

The pipeline is composed of four main stages:

## Data Collection

Restaurants are discovered using the Google Places API.

A grid-based search is used to cover the entire city area.

Place IDs, locations, and user reviews are collected at scale.

## Data Processing

Raw data is stored locally (CSV / JSON).

Duplicate places are removed.

Reviews are cleaned (emoji removal, whitespace normalization, text normalization).

Reviews are aggregated per restaurant.

## Semantic Embedding

A pretrained sentence embedding model (Hugging Face / Sentence Transformers) is used.

Each review is converted into a vector embedding.

Review embeddings are aggregated per restaurant to form a semantic profile.

Similarity scores are computed relative to a chosen semantic query.

## Geospatial Visualization

Results are displayed on Google Maps using Deck.gl.

A heatmap visualizes semantic similarity rather than raw density.

An interactive legend and debug markers are included.

