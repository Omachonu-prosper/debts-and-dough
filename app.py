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
    
    transactions = user.get('transactions', [])
    
    debt_labels = []
    debt_values = []
    dough_labels = []
    dough_values = []

    current_debt = 0.0
    current_dough = 0.0

    # Sort transactions by date to ensure correct cumulative sum
    transactions.sort(key=lambda x: datetime.strptime(x.get('created_at', '').split(' ')[0], '%Y-%m-%d'))

    for transaction in transactions:
        date = transaction.get('created_at', '').split(' ')[0]
        amount = transaction['amount']
        transaction_type = transaction['type']

        if transaction_type == 'debt':
            if transaction['description'] == 'Increased Debt':
                current_debt += amount
            elif transaction['description'] == 'Reduced Debt':
                current_debt -= amount
            debt_labels.append(date)
            debt_values.append(current_debt)
        elif transaction_type == 'dough':
            if transaction['description'] == 'Increased Dough':
                current_dough += amount
            elif transaction['description'] == 'Reduced Dough':
                current_dough -= amount
            dough_labels.append(date)
            dough_values.append(current_dough)

    debt_chart_data = {
        'labels': debt_labels,
        'values': debt_values
    }
    dough_chart_data = {
        'labels': dough_labels,
        'values': dough_values
    }

    return render_template('index.html', title='Home page', user=user, 
                           debt_chart_data=debt_chart_data, 
                           dough_chart_data=dough_chart_data)


@app.route('/tracking-history')
def tracking_history_page():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login_page'))
    
    user = users.find_one({'user_id': user_id}, {'_id': 0})
    if not user:
        session.pop('user_id')
        return redirect(url_for('login_page'))
    
    user['transactions'] = user.get('transactions', [])[::-1]
    return render_template('tracking_history_page.html', title='Tracking History', user=user)


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
        reduce_debt = request.form.get('reduce_debt')

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
        elif reduce_debt:
            reduce_debt = float(reduce_debt)
            debt_display = user.get('debts') - reduce_debt
            users.update_one(
                {'user_id': user_id},
                {'$push': {
                    'transactions': {
                        'type': 'debt',
                        'description': 'Reduced Debt',
                        'amount': reduce_debt,
                        'amount_display': format(reduce_debt, ',.2f'),
                        'created_at': timestamp()
                    }
                },
                '$inc': {
                    'debts': - reduce_debt,
                },
                '$set': {
                    'debts_display': format(debt_display, ',.2f')
                }}
            )
        return redirect(url_for('debts_page'))         
     
    user['transactions'] = user.get('transactions', [])[::-1]
    return render_template('debts.html', title='Debts', user=user)


@app.route('/dough', methods=['GET', 'POST'])
def dough_page():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login_page'))
    
    user = users.find_one({'user_id': user_id}, {'_id': 0})
    if not user:
        session.pop('user_id')
        return redirect(url_for('login_page'))
    
    if request.method == 'POST':
        increase_dough = request.form.get('increase_dough')
        reduce_dough = request.form.get('reduce_dough')

        if increase_dough:
            # create_transaction_debt(increase_dough, 'increase_dough', users)
            increase_dough = float(increase_dough)
            dough = user.get('dough') + increase_dough
            users.update_one(
                {'user_id': user_id},
                {'$push': {
                    'transactions': {
                        'type': 'dough',
                        'description': 'Increased Dough',
                        'amount': increase_dough,
                        'amount_display': format(increase_dough, ',.2f'),
                        'created_at': timestamp()
                    }
                },
                '$inc': {
                    'dough': increase_dough,
                },
                '$set': {
                    'dough_display': format(dough, ',.2f')
                }}
            )
        elif reduce_dough:
            reduce_dough = float(reduce_dough)
            dough_display = user.get('dough') - reduce_dough
            users.update_one(
                {'user_id': user_id},
                {'$push': {
                    'transactions': {
                        'type': 'dough',
                        'description': 'Reduced Dough',
                        'amount': reduce_dough,
                        'amount_display': format(reduce_dough, ',.2f'),
                        'created_at': timestamp()
                    }
                },
                '$inc': {
                    'dough': - reduce_dough,
                },
                '$set': {
                    'dough_display': format(dough_display, ',.2f')
                }}
            )
        return redirect(url_for('dough_page'))
    
    user['transactions'] = user.get('transactions', [])[::-1]
    return render_template('dough.html', title='Dough', user=user)


if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')