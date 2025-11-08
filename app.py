from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)
# Database Connection Helper

def get_db_connection():
    conn = sqlite3.connect('curtain.db', timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


# Role Access IDs

ROLE_IDS = {
    'owner': 'OWN123',
    'marketing': 'MKT456',
    'salesperson': 'SLS789',
    'measurement': 'MSR321',
    'manufacturer': 'MFR654',
    'delivery': 'DLV987'
}


# Marketing Page 

@app.route('/marketing', methods=['GET', 'POST'])
def marketing():
    """
    Marketing Person:
    - Views all customers
    - Adds new customers (name + phone)
    - Page uses frontend popup authentication (JS-based)
    """

    with get_db_connection() as conn:
        # Handle form submission (add new customer)
        if request.method == 'POST':
            customer_name = request.form.get('customer_name')
            phone_no = request.form.get('phone_no')

            if customer_name and phone_no:
                conn.execute(
                    'INSERT INTO customer (customer_name, phone_no) VALUES (?, ?)',
                    (customer_name, phone_no)
                )

        # Fetch all customers (latest first)
        customers = conn.execute(
            'SELECT * FROM customer ORDER BY customer_id DESC'
        ).fetchall()

    # Render the page
    return render_template('marketing.html', customers=customers)

#salesperson page
@app.route('/salesperson', methods=['GET', 'POST'])
def salesperson():
    """
    Salesperson Page:
    - Displays customer list (from Marketing)
    - Adds type, quantity, and address for existing customers
    - Uses popup-based UID authentication
    """

    with get_db_connection() as conn:
        # Handle form submission (add order)
        if request.method == 'POST':
            customer_id = request.form.get('customer_id')
            type_ = request.form.get('type')
            quantity = request.form.get('quantity')
            address = request.form.get('address')

            if customer_id and type_ and quantity and address:
                conn.execute(
                    'INSERT INTO "order" (customer_id, type, quantity, address) VALUES (?, ?, ?, ?)',
                    (customer_id, type_, quantity, address)
                )

        # Fetch customer + their order data
        orders = conn.execute('''
            SELECT 
                o.order_id,
                c.customer_name,
                c.phone_no,
                o.type,
                o.quantity,
                o.address
            FROM "order" o
            JOIN customer c ON o.customer_id = c.customer_id
            ORDER BY o.order_id DESC
        ''').fetchall()

        # Fetch customers to populate dropdown
        customers = conn.execute('SELECT * FROM customer ORDER BY customer_id DESC').fetchall()

    return render_template('salesperson.html', orders=orders, customers=customers)

#Measurement page
@app.route('/measurement', methods=['GET', 'POST'])
def measurement():
    """
    Measurement Person Page:
    - Displays customers & order details
    - Allows adding shade and dimensions
    - Popup-based UID authentication (MSR321)
    """

    with get_db_connection() as conn:
        # Handle new measurement entry
        if request.method == 'POST':
            order_id = request.form.get('order_id')
            shade = request.form.get('shade')
            dimensions = request.form.get('dimensions')

            if order_id and shade and dimensions:
                existing = conn.execute(
                    'SELECT * FROM measurement WHERE order_id = ?', (order_id,)
                ).fetchone()

                if existing:
                    conn.execute(
                        'UPDATE measurement SET shade = ?, dimensions = ? WHERE order_id = ?',
                        (shade, dimensions, order_id)
                    )
                else:
                    conn.execute(
                        'INSERT INTO measurement (order_id, shade, dimensions) VALUES (?, ?, ?)',
                        (order_id, shade, dimensions)
                    )

        # Fetch all relevant data for table
        records = conn.execute('''
            SELECT 
                o.order_id,
                c.customer_name,
                c.phone_no,
                o.address,
                o.type,
                o.quantity,
                m.shade,
                m.dimensions
            FROM "order" o
            JOIN customer c ON o.customer_id = c.customer_id
            LEFT JOIN measurement m ON o.order_id = m.order_id
            ORDER BY o.order_id DESC
        ''').fetchall()

        # Orders dropdown for adding new data
        orders = conn.execute('''
            SELECT o.order_id, c.customer_name, c.phone_no
            FROM "order" o
            JOIN customer c ON o.customer_id = c.customer_id
            ORDER BY o.order_id DESC
        ''').fetchall()

    return render_template('measurement.html', records=records, orders=orders)

#Manufacturer page
@app.route('/manufacturer', methods=['GET', 'POST'])
def manufacturer():
    """
    Manufacturer Page:
    - Displays full customer, order, and measurement details
    - Allows marking product as Ready (Yes/No)
    - Popup-based UID (MFR654)
    """

    with get_db_connection() as conn:
        # Handle Ready status update
        if request.method == 'POST':
            order_id = request.form.get('order_id')
            ready_status = request.form.get('ready')

            if order_id and ready_status:
                existing = conn.execute(
                    'SELECT * FROM manufacturer WHERE order_id = ?', (order_id,)
                ).fetchone()

                if existing:
                    conn.execute(
                        'UPDATE manufacturer SET ready = ? WHERE order_id = ?',
                        (ready_status, order_id)
                    )
                else:
                    conn.execute(
                        'INSERT INTO manufacturer (order_id, ready) VALUES (?, ?)',
                        (order_id, ready_status)
                    )

        # Fetch full order info with measurements
        records = conn.execute('''
            SELECT 
                o.order_id,
                c.customer_name,
                c.phone_no,
                o.address,
                o.type,
                o.quantity,
                m.shade,
                m.dimensions,
                mf.ready
            FROM "order" o
            JOIN customer c ON o.customer_id = c.customer_id
            LEFT JOIN measurement m ON o.order_id = m.order_id
            LEFT JOIN manufacturer mf ON o.order_id = mf.order_id
            ORDER BY o.order_id DESC
        ''').fetchall()

    return render_template('manufacturer.html', records=records)

#Delivery page
from datetime import datetime

@app.route('/delivery', methods=['GET', 'POST'])
def delivery():
    """
    Delivery Person Page:
    - Shows all 'Ready' orders
    - Allows marking as Delivered (auto-saves date)
    - Popup-based UID (DLV987)
    """

    with get_db_connection() as conn:
        # Handle delivery status update
        if request.method == 'POST':
            order_id = request.form.get('order_id')
            status = request.form.get('status')

            if order_id and status:
                if status == 'Delivered':
                    current_date = datetime.now().strftime("%Y-%m-%d")  # Only date
                else:
                    current_date = None

                existing = conn.execute(
                    'SELECT * FROM delivery WHERE order_id = ?', (order_id,)
                ).fetchone()

                if existing:
                    conn.execute(
                        'UPDATE delivery SET status = ?, date = ? WHERE order_id = ?',
                        (status, current_date, order_id)
                    )
                else:
                    conn.execute(
                        'INSERT INTO delivery (order_id, status, date) VALUES (?, ?, ?)',
                        (order_id, status, current_date)
                    )

        # Fetch data for all ready orders
        records = conn.execute('''
            SELECT 
                o.order_id,
                c.customer_name,
                c.phone_no,
                o.address,
                mf.ready,
                d.status,
                d.date
            FROM "order" o
            JOIN customer c ON o.customer_id = c.customer_id
            LEFT JOIN manufacturer mf ON o.order_id = mf.order_id
            LEFT JOIN delivery d ON o.order_id = d.order_id
            WHERE mf.ready = 'Yes'
            ORDER BY o.order_id DESC
        ''').fetchall()

    return render_template('delivery.html', records=records)

# Owner page
@app.route('/owner')
def owner():
    """
    Owner Dashboard:
    - Displays everything from all roles
    - Popup-based UID (OWN123)
    - Search + Date Filter + Show More/Less
    """

    with get_db_connection() as conn:
        records = conn.execute('''
            SELECT 
                c.customer_name,
                c.phone_no,
                o.order_id,
                o.type,
                o.quantity,
                o.address,
                m.shade,
                m.dimensions,
                mf.ready,
                d.status AS delivery_status,
                d.date AS delivery_date
            FROM customer c
            LEFT JOIN "order" o ON c.customer_id = o.customer_id
            LEFT JOIN measurement m ON o.order_id = m.order_id
            LEFT JOIN manufacturer mf ON o.order_id = mf.order_id
            LEFT JOIN delivery d ON o.order_id = d.order_id
            ORDER BY o.order_id DESC
        ''').fetchall()

    return render_template('owner.html', records=records)


# Home Page (Optional Redirect)

@app.route('/')
def home():
    return render_template('home.html')


# Unauthorized Page (If needed later)

@app.route('/unauthorized/<role>')
def unauthorized(role):
    return render_template('unauthorized.html', role=role)


# Run the Flask App

if __name__ == '__main__':
    app.run(debug=True)


