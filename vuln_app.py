import os
import sqlite3
from flask import Flask, request, render_template_string

app = Flask(__name__)
# ❌ Hard‑coded secret key (bad practice)
app.config['SECRET_KEY'] = 'supersecret'

DB_NAME = 'users.db'

def init_db():
    """Initialise a tiny SQLite DB with one default user."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT);')
    # ❌ Plain‑text password storage (bad practice)
    c.execute("INSERT OR IGNORE INTO users (username, password) VALUES ('admin','password123');")
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return '<h2>Welcome to *Vulnerable* Flask App!</h2><p>Try <code>/login</code>, <code>/search?q=</code>, <code>/ping?host=</code> or <code>/read?file=</code>.</p>'

# 🚨 SQL Injection vulnerability
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        # ❌ UNSAFE string concatenation — attacker can inject SQL here
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}';"
        result = c.execute(query).fetchone()
        conn.close()
        if result:
            return f'Logged in as {username}'
        return 'Invalid credentials', 401

    # Simple login form
    return '''
        <form method="post">
          <input name="username" placeholder="user">
          <input name="password" type="password" placeholder="pass">
          <button type="submit">Login</button>
        </form>
    '''

# 🚨 Reflected XSS vulnerability
@app.route('/search')
def search():
    q = request.args.get('q', '')  # attacker‑controlled
    # ❌ Reflecting unsanitised user input directly in HTML
    html = f"<h3>Results for: {q}</h3>"
    return render_template_string(html)

# 🚨 OS Command Injection vulnerability
@app.route('/ping')
def ping():
    host = request.args.get('host', '')
    # ❌ Passing user input to shell command without sanitisation
    stream = os.popen(f"ping -c 1 {host}")
    output = stream.read()
    return f"<pre>{output}</pre>"

# 🚨 Path Traversal / Arbitrary File Read vulnerability
@app.route('/read')
def read_file():
    filename = request.args.get('file', '')
    try:
        # ❌ No validation — attacker can traverse outside ./files
        with open(os.path.join('files', filename), 'r') as f:
            return f"<pre>{f.read()}</pre>"
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    init_db()
    # Debug mode on purpose (info leak + code execution helpers)
    app.run(debug=True, host='0.0.0.0')
