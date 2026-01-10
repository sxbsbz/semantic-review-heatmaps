import pandas as pd
import re
from sentence_transformers import SentenceTransformer, util

# Load data
path = "C:/Users/scheu/OneDrive/Documents/LLM Resto/db_restaurants_aggregated.csv"
df = pd.read_csv(path)

# Clean text
df['review_text'] = df['review_text'].str.replace('\n', ' ', regex=False)

def remove_emoji(text):
    if pd.isna(text):
        return ""
    return re.sub(r'[^\w\s.,!?;:àáâäçèéêëîïôöùúûüÿ\'-]', '', text)

df['review_text'] = df['review_text'].apply(remove_emoji)

# User input
user_input = input("Type your text: ")

# Load model
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-mpnet-base-v2")

# Encode reviews and input
review_embeddings = model.encode(
    df['review_text'].tolist(),
    convert_to_tensor=True
)

input_embedding = model.encode(
    user_input,
    convert_to_tensor=True
)

# Compute cosine similarity
similarities = util.cos_sim(input_embedding, review_embeddings)[0]

# Attach similarity scores to df
df['similarity_score'] = similarities.cpu().numpy()

# --------------------------------------------------
# Aggregate per restaurant
# --------------------------------------------------

restaurant_df = (
    df.groupby('place_id')
    .agg(
        place_name=('place_name', 'first'),
        latitude=('latitude', 'first'),
        longitude=('longitude', 'first'),
        similarity_score=('similarity_score', 'max')  # or mean
    )
    .reset_index()
    .sort_values('similarity_score', ascending=False)
)

print(restaurant_df.head())



# Renommer les colonnes pour le JSON final
restaurant_df = restaurant_df.rename(columns={
    "place_name": "name",
    "latitude": "lat",
    "longitude": "lng",
    "similarity_score": "similarity"
})

# Optionnel : arrondir le score
restaurant_df["similarity"] = restaurant_df["similarity"].round(4)

# Convertir en liste de dictionnaires
json_result = restaurant_df.to_dict(orient="records")

# Export vers fichier JSON
output_path = "C:/Users/scheu/OneDrive/Documents/LLM Resto/restaurants_similarity.json"
restaurant_df.to_json(
    output_path,
    orient="records",
    force_ascii=False,
    indent=2
)

print(json_result[:2]) 