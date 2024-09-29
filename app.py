import sqlite3
import os
from flask import Flask, render_template, request, url_for, flash, redirect
from werkzeug.utils import secure_filename
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash  # Import if you hash passwords
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
from User import User

load_dotenv()

secret_key = os.getenv('SECRET_KEY')

app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # or 'Strict'/'None'

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)

# For File Uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}3
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'static/uploads/')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 
app.secret_key =  secret_key

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload_profile_picture', methods=['POST'])
def upload_profile_picture():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('profile'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('profile'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # Update user's profile picture in the database
        username = current_user.username  # Assuming Flask-Login
        profile_picture_path = 'uploads/' + filename 
        update_user_profile_picture(username, profile_picture_path)
        
        return redirect(url_for('profile', username=username))

    return redirect(url_for('profile', username=username))

def update_user_profile_picture(username, profile_picture_path):
    # Connect to the SQLite database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Update the profile_picture column for the given user ID
    cursor.execute('''
        UPDATE users
        SET profile_picture = ?
        WHERE username = ?
    ''', (profile_picture_path, username))
    
    # Commit the changes and close the connection
    conn.commit()
    conn.close()


# gets databse connection
# opens connection to database.db and gives name-based access to columnds
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Gets note by id; If no id is found then we get 404 error
def get_note(note_id):
    conn = get_db_connection()
    note = conn.execute('SELECT * FROM notes WHERE id = ?',
                        (note_id,)).fetchone()
    conn.close()
    if note is None:
        abort(404)
    return note

# LOGIN ROUTE AND AUTHORIZATION
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()

        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        connection.close()

        print(f"Fetched row: {row}")

        if row:
            user = User(*row)
            if check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('main'))
            else:
                return redirect(url_for('login'))
        else:
           
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return "Welcome to your dashboard!"


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ----------------------------

@app.route('/main')
def main():
    # Opens database connection and fetches all notes
    # renders index.html and posts
    conn = get_db_connection()
    notes = conn.execute('SELECT * FROM notes').fetchall()
    conn.close()
    print(notes)
    return render_template('index.html', notes=notes)


# app route that takes postive integer for note_id
@app.route('/<int:note_id>')
def note(note_id):
    note = get_note(note_id)
    return render_template('note.html', note=note)

# Accepts GET and POST requests. 
# 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        priority = request.form.get('priority')

        if priority:
            priority_value = 1
        else:
            priority_value = 0

        if not title:
            flash('Title is required!')
        else:
            conn = get_db_connection()
            conn.execute('INSERT INTO notes (title, content, priority) VALUES (?, ?, ?)',
                         (title, content, priority_value))
            conn.commit()
            conn.close()
            return redirect(url_for('main'))
    return render_template('create.html')

# Be able to edit the notes that you make
@app.route('/<int:id>/edit', methods=('GET', 'POST'))
def edit(id):
    note = get_note(id)

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        priority = request.form.get('priority')

        if priority:
            priority_switch = 1
        else:
            priority_switch = 0

        if not title:
            flash('Title is required!')
        else:
            conn = get_db_connection()
            conn.execute('UPDATE notes SET title = ?, content = ?, priority = ?'
                         ' WHERE id = ?',
                         (title, content, priority_switch, id))
            conn.commit()
            conn.close()
            return redirect(url_for('main'))

    return render_template('edit.html', note=note)


@app.route('/<int:id>/delete', methods=('POST',))
def delete(id):
    post = get_note(id)
    conn = get_db_connection()
    conn.execute('DELETE FROM notes WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('main'))

@app.route('/<username>/profile', methods=['GET', 'POST'])
def profile(username):
    org_username = User.get(username)

    if request.method == 'POST':
        new_username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']

        conn = get_db_connection()
        conn.execute(
            'UPDATE users SET username = ?, email = ?, phone = ? WHERE username = ?',
            (new_username, email, phone, username)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('profile', username=new_username))


    return render_template('profile.html',org_username=org_username)
    

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', False))
