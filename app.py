from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from flask_bcrypt import Bcrypt
from datetime import datetime

# Initialize the Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'  # Database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secret_key_here'  # Secret key for sessions

# Initialize SQLAlchemy and other extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# Model for User (for login system)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)


# Model for Books
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    is_borrowed = db.Column(db.Boolean, default=False)


# User Loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Routes
@app.route('/')
@login_required
def home():
    return render_template('index.html')


# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Query the database to find the user by username
        user = User.query.filter_by(username=username).first()

        # Check if the user exists and the password matches
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)  # Log in the user
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login failed. Check your username and/or password.', 'danger')

    return render_template('login.html')


# Register Route (for creating a new user)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Create a new user
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# Logout Route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


# Library Management Routes
@app.route('/books')
@login_required
def list_books():
    books = Book.query.all()
    return render_template('list_books.html', books=books)


@app.route('/borrow/<int:book_id>', methods=['GET', 'POST'])
@login_required
def borrow_book(book_id):
    book = Book.query.get_or_404(book_id)
    if request.method == 'POST':
        book.is_borrowed = True
        db.session.commit()
        flash(f'You have borrowed "{book.title}" successfully.', 'success')
        return redirect(url_for('list_books'))
    return render_template('borrow.html', book=book)


@app.route('/return/<int:book_id>', methods=['GET', 'POST'])
@login_required
def return_book(book_id):
    book = Book.query.get_or_404(book_id)
    if request.method == 'POST':
        book.is_borrowed = False
        db.session.commit()
        flash(f'You have returned "{book.title}" successfully.', 'success')
        return redirect(url_for('list_books'))
    return render_template('return.html', book=book)


@app.route('/donate', methods=['GET', 'POST'])
@login_required
def donate_book():
    if request.method == 'POST':
        book_title = request.form['book_title']
        new_book = Book(title=book_title)
        db.session.add(new_book)
        db.session.commit()
        flash(f'Book "{book_title}" donated successfully!', 'success')
        return redirect(url_for('list_books'))
    return render_template('donate.html')


@app.route('/track')
@login_required
def track_books():
    books = Book.query.filter_by(is_borrowed=True).all()
    return render_template('track.html', books=books)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create all database tables
    app.run(debug=True)
