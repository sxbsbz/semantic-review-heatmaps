import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class RestaurantSearchEngine:
    """
    Fast restaurant search engine using pre-encoded embeddings.
    Loads model and database once, then performs fast searches.
    """
    
    def __init__(self, encoded_db_path):
        """
        Initialize the search engine.
        
        Parameters:
        -----------
        encoded_db_path : str
            Path to the Parquet file containing pre-encoded restaurant data
        """
        print("Loading search engine...")
        
        # Load pre-encoded database
        print("  - Loading database...")
        self.df = pd.read_parquet(encoded_db_path, engine='pyarrow')
        
        # Convert embeddings to numpy array once
        print("  - Converting embeddings...")
        self.embeddings_array = np.array(self.df['embedding'].tolist())
        
        # Load model once
        print("  - Loading model...")
        self.model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
        
        print("✓ Search engine ready!")
    
    def search(self, user_input, output_path=None, aggregation='max'):
        """
        Search for similar restaurants.
        
        Parameters:
        -----------
        user_input : str
            The text query from the user
        output_path : str, optional
            Path where to save the JSON output
        aggregation : str, default='max'
            How to aggregate similarity scores per restaurant ('max' or 'mean')
        
        Returns:
        --------
        list of dict
            List of restaurants with similarity scores, sorted by relevance
        """
        
        # Encode user input (fast - only one sentence)
        input_embedding = self.model.encode(user_input, convert_to_tensor=False)
        
        # Compute cosine similarity
        similarities = cosine_similarity([input_embedding], self.embeddings_array)[0]
        
        # Create a copy of dataframe and attach scores
        df_result = self.df.copy()
        df_result['similarity_score'] = similarities
        
        # Aggregate per restaurant
        agg_dict = {
            'place_name': 'first',
            'latitude': 'first',
            'longitude': 'first',
            'similarity_score': aggregation if aggregation in ['max', 'mean'] else 'max'
        }
        
        restaurant_df = (
            df_result.groupby('place_id', as_index=False)
            .agg(agg_dict)
            .sort_values('similarity_score', ascending=False)
        )
        
        # Rename columns
        restaurant_df.columns = ['place_id', 'name', 'lat', 'lng', 'similarity']
        restaurant_df['similarity'] = restaurant_df['similarity'].round(4)
        
        # Convert to dict
        json_result = restaurant_df.to_dict(orient="records")
        
        # Export if path provided
        if output_path:
            restaurant_df.to_json(
                output_path,
                orient="records",
                force_ascii=False,
                indent=2
            )
        
        return json_result


def find_similar_restaurants_fast(user_input, encoded_db_path, output_path=None, aggregation='max'):
    """
    Standalone function for one-time searches.
    For multiple searches, use RestaurantSearchEngine class instead.
    """
    engine = RestaurantSearchEngine(encoded_db_path)
    return engine.search(user_input, output_path, aggregation)


# Example usage:
if __name__ == "__main__":
    # Initialize search engine once
    engine = RestaurantSearchEngine("~/projects/restaurantAP/db_restaurants_encoded.parquet")
    
    # Now you can do multiple searches quickly
    while True:
        user_query = input("\nType your search query (or 'quit' to exit): ")
        
        if user_query.lower() in ['quit', 'exit', 'q']:
            break
        
        if not user_query.strip():
            continue
        
        print("Searching...")
        results = engine.search(
            user_input=user_query,
            output_path="~/projects/restaurantAP/restaurants_similarity.json"
        )
        
        print(f"\nTop 5 results:")
        for i, restaurant in enumerate(results[:5], 1):
            print(f"{i}. {restaurant['name']} (similarity: {restaurant['similarity']})")
