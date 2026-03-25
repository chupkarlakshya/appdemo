import pandas as pd
import streamlit as st

# ================================
# STEP 1: SET UP THE PAGE
# ================================

# This sets the title that appears at the top of the web app
st.title(" Book Recommendation System")

# ================================
# STEP 2: LINKS TO OUR DATA FILES
# ================================

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
    # This prevents duplicates like "Harry Potter" and "harry potter" being treated as different books
    books['Book-Title'] = books['Book-Title'].str.lower().str.strip()

    # --- Combine books and ratings into one table ---
    # This matches each rating with its book title using the ISBN
    data = ratings.merge(books, on='ISBN')

    # Remove duplicate entries (same user rating the same book twice)
    data = data.drop_duplicates(['User-ID', 'Book-Title'])

    # --- Filter out users who haven't rated many books ---
    # Users who only rated 1-2 books don't give us much useful information
    # We only keep users who rated AT LEAST 10 books
    user_counts = data['User-ID'].value_counts()       # count how many books each user rated
    active_users = user_counts[user_counts >= 10].index  # get IDs of users with 10+ ratings
    data = data[data['User-ID'].isin(active_users)]    # keep only rows from those users

    # --- Filter out books that aren't very popular ---
    # A book rated by only 2 people doesn't help us find patterns
    # We only keep books rated by AT LEAST 100 different users
    book_counts = data['Book-Title'].value_counts()         # count how many users rated each book
    popular_books = book_counts[book_counts >= 100].index   # get titles with 100+ ratings
    data = data[data['Book-Title'].isin(popular_books)]     # keep only those books

    # --- Build the ratings matrix (pivot table) ---
    # This creates a big table where:
    #   - Each ROW is a user
    #   - Each COLUMN is a book
    #   - Each CELL is the rating that user gave that book
    # If a user didn't rate a book, we fill the empty cell with 0
    pivot = data.pivot_table(index='User-ID', columns='Book-Title', values='Book-Rating')
    pivot = pivot.fillna(0)

    return pivot


# ================================
# STEP 4: LOAD THE DATA
# ================================

# Show a loading message while the data is being fetched
with st.spinner("Loading data... please wait "):
    pivot = load_data()

# Get the list of all book titles (these are the column names of our table)
book_list = list(pivot.columns)


# ================================
# STEP 5: THE RECOMMENDATION LOGIC
# ================================

def recommend(book):
    # Make the input lowercase so it matches our cleaned data
    book = book.lower().strip()

    # Check if this book exists in our dataset
    if book not in pivot.columns:
        return []  # Return an empty list if the book wasn't found

    # Get the column of ratings for the selected book
    # This is a list of how every user rated this book
    selected_book_ratings = pivot[book]

    # Compare this book's ratings against every other book's ratings
    # corrwith() calculates the "correlation" - basically asking:
    # "Do the same users who liked THIS book also tend to like OTHER books?"
    # The result is a score between -1 and 1 for each book
    # A score close to 1 = very similar taste, close to 0 = unrelated
    similarity_scores = pivot.corrwith(selected_book_ratings)

    # Sort the books from most similar to least similar
    similarity_scores = similarity_scores.sort_values(ascending=False)

    # Remove the selected book itself from the results (it would always be #1)
    # Then return the top 5 most similar books
    top_5 = similarity_scores.drop(book).head(5)

    return top_5.index.tolist()  # .index gives us the book titles, .tolist() converts to a list


# ================================
# STEP 6: BUILD THE USER INTERFACE
# ================================

# Show a dropdown menu with all available books
selected_book = st.selectbox("Select a Book Which you like", book_list)

# Show a button — when clicked, it runs the code inside the if block
if st.button("Recommend"):

    # Call our recommend function with the chosen book
    results = recommend(selected_book)

    # If no books were returned, show an error message
    if len(results) == 0:
        st.error("Book not found in our dataset.")

    # Otherwise, display the recommended books
    else:
        st.subheader(" Recommended Books:")

        # Loop through the results and print each one
        # We use enumerate to get a count (1, 2, 3...) alongside each book title
        for count, book in enumerate(results, start=1):
            # .title() capitalizes the first letter of each word
            st.write(str(count) + ". " + book.title())
