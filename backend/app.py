from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from sentence_transformers import SentenceTransformer, util
import pandas as pd
import re

app = Flask(__name__, static_folder='.')
CORS(app)

# Configuration
DB_PATH = "db_restaurants_aggregated.csv"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

# Charger le modèle et les données au démarrage
print(" Chargement du modèle et des données...")
model = SentenceTransformer(MODEL_NAME)
df = pd.read_csv(DB_PATH)

# Nettoyer les données
df['review_text'] = df['review_text'].str.replace('\n', ' ', regex=False)

def remove_emoji(text):
    if pd.isna(text):
        return ""
    return re.sub(r'[^\w\s.,!?;:àáâäçèéêëîïôöùúûüÿ\'-]', '', text)

df['review_text'] = df['review_text'].apply(remove_emoji)

# Pré-calculer les embeddings des reviews
print(" Calcul des embeddings des reviews...")
review_embeddings = model.encode(
    df['review_text'].tolist(),
    convert_to_tensor=True,
    show_progress_bar=True
)

print(" Serveur prêt!")

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        print(f"🔍 Recherche: {query}")
        
        # Encoder la requête utilisateur
        input_embedding = model.encode(query, convert_to_tensor=True)
        
        # Calculer les similarités
        similarities = util.cos_sim(input_embedding, review_embeddings)[0]
        
        # Attacher les scores au dataframe
        df['similarity_score'] = similarities.cpu().numpy()
        
        # Agréger par restaurant
        restaurant_df = (
            df.groupby('place_id')
            .agg(
                name=('place_name', 'first'),
                lat=('latitude', 'first'),
                lng=('longitude', 'first'),
                similarity=('similarity_score', 'max')
            )
            .reset_index()
            .sort_values('similarity', ascending=False)
        )
        
        restaurant_df['similarity'] = restaurant_df['similarity'].round(4)
        results = restaurant_df.to_dict(orient='records')
        
        print(f"✅ {len(results)} restaurants trouvés")
        return jsonify(results)
    
    except Exception as e:
        print(f" Erreur: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reviews/<place_id>', methods=['GET'])
def get_reviews(place_id):
    try:
        restaurant_reviews = df[df['place_id'] == place_id]['review_text'].tolist()
        reviews = [r for r in restaurant_reviews if r and len(r.strip()) > 10][:10]
        return jsonify({'reviews': reviews})
    except Exception as e:
        print(f" Erreur: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*50)
    print(" Serveur démarré sur http://localhost:8001")
    print("="*50 + "\n")
    app.run(debug=True, host='0.0.0.0', port=8001)
