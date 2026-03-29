import pandas as pd
import numpy as np
import streamlit as st

# ================================
# PAGE SETUP
# ================================

# App title
st.title("Book Recommendation System")


# Google Drive file links
books_url = "https://drive.google.com/uc?export=download&id=1rEE9L2f5x0lovm9Xyd2_QgnJe4HuBLe-"
ratings_url = "https://drive.google.com/uc?export=download&id=13bCAwIpp61k41IwjAGV00MVEnXzgqNJx"


# ================================
# LOAD + CLEAN DATA
# ================================

@st.cache_data
def load_data():
    # Load both datasets
    books = pd.read_csv(books_url, sep=';', encoding='latin-1', on_bad_lines='skip')
    ratings = pd.read_csv(ratings_url, sep=';', encoding='latin-1', on_bad_lines='skip')

    # Keep only what we need
    books = books[['ISBN', 'Book-Title']]

    # Clean titles (lowercase + remove spaces)
    books['Book-Title'] = books['Book-Title'].str.lower().str.strip()

    # Merge ratings with book titles
    data = ratings.merge(books, on='ISBN')

    # Remove duplicate ratings
    data = data.drop_duplicates(['User-ID', 'Book-Title'])

    # Keep only users who rated at least 10 books
    user_counts = data['User-ID'].value_counts()
    active_users = user_counts[user_counts >= 10].index
    data = data[data['User-ID'].isin(active_users)]

    # Keep only popular books (100+ ratings)
    book_counts = data['Book-Title'].value_counts()
    popular_books = book_counts[book_counts >= 100].index
    data = data[data['Book-Title'].isin(popular_books)]

    # Create user-book matrix
    pivot = data.pivot_table(index='User-ID', columns='Book-Title', values='Book-Rating')
    pivot = pivot.fillna(0)

    return pivot


# ================================
# LOAD DATA
# ================================

with st.spinner("Loading data..."):
    pivot = load_data()

book_list = list(pivot.columns)


# ================================
# RECOMMENDATION FUNCTION
# ================================

def recommend(book):
    book = book.lower().strip()

    # If book not found
    if book not in pivot.columns:
        return []

    selected = pivot[book].values
    distances = {}

    # Compare with all other books
    for other in pivot.columns:
        if other == book:
            continue

        other_ratings = pivot[other].values

        # Euclidean distance
        distance = np.sqrt(np.sum((selected - other_ratings) ** 2))
        distances[other] = distance

    # Sort by similarity (smaller = better)
    sorted_books = sorted(distances, key=lambda b: distances[b])

    return sorted_books[:5]


# ================================
# UI
# ================================

selected_book = st.selectbox("Select a Book", book_list)

if st.button("Recommend"):
    results = recommend(selected_book)

    if len(results) == 0:
        st.error("Book not found.")
    else:
        st.subheader("Recommended Books:")

        for i, book in enumerate(results, 1):
            st.write(f"{i}. {book.title()}")
