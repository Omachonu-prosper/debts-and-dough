import os
from flask import Flask, render_template, request, url_for, redirect, flash, session
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
from uuid import uuid4
from datetime import datetime
from utils import timestamp

app = Flask(__name__)

load_dotenv(override=True)

app.secret_key = os.getenv('APP_SECRET_KEY')
app.config["MONGO_URI"] = os.getenv('MONGO_URI')
bcrypt = Bcrypt(app) 
mongo = PyMongo(app)

# Database collections
users = mongo.db.Users


@app.route('/signup', methods=['GET', 'POST'])
def signup_page():
    if request.method == 'POST':
        username = request.form.get('username', None)
        email = request.form.get('email', None)
        password = request.form.get('password', None)

        if not email or not password or not username:
            flash(message="Invalid signup data", category="danger")
            return redirect(url_for('signup_page'))

        # Check if email is taken
        if users.find_one({'email': email}):
            flash(message="A user with the provided email exists", category="warning")
            return redirect(url_for('signup_page'))
        
        password = bcrypt.generate_password_hash(password, 12).decode()
        user_id = str(uuid4().hex)
        users.insert_one({
            'username': username,
            'email': email,
            'password': password,
            'user_id': user_id,
            'debts': 0.0,
            'debts_display': '0.00',
            'dough': 0.0,
            'dough_display': '0.00',
            'transactions': [],
            'created_at': timestamp(),
            'last_login': timestamp()
        })
        flash(message="Welcome to debts and dough", category="success")
        session['user_id'] = user_id
        return redirect(url_for('home_page'))
    
    return render_template('signup.html', title='Signup')


@app.route('/login', methods=['GET', 'POST'])
def login_page():    
    if request.method == 'POST':
        email = request.form.get('email', None)
        password = request.form.get('password', None)

        if not email or not password:
            flash(message="Invalid login data", category="danger")
            return redirect(url_for('login_page'))

        # Check if email is exists
        user = users.find_one_and_update(
            {'email': email},
            {'$set': {'last_login': timestamp()}}
        )
        if not user:
            flash(message="Email not found", category="danger")
            return redirect(url_for('login_page'))
        
        user_password = user.get('password')
        if not bcrypt.check_password_hash(user_password, password):
            flash(message=f"Invalid password for {email}", category='danger')
            return redirect(url_for('login_page'))

        session['user_id'] = user.get('user_id')
        return redirect(url_for('home_page'))
    else:
        if session.get('user_id'):
            return redirect(url_for('home_page'))
        return render_template('login.html', title='Login')


@app.route('/logout')
def logout():
    session.pop('user_id')
    return redirect(url_for('login_page'))


@app.route('/')
def home_page():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login_page'))
    
    user = users.find_one({'user_id': user_id}, {'_id': 0})
    if not user:
        session.pop('user_id')
        return redirect(url_for('login_page'))
    return render_template('index.html', title='Home page', user=user)


@app.route('/debts', methods=['GET', 'POST'])
def debts_page():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login_page'))
    
    user = users.find_one({'user_id': user_id}, {'_id': 0})
    if not user:
        session.pop('user_id')
        return redirect(url_for('login_page'))
    
    if request.method == 'POST':
        increase_debt = request.form.get('increase_debt')

        if increase_debt:
            # create_transaction_debt(increase_debt, 'increase_debt', users)
            increase_debt = float(increase_debt)
            debt_display = user.get('debts') + increase_debt
            users.update_one(
                {'user_id': user_id},
                {'$push': {
                    'transactions': {
                        'type': 'debt',
                        'description': 'Increased Debt',
                        'amount': increase_debt,
                        'amount_display': format(increase_debt, ',.2f'),
                        'created_at': timestamp()
                    }
                },
                '$inc': {
                    'debts': increase_debt,
                },
                '$set': {
                    'debts_display': format(debt_display, ',.2f')
                }}
            )

        return redirect(url_for('debts_page'))         
     
    return render_template('debts.html', title='Debts', user=user)


@app.route('/dough')
def dough_page():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login_page'))
    
    user = users.find_one({'user_id': user_id}, {'_id': 0})
    if not user:
        session.pop('user_id')
        return redirect(url_for('login_page'))
    return render_template('dough.html', title='Dough', user=user)


if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')