import sqlite3
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, email, username, phone, password, profile_picture):
        self.id = id
        self.email = email
        self.username = username
        self.phone = phone
        self.password = password
        self.profile_picture = profile_picture

    def __repr__(self):
        return f'<User {self.username}>'
    
    def get_id(self):
        return self.id

    def get(user_id):
        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()

        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        connection.close()

        if row:
            return User(*row) 
        return None

    def set_email(self, new_email):
        self.email = new_email
    
    def set_username(self, new_username):
        self.username = new_username

    def set_phone(self, new_phone):
        self.phone = new_phone
    
    def set_password(self, new_pass):
        self.password = new_pass