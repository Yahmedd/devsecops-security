"""User model."""
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from . import db


class User(UserMixin, db.Model):
    """User model for authentication and orders."""
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    orders = db.relationship('Order', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and set user password."""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Verify user password."""
        return check_password_hash(self.password, password)

    def is_authenticated(self):
        """Check if user is authenticated."""
        return True

    def is_active(self):
        """Check if user is active."""
        return True

    def is_anonymous(self):
        """Check if user is anonymous."""
        return False

    def get_id(self):
        """Get user ID."""
        return str(self.id)
    
    def __repr__(self):
        return f'<User {self.username}>'
