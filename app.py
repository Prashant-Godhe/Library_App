from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import requests
import datetime
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'Prash'

# DB Helper
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/books')
def books():
    conn = get_db_connection()
    books = conn.execute('SELECT * FROM books').fetchall()
    conn.close()
    return render_template('books.html', books=books)

@app.route('/books/add', methods=('GET', 'POST'))
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        authors = request.form['authors']
        isbn = request.form['isbn']
        publisher = request.form['publisher']
        pages = request.form['pages']
        rent_fee = request.form['rent_fee']
        quantity = request.form['quantity']
        available_quantity = request.form['available_quantity']

        conn = get_db_connection()
        conn.execute('INSERT INTO books (title, authors, isbn, publisher, pages, rent_fee, quantity, available_quantity) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                     (title, authors, isbn, publisher, pages, rent_fee, quantity, available_quantity))
        conn.commit()
        conn.close()
        flash('Book added successfully!')
        return redirect(url_for('books'))

    return render_template('book_form.html', action='Add')

@app.route('/books/edit/<int:id>', methods=('GET', 'POST'))
def edit_book(id):
    conn = get_db_connection()
    book = conn.execute('SELECT * FROM books WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        title = request.form['title']
        authors = request.form['authors']
        isbn = request.form['isbn']
        publisher = request.form['publisher']
        pages = request.form['pages']
        rent_fee = request.form['rent_fee']
        quantity = request.form['quantity']
        available_quantity = request.form['available_quantity']

        conn.execute('''
            UPDATE books SET
                title = ?, authors = ?, isbn = ?, publisher = ?, pages = ?,
                rent_fee = ?, quantity = ?, available_quantity = ?
            WHERE id = ?
        ''', (title, authors, isbn, publisher, pages, rent_fee, quantity, available_quantity, id))

        conn.commit()
        conn.close()
        flash('Book updated!')
        return redirect(url_for('books'))

    conn.close()
    return render_template('book_form.html', book=book)


@app.route('/books/delete/<int:id>', methods=['GET', 'POST'])
def delete_book(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM books WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Book deleted!')
    return redirect(url_for('books'))

@app.route('/import', methods=['GET', 'POST'])
def import_books():
    if request.method == 'GET':
        return render_template('import_books.html')

    # POST method below
    try:
        data = request.get_json()
        num_books = int(data.get('num_books', 20))
        title = data.get('title', '')
        authors = data.get('authors', '')
        isbn = data.get('isbn', '')
        publisher = data.get('publisher', '')

        books_imported = 0
        page = 1

        conn = get_db_connection()
        cursor = conn.cursor()

        while books_imported < num_books:
            api_url = f"https://frappe.io/api/method/frappe-library?page={page}"
            if title:
                api_url += f"&title={title}"
            if authors:
                api_url += f"&authors={authors}"
            if isbn:
                api_url += f"&isbn={isbn}"
            if publisher:
                api_url += f"&publisher={publisher}"

            response = requests.get(api_url)
            if response.status_code != 200:
                break

            api_data = response.json()
            books_data = api_data.get('message', [])
            if not books_data:
                break

            for book in books_data:
                if books_imported >= num_books:
                    break
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO books 
                        (title, authors, isbn, publisher, pages, rent_fee, quantity, available_quantity)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        book.get('title'),
                        book.get('authors'),
                        book.get('isbn'),
                        book.get('publisher'),
                        book.get('num_pages'),
                        10.00,
                        1,
                        1
                    ))
                    books_imported += 1
                except Exception as e:
                    print(f"Error: {e}")
                    continue

            page += 1
            if len(books_data) < 20:
                break

        conn.commit()
        conn.close()
        return jsonify({'message': f'{books_imported} books imported successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/members')
def members():
    conn = get_db_connection()
    members = conn.execute('SELECT * FROM members').fetchall()
    conn.close()
    return render_template('members.html', members=members)

@app.route('/members/add', methods=['GET', 'POST'])
def add_member():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']

        conn = get_db_connection()
        conn.execute('INSERT INTO members (name, email, phone) VALUES (?, ?, ?)',
                     (name, email, phone))
        conn.commit()
        conn.close()
        flash('Member added successfully!')
        return redirect(url_for('members'))

    return render_template('member_form.html', member=None)

@app.route('/members/edit/<int:id>', methods=['GET', 'POST'])
def edit_member(id):
    conn = get_db_connection()
    member = conn.execute('SELECT * FROM members WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']

        conn.execute('UPDATE members SET name = ?, email = ?, phone = ? WHERE id = ?',
                     (name, email, phone, id))
        conn.commit()
        conn.close()
        flash('Member updated successfully!')
        return redirect(url_for('members'))

    conn.close()
    return render_template('member_form.html', member=member)

@app.route('/members/delete/<int:id>')
def delete_member(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM members WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Member deleted successfully!')
    return redirect(url_for('members'))

@app.route('/transactions')
def transactions():
    conn = get_db_connection()
    transactions = conn.execute('''
        SELECT t.*, 
               b.title AS book_title,
               m.name AS member_name,
               julianday('now') - julianday(t.issue_date) - t.days AS penalty_days
        FROM transactions t
        JOIN books b ON t.book_id = b.id
        JOIN members m ON t.member_id = m.id
    ''').fetchall()
    conn.close()
    return render_template('transactions.html', transactions=transactions)

@app.route('/transactions/assign', methods=['GET', 'POST'])
def assign_transaction():
    conn = get_db_connection()

    if request.method == 'POST':
        book_id = request.form['book_id']
        member_id = request.form['member_id']
        days = int(request.form['days'])
        amount_per_day = float(request.form['amount_per_day'])

        rent = days * amount_per_day
        issue_date = datetime.now().date()
        return_date = issue_date + timedelta(days=days)

        conn.execute('''
            INSERT INTO transactions (book_id, member_id, issue_date, days, return_date, amount_per_day, rent)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (book_id, member_id, issue_date, days, return_date, amount_per_day, rent))

        # Add rent to member's debt
        conn.execute('UPDATE members SET debt = debt + ? WHERE id = ?', (rent, member_id))

        # Decrease available quantity
        conn.execute('UPDATE books SET available_quantity = available_quantity - 1 WHERE id = ?', (book_id,))
        
        conn.commit()
        conn.close()
        flash('Book assigned and rent recorded.')
        return redirect(url_for('transactions'))

    books = conn.execute('SELECT id, title FROM books WHERE available_quantity > 0').fetchall()
    members = conn.execute('SELECT id, name FROM members').fetchall()
    conn.close()
    return render_template('assign_transaction.html', books=books, members=members)

@app.route('/transactions/return/<int:id>', methods=['POST'])
def return_book(id):
    conn = get_db_connection()

    # Get the transaction
    transaction = conn.execute('SELECT * FROM transactions WHERE id = ?', (id,)).fetchone()
    if not transaction:
        conn.close()
        flash('Transaction not found!')
        return redirect(url_for('transactions'))

    # Update return_date to current date
    return_date = datetime.now().date()
    conn.execute('UPDATE transactions SET return_date = ? WHERE id = ?', (return_date, id))

    # Increment book availability
    conn.execute('UPDATE books SET available_quantity = available_quantity + 1 WHERE id = ?', (transaction['book_id'],))

    conn.commit()
    conn.close()
    flash('Book returned successfully!')
    return redirect(url_for('transactions'))

@app.route('/transactions/receive/<int:id>', methods=['POST'])
def mark_as_received(id):
    conn = get_db_connection()
    txn = conn.execute('SELECT * FROM transactions WHERE id = ?', (id,)).fetchone()
    if not txn:
        conn.close()
        flash('Transaction not found!')
        return redirect(url_for('transactions'))

    conn.execute('UPDATE transactions SET return_date = ?, status = ? WHERE id = ?',
                 (datetime.now().date(), 'Returned', id))
    conn.execute('UPDATE books SET available_quantity = available_quantity + 1 WHERE id = ?', (txn['book_id'],))
    conn.commit()
    conn.close()
    flash('Book marked as received.')
    return redirect(url_for('transactions'))

@app.route('/transactions/penalty/<int:id>', methods=['POST'])
def add_penalty(id):
    conn = get_db_connection()

    txn = conn.execute('SELECT * FROM transactions WHERE id = ?', (id,)).fetchone()
    if not txn:
        conn.close()
        flash('Transaction not found.')
        return redirect(url_for('transactions'))

    penalty_amount = 10

    # Update penalty in transaction
    conn.execute('UPDATE transactions SET penalty = penalty + ? WHERE id = ?', (penalty_amount, id))

    # Update member's debt
    conn.execute('UPDATE members SET debt = debt + ? WHERE id = ?', (penalty_amount, txn['member_id']))

    conn.commit()
    conn.close()
    flash(f'Penalty of ₹{penalty_amount} added.')
    return redirect(url_for('transactions'))


if __name__ == '__main__':
    app.run(debug=True)
