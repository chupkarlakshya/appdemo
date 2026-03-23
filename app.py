import pandas as pd
import streamlit as st

st.title("📚 Book Recommendation System")

# =========================
# GOOGLE DRIVE FILE IDS
# =========================

BOOKS_ID = "1rEE9L2f5x0lovm9Xyd2_QgnJe4HuBLe-"
RATINGS_ID = "13bCAwIpp61k41IwjAGV00MVEnXzgqNJx"

books_url = f"https://drive.google.com/uc?id={BOOKS_ID}"
ratings_url = f"https://drive.google.com/uc?id={RATINGS_ID}"

# =========================
# LOAD DATA
# =========================

@st.cache_data
def load_data():
    books = pd.read_csv(books_url, sep=';', encoding='latin-1', on_bad_lines='skip')
    ratings = pd.read_csv(ratings_url, sep=';', encoding='latin-1', on_bad_lines='skip')

    books = books[['ISBN', 'Book-Title']]
    books['Book-Title'] = books['Book-Title'].str.lower().str.strip()

    data = ratings.merge(books, on='ISBN')
    data = data.drop_duplicates(['User-ID', 'Book-Title'])

    # filter users
    user_counts = data['User-ID'].value_counts()
    active_users = user_counts[user_counts >= 10].index
    data = data[data['User-ID'].isin(active_users)]

    # filter books
    book_counts = data['Book-Title'].value_counts()
    popular_books = book_counts[book_counts >= 50].index
    data = data[data['Book-Title'].isin(popular_books)]

    pivot = data.pivot_table(index='User-ID', columns='Book-Title', values='Book-Rating')
    pivot = pivot.fillna(0)

    return pivot

pivot = load_data()

book_list = list(pivot.columns)

# =========================
# RECOMMEND FUNCTION
# =========================

def recommend(book):
    book = book.lower().strip()

    if book not in pivot.columns:
        return []

    x = pivot[book]
    sim = pivot.corrwith(x).sort_values(ascending=False)

    return sim.drop(book).head(5).index.tolist()

# =========================
# UI
# =========================

selected_book = st.selectbox("Select a Book", book_list)

if st.button("Recommend"):
    results = recommend(selected_book)

    if not results:
        st.write("❌ Book not found")
    else:
        st.subheader("📚 Recommended Books:")
        for i, b in enumerate(results, 1):
            st.write(f"{i}. {b.title()}")
