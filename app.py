import os
from flask import Flask, render_template, request, url_for, redirect, flash, session
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
from uuid import uuid4

app = Flask(__name__)

load_dotenv(override=True)

app.secret_key = os.getenv('APP_SECRET_KEY')
app.config["MONGO_URI"] = os.getenv('MONGO_URI')
bcrypt = Bcrypt(app) 
mongo = PyMongo(app)

# Database collections
users = mongo.db.Users
    

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        return 'You want to login'
    else:
        return render_template('login.html', title='Login')


@app.route('/signup', methods=['GET', 'POST'])
def signup_page():
    if request.method == 'POST':
        email = request.form.get('email', None)
        password = request.form.get('password', None)

        if not email or not password:
            flash(message="Invalid signup data", category="danger")
            return redirect(url_for('signup_page'))

        # Check if email is taken
        if users.find_one({'email': email}):
            flash(message="A user with the provided email exists", category="warning")
            return redirect(url_for('signup_page'))
        
        password = bcrypt.generate_password_hash(password, 12).decode()
        user_id = str(uuid4().hex)
        users.insert_one({
            'email': email,
            'password': password,
            'user_id': user_id
        })
        flash(message="Welcome to debts and dough", category="success")
        session['user_id'] = user_id
        return redirect(url_for('home_page'))
    
    return render_template('signup.html', title='Signup')


@app.route('/')
def home_page():
    return render_template('index.html', title='Home page')


@app.route('/debts')
def debts_page():
    return render_template('debts.html', title='Debts')


@app.route('/dough')
def dough_page():
    return render_template('dough.html', title='Dough')


if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')