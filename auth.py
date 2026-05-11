from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Subscription, Transaction
from datetime import datetime, timedelta
from functools import wraps
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def subscription_required(f):
    """Decorator to check if user has valid subscription"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in first.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not current_user.can_access():
            flash('Your trial/subscription has expired. Please upgrade.', 'warning')
            return redirect(url_for('auth.subscription'))
        
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            # Convert remember checkbox value to a proper boolean.
            # request.form.get('remember') returns the string "true" or None.
            remember = bool(request.form.get('remember'))

            # Make the session permanent so it survives browser restarts
            # even without "remember me" (uses PERMANENT_SESSION_LIFETIME).
            session.permanent = True

            login_user(user, remember=remember)
            logger.info("User %s logged in (remember=%s)", user.email, remember)

            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration with 10-day free trial"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not all([email, username, password, confirm_password]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('auth.signup'))
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.signup'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('auth.signup'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.signup'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return redirect(url_for('auth.signup'))
        
        # Create new user with 10-day trial
        user = User(
            email=email,
            username=username,
            signup_date=datetime.utcnow(),
            subscription_type='trial',
            trial_days=10,
            trial_used=False
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'Account created! You have {user.trial_days} days free trial.', 'success')
        login_user(user)
        return redirect(url_for('index'))
    
    return render_template('auth/signup.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/subscription')
@login_required
def subscription():
    """Subscription management page"""
    subscriptions = Subscription.query.all()
    user_days_remaining = current_user.days_remaining()
    
    return render_template('auth/subscription.html', 
                          subscriptions=subscriptions,
                          user=current_user,
                          days_remaining=user_days_remaining)

@auth_bp.route('/subscribe/<int:sub_id>', methods=['POST'])
@login_required
def subscribe(sub_id):
    """Subscribe to a plan"""
    subscription = Subscription.query.get_or_404(sub_id)
    
    # Create transaction record
    transaction = Transaction(
        user_id=current_user.id,
        amount=subscription.price,
        subscription_type=subscription.name,
        status='pending'
    )
    
    # Update user subscription
    current_user.subscription_type = subscription.name
    current_user.subscription_start = datetime.utcnow()
    current_user.subscription_end = datetime.utcnow() + timedelta(days=subscription.duration_days)
    current_user.trial_used = True
    
    db.session.add(transaction)
    db.session.commit()
    
    flash(f'Subscribed to {subscription.name} plan!', 'success')
    return redirect(url_for('index'))

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    return render_template('auth/dashboard.html', user=current_user)
