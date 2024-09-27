from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from datetime import datetime
import mysql.connector.pooling

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Database configuration with connection pooling
db_config = {
    'host': 'database-1.ctuw4ek62fgr.ap-south-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'Sunder34$2010',
    'database': 'hotel123'
}

cnxpool = mysql.connector.pooling.MySQLConnectionPool(pool_name="mypool",
                                                      pool_size=5,
                                                      **db_config)

# Function to establish a database connection
def get_db_connection():
    try:
        return cnxpool.get_connection()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

# Pricing per adult
PRICE_PER_ADULT = {
    1: 100,  # Price for 1 adult
    2: 180,  # Price for 2 adults (discounted for couples)
    3: 250,  # Price for 3 adults
    4: 300   # Price for 4 adults
}

# Home Route
@app.route('/')
def home():
    return render_template('home.html')

# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        mobile_number = request.form['mobile_number']

        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute("INSERT INTO users (name, email, password, mobile_number) VALUES (%s, %s, %s, %s)",
                               (name, email, password, mobile_number))
                connection.commit()
                flash("Thanks for registering!", "success")
                return redirect(url_for('login'))
            except mysql.connector.Error as err:
                flash(f"Error: {err}", "danger")
            finally:
                cursor.close()
                connection.close()
        else:
            flash("Database connection failed!", "danger")
    return render_template('register.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
                user = cursor.fetchone()

                if user:
                    session['user_id'] = user['id']
                    session['username'] = user['name']
                    flash("Login successful!", "success")
                    return redirect(url_for('check_rooms'))
                else:
                    flash("Invalid login. Please try again.", "danger")
            except mysql.connector.Error as err:
                flash(f"Error: {err}", "danger")
            finally:
                cursor.close()
                connection.close()
        else:
            flash("Database connection failed!", "danger")
    return render_template('login.html')

# Check Rooms Route
@app.route('/check_rooms', methods=['GET', 'POST'])
def check_rooms():
    if request.method == 'POST':
        room_type = request.form['room_type']
        return redirect(url_for('book', room_type=room_type))

    return render_template('check_rooms.html')

# Book Route
@app.route('/book/<room_type>', methods=['GET', 'POST'])
def book(room_type):
    if request.method == 'GET':
        return render_template('booking.html', room_type=room_type, price_per_adult=PRICE_PER_ADULT)

    if request.method == 'POST':
        num_people = int(request.form['num_people'])
        check_in = request.form['check_in']
        check_out = request.form['check_out']
        special_requests = request.form['special_requests']
        payment_mode = request.form['payment_mode']
        total_price = request.form['total_price']

        # Get user ID from session (assuming user is logged in)
        user_id = session.get('user_id')

        # Calculate the number of days
        check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
        check_out_date = datetime.strptime(check_out, "%Y-%m-%d")
        days = (check_out_date - check_in_date).days

        # Calculate the total price based on the number of adults and days
        total_price = PRICE_PER_ADULT.get(num_people, 0) * days

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO bookings (user_id, room_type, num_people, check_in, check_out, 
            special_requests, payment_mode, total_price)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_id, room_type, num_people, check_in, check_out, special_requests, payment_mode, total_price))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect('/thank_you')

# Thank You Route
@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

# My Bookings Route
@app.route('/my_bookings')
def my_bookings():
    user_id = session.get('user_id')  # Get user ID from session
    if not user_id:
        flash("You need to log in to view your bookings.", "danger")
        return redirect(url_for('login'))

    connection = get_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM bookings WHERE user_id=%s", (user_id,))
            bookings = cursor.fetchall()  # Fetch all bookings for the user
            return render_template('my_bookings.html', bookings=bookings)  # Render bookings
        except mysql.connector.Error as err:
            flash(f"Error: {err}", "danger")
        finally:
            cursor.close()
            connection.close()
    else:
        flash("Database connection failed!", "danger")
    
    return render_template('my_bookings.html', bookings=[])


if __name__ == '__main__':
    app.run(debug=True)