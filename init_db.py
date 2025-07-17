import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Books table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    authors TEXT,
    isbn TEXT UNIQUE,
    publisher TEXT,
    pages INTEGER,
    rent_fee REAL,
    quantity INTEGER DEFAULT 1,
    available_quantity INTEGER DEFAULT 1
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    phone TEXT,
    debt REAL DEFAULT 0
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER,
    member_id INTEGER,
    issue_date DATE,
    days INTEGER,
    return_date DATE,
    penalty INTEGER DEFAULT 0,
    status TEXT DEFAULT 'Issued',
    amount_per_day REAL DEFAULT 0,
    rent REAL DEFAULT 0,
    FOREIGN KEY (book_id) REFERENCES books(id),
    FOREIGN KEY (member_id) REFERENCES members(id)
)
''')

conn.commit()
conn.close()
print("Database initialized.")
