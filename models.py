from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model with subscription tracking"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Trial tracking
    signup_date = db.Column(db.DateTime, default=datetime.utcnow)
    trial_days = db.Column(db.Integer, default=10)
    trial_used = db.Column(db.Boolean, default=False)
    
    # Subscription tracking
    subscription_type = db.Column(db.String(50), default='free')  # free, trial, basic, premium
    subscription_start = db.Column(db.DateTime)
    subscription_end = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Payment info
    last_payment_date = db.Column(db.DateTime)
    payment_status = db.Column(db.String(50), default='pending')  # pending, completed, failed
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def is_trial_active(self):
        """Check if user's trial period is still active"""
        # User is on trial if subscription_type is 'trial' or 'free' and trial hasn't been used
        if self.subscription_type in ('trial', 'free') and not self.trial_used:
            if self.signup_date:
                trial_end = self.signup_date + timedelta(days=self.trial_days)
                return datetime.utcnow() < trial_end
        return False
    
    def is_subscription_valid(self):
        """Check if subscription is still valid"""
        if self.subscription_type in ['basic', 'premium']:
            if self.subscription_end:
                return datetime.utcnow() < self.subscription_end
        return False
    
    def can_access(self):
        """Check if user can access satellite features"""
        return self.is_active and (self.is_trial_active() or self.is_subscription_valid())
    
    def days_remaining(self):
        """Get remaining days in trial or subscription"""
        if self.subscription_type in ('trial', 'free') and not self.trial_used:
            if self.signup_date:
                trial_end = self.signup_date + timedelta(days=self.trial_days)
                remaining = (trial_end - datetime.utcnow()).days
                return max(0, remaining)
        elif self.subscription_end:
            remaining = (self.subscription_end - datetime.utcnow()).days
            return max(0, remaining)
        return 0

class Subscription(db.Model):
    """Subscription plans"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # basic, premium
    price = db.Column(db.Float, nullable=False)
    duration_days = db.Column(db.Integer, default=30)
    features = db.Column(db.JSON)  # Array of features
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'duration_days': self.duration_days,
            'features': self.features
        }

class Transaction(db.Model):
    """Track user transactions"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='transactions')
    
    amount = db.Column(db.Float, nullable=False)
    subscription_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, completed, failed
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(50))  # card, paypal, etc
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
