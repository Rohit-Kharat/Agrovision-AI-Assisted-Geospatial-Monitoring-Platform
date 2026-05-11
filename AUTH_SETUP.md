# Authentication System Setup Guide

## Overview
This guide will help you set up the complete authentication system with user accounts, 10-day free trial, subscription management, and payment integration for your Satellite Hub application.

## System Components

### 1. **Database Models** (`models.py`)
- **User Model**: Stores user credentials, trial status, subscription info
- **Subscription Model**: Defines subscription plans (Basic, Premium)
- **Transaction Model**: Tracks payment transactions

### 2. **Authentication Module** (`auth.py`)
- Login/Signup routes
- Session management
- Subscription validation
- Access control decorators

### 3. **Templates**
- `auth/login.html` - User login page
- `auth/signup.html` - User registration with 10-day trial
- `auth/subscription.html` - Subscription plans page
- `auth/dashboard.html` - User account dashboard
- `error.html` - Error page

### 4. **Flask App** (`app.py`)
- Integrated authentication
- Protected routes with `@subscription_required` decorator
- Database initialization

---

## Installation Steps

### Step 1: Install Dependencies

```bash
pip install -r requirements_auth.txt
```

**Dependencies installed:**
- Flask-SQLAlchemy: Database ORM
- Flask-Login: Session management
- Flask-WTF: Form handling & CSRF protection
- WTForms: Form validation
- Werkzeug: Password hashing

### Step 2: Set Environment Variables

Create a `.env` file in your project root:

```
SECRET_KEY=your-super-secret-key-change-in-production
DATABASE_URL=sqlite:///satellite.db
FLASK_ENV=development
```

**For production**, use a strong SECRET_KEY:
```bash
python -c 'import secrets; print(secrets.token_hex(32))'
```

### Step 3: Initialize Database

Run this Python script to create tables and seed default subscription plans:

```bash
python app.py
```

This will:
- Create SQLite database (`satellite.db`)
- Create all tables (User, Subscription, Transaction)
- Add default subscription plans (Basic: $9.99, Premium: $29.99)

---

## Features Implemented

### ✅ User Authentication
- **Signup**: New users get 10 days free trial automatically
- **Login**: Email + password authentication with "Remember me" option
- **Logout**: Secure session termination
- **Session Management**: Flask-Login handles user sessions

### ✅ Free Trial System
- All new users get 10-day free trial on signup
- Trial countdown shows in dashboard
- Automatic expiration after 10 days
- Users redirected to upgrade page when trial expires

### ✅ Subscription Plans
1. **Free Trial** - 10 days, limited features
2. **Basic** - $9.99/month
   - Advanced NDVI & SMI analysis
   - Up to 3 AOI areas
   - 100x daily requests
   - High resolution imagery
3. **Premium** - $29.99/month
   - Full analysis suite
   - Unlimited AOI areas
   - Unlimited daily requests
   - 24/7 dedicated support

### ✅ Access Control
- All satellite processing routes require authentication
- `@subscription_required` decorator checks:
  - User is logged in
  - Trial/subscription is still active
- Expired users redirected to upgrade page

### ✅ User Dashboard
- Shows subscription status
- Displays days remaining
- Account information
- Easy access to app and subscription management

---

## Route Protection

### Protected Routes

```python
@subscription_required  # New decorator
def process_satellite():
    # User must be authenticated AND have valid trial/subscription
    pass
```

**Protected routes include:**
- `/` (Main dashboard)
- `/generate_map`
- `/process_satellite`
- `/view_map`
- `/ndvi`
- `/ndvi_png`
- `/smi`

### Unprotected Routes (Public)

```python
/auth/login       # Login page
/auth/signup      # Registration page
/auth/subscription # Subscription page (shows available plans)
```

---

## Database Schema

### User Table
```
id              - Primary key
email           - Unique email
username        - Unique username
password_hash   - Hashed password
signup_date     - Account creation date
trial_days      - Number of trial days (default: 10)
trial_used      - Boolean flag
subscription_type - 'free', 'trial', 'basic', 'premium'
subscription_start - When subscription started
subscription_end   - When subscription expires
is_active       - Account active status
last_payment_date - Last payment timestamp
payment_status  - 'pending', 'completed', 'failed'
created_at      - Record creation time
updated_at      - Last update time
```

### Subscription Table
```
id              - Primary key
name            - 'basic' or 'premium'
price           - Monthly price in USD
duration_days   - Subscription duration (30 for monthly)
features        - JSON array of features
```

### Transaction Table
```
id              - Primary key
user_id         - Foreign key to User
amount          - Transaction amount
subscription_type - Which plan purchased
status          - 'pending', 'completed', 'failed'
transaction_date - When transaction occurred
payment_method  - Payment method used
```

---

## User Flow

### New User Journey
```
Visit Site
    ↓
Sign Up Page
    ↓
Create Account (email, username, password)
    ↓
Automatically Assigned 10-Day Trial
    ↓
Dashboard Shows Trial Countdown
    ↓
Access Satellite Features
    ↓
After 10 Days: Redirect to Upgrade Page
    ↓
Choose Plan → Process Payment
    ↓
Access Granted for Subscription Duration
```

### Returning User Journey
```
Login Page
    ↓
Enter Email + Password
    ↓
Check Trial/Subscription Status
    ↓
If Valid: Dashboard
    If Expired: Upgrade Page
```

