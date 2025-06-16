from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# In-memory user store
users = {} # {username: User}
user_id_to_username = {} # {id: username}
next_user_id = 1

class User(UserMixin):
    def __init__(self, username, password):
        global next_user_id
        self.id = next_user_id
        next_user_id += 1
        self.username = username
        self.password_hash = generate_password_hash(password)
        users[username] = self
        user_id_to_username[self.id] = username

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def get_by_username(username):
        return users.get(username)

    @staticmethod
    def get_by_id(user_id):
        username = user_id_to_username.get(user_id)
        if username:
            return users.get(username)
        return None

    def __repr__(self):
        return f'<User {self.username}>'
