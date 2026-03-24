import pandas as pd
import streamlit as st

st.title(" Book Recommendation System")

# =========================
# GOOGLE DRIVE FILE IDS
# =========================

books_url = "https://drive.google.com/uc?export=download&id=1rEE9L2f5x0lovm9Xyd2_QgnJe4HuBLe-"
ratings_url = "https://drive.google.com/uc?export=download&id=13bCAwIpp61k41IwjAGV00MVEnXzgqNJx"

# =========================
# LOAD DATA (CACHED)
# =========================

@st.cache_data
def load_data():
    # load files
    books = pd.read_csv(books_url, sep=';', encoding='latin-1', on_bad_lines='skip')
    ratings = pd.read_csv(ratings_url, sep=';', encoding='latin-1', on_bad_lines='skip')

    # keep needed columns
    books = books[['ISBN', 'Book-Title']]
    books['Book-Title'] = books['Book-Title'].str.lower().str.strip()

    # merge
    data = ratings.merge(books, on='ISBN')
    data = data.drop_duplicates(['User-ID', 'Book-Title'])

    # filter users
    user_counts = data['User-ID'].value_counts()
    active_users = user_counts[user_counts >= 10].index
    data = data[data['User-ID'].isin(active_users)]

    # filter books (IMPORTANT: reduce size)
    book_counts = data['Book-Title'].value_counts()
    popular_books = book_counts[book_counts >= 100].index
    data = data[data['Book-Title'].isin(popular_books)]

    # pivot
    pivot = data.pivot_table(index='User-ID', columns='Book-Title', values='Book-Rating')
    pivot = pivot.fillna(0)

    return pivot

# =========================
# LOAD DATA
# =========================

with st.spinner("Loading data... please wait ⏳"):
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
    sim = pivot.corrwith(x)
    sim = sim.sort_values(ascending=False)

    return sim.drop(book).head(5).index.tolist()

# =========================
# UI
# =========================

selected_book = st.selectbox("Select a Book", book_list)

if st.button("Recommend"):

    # call the function to get recommendations
    results = recommend(selected_book)

    # check if any books were returned
    if len(results) == 0:
        st.error("Book not found")

    else:
        st.subheader("📚 Recommended Books:")

        # print each book one by one
        count = 1
        for book in results:
            st.write(str(count) + ". " + book.title())
            count = count + 1
