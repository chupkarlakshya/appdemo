import pandas as pd
import numpy as np
import streamlit as st

# ================================
# STEP 1: SET UP THE PAGE
# ================================

# This sets the title that appears at the top of the web app
st.title(" Book Recommendation System")



# These are download links to two files stored on Google Drive:
# - books_url: contains book info (ISBN number and book title)
# - ratings_url: contains ratings (which user rated which book, and what score they gave)
books_url = "https://drive.google.com/uc?export=download&id=1rEE9L2f5x0lovm9Xyd2_QgnJe4HuBLe-"
ratings_url = "https://drive.google.com/uc?export=download&id=13bCAwIpp61k41IwjAGV00MVEnXzgqNJx"

# ================================
# STEP 3: LOAD AND CLEAN THE DATA
# ================================

# @st.cache_data means: "run this function once and remember the result"
# Without it, the app would reload the data every time you click a button (very slow!)
@st.cache_data
def load_data():

    # --- Load the raw files ---
    # sep=';' means the columns are separated by semicolons (not commas)
    # encoding='latin-1' handles special characters like accents
    # on_bad_lines='skip' ignores any rows that are broken/corrupted
    books = pd.read_csv(books_url, sep=';', encoding='latin-1', on_bad_lines='skip')
    ratings = pd.read_csv(ratings_url, sep=';', encoding='latin-1', on_bad_lines='skip')

    # --- Clean the books data ---
    # We only need two columns: the ISBN (unique book ID) and the title
    books = books[['ISBN', 'Book-Title']]

    # Make all titles lowercase and remove extra spaces
    # This prevents duplicates like "Harry Potter" and "harry potter" being treated differently
    books['Book-Title'] = books['Book-Title'].str.lower().str.strip()

    # --- Combine books and ratings into one table ---
    # This matches each rating with its book title using the ISBN
    data = ratings.merge(books, on='ISBN')

    # Remove duplicate entries (same user rating the same book twice)
    data = data.drop_duplicates(['User-ID', 'Book-Title'])

    # --- Filter out users who haven't rated many books ---
    # Users who only rated 1-2 books don't give us much useful information
    # We only keep users who rated AT LEAST 10 books
    user_counts = data['User-ID'].value_counts()
    active_users = user_counts[user_counts >= 10].index
    data = data[data['User-ID'].isin(active_users)]

    # --- Filter out books that aren't very popular ---
    # We only keep books rated by AT LEAST 100 different users
    book_counts = data['Book-Title'].value_counts()
    popular_books = book_counts[book_counts >= 100].index
    data = data[data['Book-Title'].isin(popular_books)]

    # --- Build the ratings matrix (pivot table) ---
    # Rows = users, Columns = books, Cells = rating given
    # Empty cells (user didn't rate that book) are filled with 0
    pivot = data.pivot_table(index='User-ID', columns='Book-Title', values='Book-Rating')
    pivot = pivot.fillna(0)

    return pivot


# ================================
# STEP 4: LOAD THE DATA
# ================================

with st.spinner("Loading data... please wait "):
    pivot = load_data()

# Get the list of all book titles (the column names of our table)
book_list = list(pivot.columns)


# ================================
# STEP 5: THE RECOMMENDATION LOGIC
# ================================

def recommend(book):
    # Make the input lowercase so it matches our cleaned data
    book = book.lower().strip()

    # Check if this book exists in our dataset
    if book not in pivot.columns:
        return []

    # Get the ratings column for the selected book as a numpy array
    # A numpy array is just a list of numbers that's fast to do maths on
    selected_book_ratings = pivot[book].values

    # --- Calculate Euclidean Distance ---
    # For each other book, we measure how "far apart" its ratings are
    # from the selected book's ratings.
    #
    # The formula is: distance = sqrt( sum of (a - b)^2 )
    # where a = selected book's ratings, b = another book's ratings
    #
    # A small distance means users rated both books very similarly -> good recommendation
    # A large distance means users rated them differently -> not a good match

    distances = {}

    for other_book in pivot.columns:
        # Skip comparing the book to itself
        if other_book == book:
            continue

        # Get the other book's ratings
        other_book_ratings = pivot[other_book].values

        # Calculate the Euclidean distance using numpy:
        # np.subtract gives us (a - b) for each user
        # ** 2 squares each difference
        # np.sum adds them all up
        # np.sqrt takes the square root
        distance = np.sqrt(np.sum((selected_book_ratings - other_book_ratings) ** 2))

        # Store the result
        distances[other_book] = distance

    # Sort by distance - smallest distance first (most similar books at the top)
    sorted_books = sorted(distances, key=lambda b: distances[b])

    # Return just the top 5 most similar book titles
    return sorted_books[:5]


# ================================
# STEP 6: BUILD THE USER INTERFACE
# ================================

# Show a dropdown menu with all available books
selected_book = st.selectbox("Select a Book", book_list)

# When the button is clicked, run the recommendation
if st.button("Recommend"):

    results = recommend(selected_book)

    if len(results) == 0:
        st.error("Book not found in our dataset.")
    else:
        st.subheader(" Recommended Books:")

        # Loop through results and display each one
        for count, book in enumerate(results, start=1):
            st.write(str(count) + ". " + book.title())
