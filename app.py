from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# --- Database Connection Function ---
def get_db_connection():
    conn = sqlite3.connect('curtain.db')
    conn.row_factory = sqlite3.Row
    return conn


# --- Home Page ---
@app.route('/')
def home():
    return render_template('home.html')


# --- Marketing Page ---
@app.route('/marketing', methods=['GET', 'POST'])
def marketing():
    conn = get_db_connection()
    
    if request.method == 'POST':
        customer_name = request.form['customer_name']
        phone_no = request.form['phone_no']
        conn.execute('INSERT INTO customer (customer_name, phone_no) VALUES (?, ?)',
                     (customer_name, phone_no))
        conn.commit()
        conn.close()
        return redirect(url_for('marketing'))

    customers = conn.execute('SELECT * FROM customer').fetchall()
    conn.close()
    return render_template('marketing.html', customers=customers)


@app.route('/salesperson', methods=['GET', 'POST'])
def salesperson():
    # Use a context manager for safety
    with get_db_connection() as conn:
        # Fetch customers
        customers = conn.execute('SELECT * FROM customer').fetchall()

        # Handle form submission
        if request.method == 'POST':
            customer_id = request.form['customer_id']
            type_ = request.form['type']
            quantity = request.form['quantity']
            address = request.form['address']

            # Insert order (SQLite auto-commits with context manager)
            conn.execute(
                'INSERT INTO "order" (customer_id, type, quantity, address) VALUES (?, ?, ?, ?)',
                (customer_id, type_, quantity, address)
            )

        # Fetch orders joined with customer
        orders = conn.execute('''
            SELECT o.order_id, c.customer_name, c.phone_no, o.type, o.quantity, o.address
            FROM "order" o
            JOIN customer c ON o.customer_id = c.customer_id
        ''').fetchall()

    # Connection is automatically closed here
    return render_template('salesperson.html', customers=customers, orders=orders)

@app.route('/measurement', methods=['GET', 'POST'])
def measurement():
    with get_db_connection() as conn:
        # Fetch all orders with customer info and (if available) measurement data
        orders = conn.execute('''
            SELECT o.order_id, c.customer_name, c.phone_no, o.address,
                   m.shade, m.dimensions
            FROM "order" o
            JOIN customer c ON o.customer_id = c.customer_id
            LEFT JOIN measurement m ON o.order_id = m.order_id
        ''').fetchall()

        # Handle form submission (insert or update measurement)
        if request.method == 'POST':
            order_id = request.form['order_id']
            shade = request.form['shade']
            dimensions = request.form['dimensions']

            # Check if this order already has a measurement record
            existing = conn.execute('SELECT * FROM measurement WHERE order_id = ?', (order_id,)).fetchone()

            if existing:
                # Update existing record
                conn.execute('UPDATE measurement SET shade = ?, dimensions = ? WHERE order_id = ?',
                             (shade, dimensions, order_id))
            else:
                # Insert new measurement
                conn.execute('INSERT INTO measurement (order_id, shade, dimensions) VALUES (?, ?, ?)',
                             (order_id, shade, dimensions))

    return render_template('measurement.html', orders=orders)


if __name__ == '__main__':
    app.run(debug=True)
