import re

import numpy as np
import pandas as pd


def _category_tags(category):
    category = str(category).lower().replace('vastrika', '')
    return re.findall(r'[a-z0-9]+', category)


def _rating_score(rating):
    rating = str(rating)
    stars = rating.count('★')
    return stars / max(len(rating), 1)


def get_recommendations(product_slug, catalog, limit=4):
    """Rank catalog items by category, price, and rating similarity."""
    if limit <= 0 or product_slug not in catalog:
        return []

    products = pd.DataFrame.from_records(
        [
            {'slug': slug, **product}
            for slug, product in catalog.items()
        ]
    )
    if products.empty:
        return []

    current_rows = products.index[products['slug'] == product_slug]
    if current_rows.empty:
        return []
    current_index = current_rows[0]

    tags = products['category'].map(_category_tags)
    eligible = products.index != current_index
    if 'jeans' in tags.iloc[current_index]:
        eligible &= tags.map(lambda category: 'jeans' in category).to_numpy()

    tag_matrix = pd.get_dummies(tags.explode()).groupby(level=0).max()
    tag_matrix = tag_matrix.reindex(products.index, fill_value=0)
    category_vectors = tag_matrix.to_numpy(dtype=float)
    norms = np.linalg.norm(category_vectors, axis=1)
    category_similarity = np.divide(
        category_vectors @ category_vectors[current_index],
        norms * norms[current_index],
        out=np.zeros(len(products), dtype=float),
        where=(norms * norms[current_index]) != 0,
    )

    prices = pd.to_numeric(products['price'], errors='raise').to_numpy(dtype=float)
    price_similarity = np.exp(
        -np.abs(prices - prices[current_index]) / max(prices[current_index], 1)
    )
    rating_similarity = products['rating'].map(_rating_score).to_numpy(dtype=float)
    scores = 0.8 * category_similarity + 0.15 * price_similarity + 0.05 * rating_similarity

    ranked = products.assign(score=scores)
    ranked = ranked[eligible].sort_values(
        ['score', 'slug'],
        ascending=[False, True],
        kind='stable',
    )

    return ranked.head(limit).drop(columns='score').to_dict(orient='records')
