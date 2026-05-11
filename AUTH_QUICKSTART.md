# Authentication Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Install Dependencies
```bash
pip install -r requirements_auth.txt
```

### 2. Run Setup Script
```bash
python setup_auth.py
```

This will:
- Create `.env` file with secret key
- Initialize SQLite database
- Create subscription plans
- (Optional) Create test user

### 3. Start the App
```bash
python app.py
```

### 4. Open in Browser
```
http://localhost:5000
```

---

## 📋 User Journeys

### For New Users
```
1. Click "Sign Up" on login page
2. Enter email, username, password
3. Account created → 10-day free trial starts
4. Dashboard shows countdown timer
5. Full access to satellite analysis tools
```

### For Existing Users
```
1. Enter email & password on login
2. Dashboard shows subscription status
3. If trial/subscription active → Full access
4. If expired → Redirect to upgrade page
```

### Subscription Upgrade
```
1. Click "View Plans" on dashboard
2. See 3 options: Free Trial, Basic ($9.99), Premium ($29.99)
3. Click "Subscribe Now"
4. (TODO: Payment processing)
5. Subscription activated
```

---

## 🔐 Default Credentials (After Setup)

If you create a test account, use those credentials to login.

**Test Account Created During Setup:**
- Email: (whatever you entered)
- Password: (whatever you entered)
- Trial: 10 days

---

## 📁 File Structure

```
Satellite/
├── app.py                      # Main Flask app with auth integration
├── models.py                   # Database models (User, Subscription, Transaction)
├── auth.py                     # Authentication routes and logic
├── setup_auth.py               # Quick setup script
├── requirements_auth.txt       # Python dependencies
├── AUTH_SETUP.md               # Detailed documentation
├── AUTH_QUICKSTART.md          # This file
├── .env                        # Environment variables (created by setup)
├── satellite.db                # SQLite database (created by setup)
│
├── templates/
│   ├── auth/
│   │   ├── login.html          # Login page
│   │   ├── signup.html         # Registration page
│   │   ├── subscription.html   # Plans & upgrade
│   │   └── dashboard.html      # User account dashboard
│   ├── index.html              # Main dashboard (protected)
│   └── error.html              # Error page
│
├── static/
│   ├── css/
│   └── js/
│
└── [other satellite processing files]
```

---

## 🎯 Key Features

### ✅ Implemented
- [x] User registration with email & password
- [x] Secure login with session management
- [x] 10-day automatic free trial for new users
- [x] Trial countdown in dashboard
- [x] Subscription plan selection (Basic, Premium)
- [x] Access control - routes protected by authentication
- [x] User dashboard with account info
- [x] Automatic redirect on trial expiration

### 🔄 In Development
- [ ] Payment processing (Stripe/PayPal integration)
- [ ] Email notifications (trial expiry reminders)
- [ ] Subscription auto-renewal
- [ ] User activity logging
- [ ] Admin panel for user management

---

## 🛡️ Security Features

✅ **Passwords**: Hashed with Werkzeug (not stored as plain text)
✅ **Sessions**: Secure Flask-Login session management
✅ **CSRF Protection**: Built-in with Flask-WTF
✅ **SQL Injection**: Protected by SQLAlchemy ORM
✅ **XSS Protection**: Template escaping by default
✅ **Environment Variables**: Sensitive keys in .env (not in code)

---

## 🧪 Testing

### Test Login
```bash
# 1. Start Flask app
python app.py

# 2. Open browser
http://localhost:5000

# 3. Try signup with test credentials
# 4. Should see dashboard with 10-day trial
```

### Test Access Control
```bash
# 1. Logout
# 2. Try accessing protected route directly:
http://localhost:5000/generate_map

# 3. Should redirect to login page
```

### Test Trial Expiration
```bash
# Manually set trial expiration date
python -c "
from app import app, db
from models import User
from datetime import datetime, timedelta

with app.app_context():
    user = User.query.filter_by(email='test@example.com').first()
    user.signup_date = datetime.utcnow() - timedelta(days=11)
    db.session.commit()
    print('Trial set to expired')
"

# Now login - should redirect to upgrade page
```

---

## 🐛 Troubleshooting

### "No module named 'flask_login'"
```bash
pip install Flask-Login
```

### "Database is locked"
```bash
# Delete and recreate database
rm satellite.db
python app.py  # Restart
```

### "Login not working"
```bash
# Check if user exists in database
python -c "
from app import app
from models import User

with app.app_context():
    user = User.query.filter_by(email='test@example.com').first()
    print(f'User: {user}')
    if user:
        print(f'Email: {user.email}')
        print(f'Password valid: {user.check_password(\"password123\")}')
"
```

### "Static files not loading"
Ensure Bootstrap CDN is accessible or download offline

### "Templates not found"
Check that `templates/` folder exists with all required HTML files

---

## 📊 Database Queries

### Check all users
```python
from app import app
from models import User

with app.app_context():
    users = User.query.all()
    for u in users:
        print(f"{u.username} - {u.email} - Trial Active: {u.is_trial_active()}")
```

### Check subscriptions
```python
from app import app
from models import Subscription

with app.app_context():
    subs = Subscription.query.all()
    for s in subs:
        print(f"{s.name.upper()}: ${s.price}/month")
```

### Check transactions
```python
from app import app
from models import Transaction

with app.app_context():
    txns = Transaction.query.all()
    for t in txns:
        print(f"User {t.user_id}: ${t.amount} - {t.status}")
```

---

## 🔗 Related Routes

| Route | Method | Auth Required | Purpose |
|-------|--------|---------------|---------|
| `/` | GET | Yes | Main dashboard |
| `/auth/login` | GET, POST | No | Login page |
| `/auth/signup` | GET, POST | No | Registration page |
| `/auth/subscription` | GET | Yes | View plans & upgrade |
| `/auth/dashboard` | GET | Yes | User account dashboard |
| `/auth/subscribe/<id>` | POST | Yes | Process subscription |
| `/auth/logout` | GET | Yes | Logout user |
| `/process_satellite` | GET | Yes | Run satellite pipeline |
| `/view_map` | GET | Yes | View interactive map |

---

## 💡 Tips

1. **During Development**: Set `FLASK_ENV=development` in .env for auto-reload
2. **Database Backup**: SQLite files can be copied directly for backup
3. **User Password Reset**: Implement this later by sending reset link via email
4. **Subscription Cancellation**: Add ability for users to cancel subscription
5. **Payment Integration**: Add Stripe webhook handlers for subscription updates

---

## 🎓 Learning Resources

- [Flask Official Tutorial](https://flask.palletsprojects.com/)
- [Flask-Login Documentation](https://flask-login.readthedocs.io/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [Werkzeug Security](https://werkzeug.palletsprojects.com/security/)

---

## ✉️ Support

For issues or questions:
1. Check [AUTH_SETUP.md](AUTH_SETUP.md) for detailed docs
2. Review [models.py](models.py) for database schema
3. Check [auth.py](auth.py) for authentication logic
4. See error messages in Flask debug output

---

**Last Updated**: May 11, 2026
**Status**: ✅ Ready for Use
