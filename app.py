from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def home_page():
    return render_template('index.html', title='Home page')


@app.route('/login')
def login_page():
    return render_template('login.html', title='Login')


@app.route('/signup')
def signup_page():
    return render_template('signup.html', title='Signup')


@app.route('/debts')
def debts_page():
    return render_template('debts.html', title='Debts')


@app.route('/dough')
def dough_page():
    return render_template('dough.html', title='Dough')


if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')