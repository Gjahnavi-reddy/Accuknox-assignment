import requests
import sqlite3

# 1. Open Library API
url = "https://openlibrary.org/search.json"

params = {
    "q": "python",
    "limit": 10
}

# 2. Get data from Open Library
response = requests.get(url, params=params)

# Check if request was successful
if response.status_code == 200:

    data = response.json()

    # 3. Create SQLite database
    connection = sqlite3.connect("books.db")
    cursor = connection.cursor()

    # 4. Create books table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            author TEXT,
            publish_year INTEGER,
            openlibrary_key TEXT
        )
    """)

    # 5. Store books
    for book in data["docs"]:

        title = book.get("title", "Unknown")

        authors = ", ".join(
            book.get("author_name", [])
        )

        year = book.get("first_publish_year")

        key = book.get("key")

        cursor.execute("""
            INSERT INTO books
            (title, author, publish_year, openlibrary_key)
            VALUES (?, ?, ?, ?)
        """, (
            title,
            authors,
            year,
            key
        ))

    # 6. Save changes
    connection.commit()

    # 7. Close database
    connection.close()

    print("Books successfully saved!")

else:
    print("Failed to get data from Open Library")