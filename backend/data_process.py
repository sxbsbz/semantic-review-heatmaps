"""
data_process.py
Nettoie la base de données restaurants
"""

import pandas as pd
import re
from typing import List


def remove_emoji(text: str) -> str:
    """
    Supprime les emojis d'un texte
    """
    if pd.isna(text):
        return ""
    
    # Pattern pour supprimer les emojis
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symboles
        "\U0001F680-\U0001F6FF"  # transport
        "\U0001F1E0-\U0001F1FF"  # drapeaux
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FA6F"
        "\U00002600-\U000026FF"
        "\U00002700-\U000027BF"
        "]+",
        flags=re.UNICODE
    )
    
    text = emoji_pattern.sub('', text)
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def clean_emojis(db: pd.DataFrame) -> pd.DataFrame:
    """
    Supprime tous les emojis de la base
    """
    text_columns = ['place_name', 'review_text', 'zone']
    
    for col in text_columns:
        if col in db.columns:
            db[col] = db[col].apply(remove_emoji)
    
    return db


def normalize_name(name: str) -> str:
    """
    Normalise un nom de restaurant
    """
    if pd.isna(name):
        return ""
    
    name = name.lower()
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', ' ', name)
    
    return name.strip()


def is_same_location(lat1: float, lng1: float, lat2: float, lng2: float) -> bool:
    """
    Vérifie si deux coordonnées sont proches (< 100m)
    """
    lat_diff = abs(lat1 - lat2)
    lng_diff = abs(lng1 - lng2)
    return lat_diff < 0.001 and lng_diff < 0.001


def is_duplicate(row1: pd.Series, row2: pd.Series) -> bool:
    """
    Vérifie si deux restaurants sont des doublons
    """
    # Même nom
    name1 = normalize_name(row1['place_name'])
    name2 = normalize_name(row2['place_name'])
    
    if name1 != name2:
        return False
    
    # Même localisation
    same_location = is_same_location(
        row1['latitude'], row1['longitude'],
        row2['latitude'], row2['longitude']
    )
    
    return same_location


def merge_reviews(reviews_list: List[str]) -> str:
    """
    Fusionne plusieurs ensembles de reviews en supprimant les doublons
    """
    all_reviews = []
    
    for reviews in reviews_list:
        if pd.notna(reviews) and reviews.strip():
            all_reviews.extend(reviews.split('\n'))
    
    # Supprimer les doublons
    seen = set()
    unique_reviews = []
    
    for review in all_reviews:
        review = review.strip()
        if review and review not in seen:
            seen.add(review)
            unique_reviews.append(review)
    
    return '\n'.join(unique_reviews)


def remove_duplicates(db: pd.DataFrame) -> pd.DataFrame:
    """
    Supprime les restaurants dupliqués
    """
    to_remove = set()
    
    for i in range(len(db)):
        if i in to_remove:
            continue
        
        row1 = db.iloc[i]
        reviews_to_merge = [row1['review_text']]
        
        for j in range(i + 1, len(db)):
            if j in to_remove:
                continue
            
            row2 = db.iloc[j]
            
            if is_duplicate(row1, row2):
                reviews_to_merge.append(row2['review_text'])
                to_remove.add(j)
        
        # Fusionner les reviews si des doublons ont été trouvés
        if len(reviews_to_merge) > 1:
            merged = merge_reviews(reviews_to_merge)
            db.at[i, 'review_text'] = merged
            db.at[i, 'review_count'] = len(merged.split('\n'))
    
    # Supprimer les doublons
    if to_remove:
        db = db.drop(list(to_remove)).reset_index(drop=True)
        print(f"{len(to_remove)} doublons supprimés")
    
    return db


def data_process(db: pd.DataFrame) -> pd.DataFrame:
    """
    Nettoie la base de données
    
    Args:
        db: DataFrame à nettoyer
    
    Returns:
        DataFrame nettoyé
    """
    print(f"Nettoyage: {len(db)} entrées")
    
    # Supprimer les emojis
    print("Suppression des emojis...")
    clean_db = clean_emojis(db.copy())
    
    # Supprimer les doublons
    print("Suppression des doublons...")
    clean_db = remove_duplicates(clean_db)
    
    # Supprimer les lignes avec données manquantes
    clean_db = clean_db.dropna(subset=['place_id', 'place_name'])
    clean_db = clean_db.reset_index(drop=True)
    
    print(f"Nettoyage terminé: {len(clean_db)} entrées")
    
    return clean_db


def load_db(path: str = "db_restaurants_aggregated.csv") -> pd.DataFrame:
    """
    Charge la base de données
    """
    return pd.read_csv(path)


def save_db(db: pd.DataFrame, path: str = "db_restaurants_clean.csv"):
    """
    Sauvegarde la base de données nettoyée
    """
    db.to_csv(path, index=False)
    print(f"Base sauvegardée: {path}")


if __name__ == "__main__":
    # Exemple d'utilisation
    db = load_db()
    print(f"Base chargée: {len(db)} entrées")
    
    # Nettoyer
    clean_db = data_process(db)
    
    # Sauvegarder
    save_db(clean_db)