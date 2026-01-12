# Main.py
import pandas as pd
import spacy
from Cleaning import clean_reviews
from Embedding import generate_embeddings, calculate_similarities
import numpy as np


# Path to the CSV file containing restaurant data
path = "~/projects/restaurantAP/db_restaurants_aggregated.csv"
df = pd.read_csv(path)

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

TOOL_DESCRIPTIONS = {
    "restaurant_request": "User asks for restaurant recommendations or places to eat",
    "food_preference": "User mentions food they like or describe a dish or cuisine they enjoy",
    "no_tool": "General conversation unrelated to restaurants or food"
}

tool_texts = list(TOOL_DESCRIPTIONS.values())
tool_embeddings = generate_embeddings(tool_texts)

def get_user_input():
    """
    Get user input from the console or any external source.
    """
    return input("Please enter your request: ")

def classify_intent(user_request: str):
    user_embedding = generate_embeddings([user_request])
    similarities = calculate_similarities(user_embedding, tool_embeddings)

    best_idx = similarities[0].argmax()
    confidence = similarities[0][best_idx]

    if confidence < 0.35:
        return False, False

    intent = list(TOOL_DESCRIPTIONS.keys())[best_idx]

    if intent in ("restaurant_request", "food_preference"):
        return True, True

    return False, False

def main():
    """
    Main function to process the user request, decide on actions, and run the necessary tools.
    """
    # Step 1: Get user input
    user_request = get_user_input()
    
    # Step 2: Classify intent using NLP
    use_cleaning, use_embedding = classify_intent(user_request)

    # Step 3: Check if neither cleaning nor embedding is needed
    if not use_cleaning and not use_embedding:
        print("I am not programmed to achieve this.")
        return

    # Step 4: Process request based on the decision
    if use_cleaning:
        # Clean the reviews (removes newlines and emojis)
        df['review_text'] = clean_reviews(df['review_text'])

    if use_embedding:
        # Generate embeddings for the reviews
        embeddings = generate_embeddings(df['review_text'])

        # Now we simulate calculating similarities (for example, based on the user request)
        user_embedding = generate_embeddings([user_request])
        similarities = calculate_similarities(user_embedding, embeddings)

        # Ensure similarities is not empty and contains valid values
        if similarities.size == 0:
            print("No similarities found.")
            return

        # Handle case where similarities are all equal or zero
        if similarities.max() == 0:
            print("No similar restaurants found.")
            return

        # Number of recommendations
        TOP_K = 5

        scores = similarities.cpu().numpy().reshape(-1)
        top_indices = np.argsort(-scores)[:TOP_K]


        print("\nTop restaurant recommendations:")

        for rank, idx in enumerate(top_indices, start=1):
            if idx >= len(df) or idx < 0:
                continue

            restaurant = df.iloc[idx]
            score = scores[int(idx)]

            print(f"{rank}. {restaurant['place_name']} (score: {score:.3f})")

if __name__ == "__main__":
    main()