---

## Key Functions & Methods

### In `models.py`

```python
# Check if trial is still active
user.is_trial_active()          # Returns bool

# Check if subscription is valid
user.is_subscription_valid()    # Returns bool

# Check if user can access features
user.can_access()               # Returns bool

# Get remaining days
user.days_remaining()           # Returns int
```

### In `auth.py`

```python
# Decorator to protect routes
@subscription_required
def my_route():
    pass

# Create trial user
user = User(
    email='user@example.com',
    username='username',
    subscription_type='trial',
    trial_days=10
)
user.set_password('password123')
db.session.add(user)
db.session.commit()

# Subscribe user
user.subscription_type = 'basic'
user.subscription_start = datetime.utcnow()
user.subscription_end = datetime.utcnow() + timedelta(days=30)
user.trial_used = True
db.session.commit()
```

---

## Testing the System

### Test Account Creation
```python
from app import app, db
from models import User

with app.app_context():
    # Create test user
    test_user = User(
        email='test@example.com',
        username='testuser',
        subscription_type='trial',
        trial_days=10
    )
    test_user.set_password('password123')
    db.session.add(test_user)
    db.session.commit()
    print("Test user created successfully")
```

### Test Login Flow
1. Navigate to `http://localhost:5000/auth/login`
2. Try logging in with non-existent account (should show error)
3. Navigate to signup: `http://localhost:5000/auth/signup`
4. Create new account
5. Should be redirected to dashboard
6. Dashboard shows 10-day trial countdown

### Test Access Control
1. Logout
2. Try accessing `/process_satellite` directly
3. Should redirect to login page
4. Login
5. Should see protected content

---

## Integration with Payment Gateway

### For Stripe Integration (Recommended)

Install Stripe:
```bash
pip install stripe
```

Add to `auth.py`:
```python
import stripe

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

@auth_bp.route('/subscribe/<int:sub_id>', methods=['POST'])
@login_required
def subscribe(sub_id):
    subscription = Subscription.query.get_or_404(sub_id)
    
    # Create Stripe payment
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {'name': subscription.name},
                'unit_amount': int(subscription.price * 100),
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=url_for('auth.subscription', _external=True),
        cancel_url=url_for('auth.subscription', _external=True),
    )
    return redirect(session.url, code=303)
```

### For PayPal Integration

Install PyPayPal:
```bash
pip install paypalrestsdk
```

Similar process to Stripe integration.

---

## Maintenance Tasks

### Check for Expired Trials/Subscriptions

```python
from app import app
from models import User, db
from datetime import datetime, timedelta

with app.app_context():
    expired_users = User.query.filter(
        User.subscription_end < datetime.utcnow()
    ).all()
    
    for user in expired_users:
        user.subscription_type = 'free'
        db.session.add(user)
    
    db.session.commit()
    print(f"Updated {len(expired_users)} expired subscriptions")
```

### Send Email Reminders

```python
# Before trial expires (1 day notification)
one_day_before = datetime.utcnow() + timedelta(days=1)
soon_to_expire = User.query.filter(
    (User.subscription_type == 'trial') &
    (User.signup_date + timedelta(days=9) <= one_day_before)
).all()

for user in soon_to_expire:
    # Send email to user.email
    send_trial_expiry_warning(user)
```

---

## Security Best Practices

1. **Never commit `.env` file** - Add to `.gitignore`
2. **Use strong SECRET_KEY** - Generate with secrets module
3. **HTTPS in Production** - Always use SSL/TLS
4. **Password Requirements** - Enforce minimum 6 characters (adjust as needed)
5. **CSRF Protection** - Enabled by Flask-WTF
6. **SQL Injection** - Protected by SQLAlchemy ORM
7. **XSS Protection** - Jinja2 escapes by default

---

## Common Issues & Solutions

### Issue: "User is not defined"
**Solution**: Make sure `models.py` is imported in `app.py`

### Issue: Database locked error
**Solution**: Close all connections and restart Flask app
```bash
# Delete the old database
rm satellite.db
# Restart: python app.py
```

### Issue: Login not working
**Solution**: 
1. Check if user exists: `User.query.filter_by(email='user@example.com').first()`
2. Verify password: `user.check_password('password')`
3. Check session config

### Issue: Subscription status not updating
**Solution**: Ensure `db.session.commit()` is called after modifications

---

## Next Steps

1. ✅ **Basic Auth Complete** - Users can sign up and login
2. ✅ **Trial System** - 10-day countdown working
3. ⚠️ **Payment Integration** - Add Stripe or PayPal (see above)
4. ⚠️ **Email Notifications** - Send reminder emails before trial expires
5. ⚠️ **Analytics** - Track user engagement and subscription status
6. ⚠️ **Admin Panel** - View all users, subscriptions, payments

---

## Support & Documentation

- **Flask-Login**: https://flask-login.readthedocs.io/
- **SQLAlchemy**: https://www.sqlalchemy.org/
- **Flask-SQLAlchemy**: https://flask-sqlalchemy.palletsprojects.com/
- **Werkzeug Security**: https://werkzeug.palletsprojects.com/security/

---

**Created**: May 11, 2026
**Last Updated**: May 11, 2026
**Status**: Ready for Testing
