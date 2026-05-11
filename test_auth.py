import requests

s = requests.Session()

# Test 1: Try signup
print("=== TESTING SIGNUP ===")
r = s.post("http://127.0.0.1:5000/auth/signup", data={
    "email": "test@example.com",
    "username": "testuser",
    "password": "test123456",
    "confirm_password": "test123456"
}, allow_redirects=False)
print("Status:", r.status_code)
print("Location:", r.headers.get("Location", "none"))
if r.status_code >= 400:
    print("Body:", r.text[:500])

# Follow redirect
if r.status_code == 302:
    loc = r.headers.get("Location", "/")
    if not loc.startswith("http"):
        loc = "http://127.0.0.1:5000" + loc
    r2 = s.get(loc, allow_redirects=False)
    print("After redirect:", r2.status_code)
    if r2.status_code == 500:
        print("500 ERROR:", r2.text[:1000])

# Test 2: Try login
print()
print("=== TESTING LOGIN ===")
s2 = requests.Session()
r = s2.post("http://127.0.0.1:5000/auth/login", data={
    "email": "test@example.com",
    "password": "test123456",
    "remember": "true"
}, allow_redirects=False)
print("Status:", r.status_code)
print("Location:", r.headers.get("Location", "none"))
print("Cookies:", dict(s2.cookies))

# Follow redirect to index
if r.status_code == 302:
    loc = r.headers.get("Location", "/")
    if not loc.startswith("http"):
        loc = "http://127.0.0.1:5000" + loc
    r3 = s2.get(loc, allow_redirects=False)
    print("After redirect status:", r3.status_code)
    if r3.status_code == 302:
        print("Redirected again to:", r3.headers.get("Location", "none"))
    elif r3.status_code == 500:
        print("500 Error body:", r3.text[:1000])
    elif r3.status_code == 200:
        print("SUCCESS - reached index page")
        if "error" in r3.text.lower():
            print("But page contains error text")
