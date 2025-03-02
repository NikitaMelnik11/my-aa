from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime
import sqlite3
import os
import json
import time
import secrets
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize the Flask app
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Database setup
DB_PATH = 'chatapp.db'

def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT UNIQUE,
            profile_pic TEXT DEFAULT 'default.png',
            about_me TEXT,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            recipient_id INTEGER NOT NULL,
            body TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_read BOOLEAN DEFAULT 0,
            FOREIGN KEY (sender_id) REFERENCES users (id),
            FOREIGN KEY (recipient_id) REFERENCES users (id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE contacts (
            user_id INTEGER NOT NULL,
            contact_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, contact_id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (contact_id) REFERENCES users (id)
        )
        ''')
        
        # Create demo users
        demo_users = [
            ('user1', generate_password_hash('password'), 'user1@example.com', 'Hi, I am User 1'),
            ('user2', generate_password_hash('password'), 'user2@example.com', 'Hello from User 2'),
            ('user3', generate_password_hash('password'), 'user3@example.com', 'User 3 here')
        ]
        
        for user in demo_users:
            cursor.execute(
                'INSERT INTO users (username, password_hash, email, about_me) VALUES (?, ?, ?, ?)', 
                user
            )
        
        # Create some demo contacts
        contacts = [
            (1, 2), (1, 3), (2, 1), (2, 3), (3, 1), (3, 2)
        ]
        
        for contact in contacts:
            cursor.execute('INSERT INTO contacts VALUES (?, ?)', contact)
        
        # Create some demo messages
        messages = [
            (1, 2, 'Hello User 2! How are you?'),
            (2, 1, 'Hi User 1! I am good, thanks for asking.'),
            (1, 3, 'Hey User 3, nice to meet you!'),
            (3, 1, 'Nice to meet you too, User 1!')
        ]
        
        for message in messages:
            cursor.execute(
                'INSERT INTO messages (sender_id, recipient_id, body) VALUES (?, ?, ?)', 
                message
            )
        
        conn.commit()
        conn.close()

# Initialize the database
init_db()

# Helper functions
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_by_id(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
        # Convert last_seen to a datetime object that can be formatted in templates
        from datetime import datetime
        if user['last_seen']:
            user = dict(user)
            user['last_seen'] = datetime.strptime(user['last_seen'], '%Y-%m-%d %H:%M:%S')
    return user

def get_user_by_username(username):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return user

def get_messages(sender_id, recipient_id):
    conn = get_db_connection()
    messages = conn.execute(
        '''SELECT * FROM messages 
           WHERE (sender_id = ? AND recipient_id = ?) 
           OR (sender_id = ? AND recipient_id = ?)
           ORDER BY timestamp ASC''',
        (sender_id, recipient_id, recipient_id, sender_id)
    ).fetchall()
    
    # Mark messages as read
    conn.execute(
        'UPDATE messages SET is_read = 1 WHERE sender_id = ? AND recipient_id = ? AND is_read = 0',
        (recipient_id, sender_id)
    )
    conn.commit()
    conn.close()
    
    result = []
    for msg in messages:
        result.append({
            'id': msg['id'],
            'sender_id': msg['sender_id'],
            'recipient_id': msg['recipient_id'],
            'body': msg['body'],
            'timestamp': msg['timestamp'],
            'is_read': bool(msg['is_read']),
            'is_sender': msg['sender_id'] == sender_id
        })
    
    return result

def get_contacts(user_id):
    conn = get_db_connection()
    contacts = conn.execute(
        '''SELECT u.* FROM users u
           JOIN contacts c ON u.id = c.contact_id
           WHERE c.user_id = ?''',
        (user_id,)
    ).fetchall()
    conn.close()
    
    result = []
    for contact in contacts:
        result.append({
            'id': contact['id'],
            'username': contact['username'],
            'profile_pic': contact['profile_pic'],
            'about_me': contact['about_me'],
            'last_seen': contact['last_seen']
        })
    
    return result

def get_unread_count(user_id, sender_id):
    conn = get_db_connection()
    count = conn.execute(
        'SELECT COUNT(*) FROM messages WHERE sender_id = ? AND recipient_id = ? AND is_read = 0',
        (sender_id, user_id)
    ).fetchone()[0]
    conn.close()
    return count

def get_all_users(except_id=None):
    conn = get_db_connection()
    if except_id:
        users = conn.execute('SELECT * FROM users WHERE id != ?', (except_id,)).fetchall()
    else:
        users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    
    result = []
    for user in users:
        result.append({
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'profile_pic': user['profile_pic'],
            'about_me': user['about_me'],
        })
    
    return result

def update_last_seen(user_id):
    conn = get_db_connection()
    conn.execute(
        'UPDATE users SET last_seen = CURRENT_TIMESTAMP WHERE id = ?',
        (user_id,)
    )
    conn.commit()
    conn.close()

def send_message(sender_id, recipient_id, body):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO messages (sender_id, recipient_id, body) VALUES (?, ?, ?)',
        (sender_id, recipient_id, body)
    )
    message_id = cursor.lastrowid
    conn.commit()
    
    # Get the created message
    message = conn.execute('SELECT * FROM messages WHERE id = ?', (message_id,)).fetchone()
    conn.close()
    
    return {
        'id': message['id'],
        'sender_id': message['sender_id'],
        'recipient_id': message['recipient_id'],
        'body': message['body'],
        'timestamp': message['timestamp'],
        'is_read': bool(message['is_read'])
    }

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('chat'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Validate input
        if not username or not password:
            flash('Username and password are required', 'danger')
            return render_template('register.html')
        
        # Check if username already exists
        if get_user_by_username(username):
            flash('Username already exists', 'danger')
            return render_template('register.html')
        
        # Create new user
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
            (username, email, generate_password_hash(password))
        )
        conn.commit()
        conn.close()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = get_user_by_username(username)
        
        if not user or not check_password_hash(user['password_hash'], password):
            flash('Invalid username or password', 'danger')
            return render_template('login.html')
        
        # Set user session
        session['user_id'] = user['id']
        session['username'] = user['username']
        
        # Update last seen
        update_last_seen(user['id'])
        
        return redirect(url_for('chat'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    contacts = get_contacts(user_id)
    
    # Add unread count to contacts
    for contact in contacts:
        contact['unread'] = get_unread_count(user_id, contact['id'])
    
    # Update last seen
    update_last_seen(user_id)
    
    return render_template('chat.html', contacts=contacts, current_user_id=user_id)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = get_user_by_id(user_id)
    
    if request.method == 'POST':
        email = request.form.get('email')
        about_me = request.form.get('about_me')
        
        conn = get_db_connection()
        conn.execute(
            'UPDATE users SET email = ?, about_me = ? WHERE id = ?',
            (email, about_me, user_id)
        )
        conn.commit()
        conn.close()
        
        flash('Profile updated successfully', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html', user=user)

@app.route('/add_contact', methods=['GET', 'POST'])
def add_contact():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        contact_id = request.form.get('contact_id')
        
        if not contact_id:
            flash('No contact selected', 'danger')
            return redirect(url_for('add_contact'))
        
        # Check if contact already exists
        conn = get_db_connection()
        existing = conn.execute(
            'SELECT * FROM contacts WHERE user_id = ? AND contact_id = ?',
            (user_id, contact_id)
        ).fetchone()
        
        if existing:
            flash('Contact already added', 'warning')
        else:
            conn.execute(
                'INSERT INTO contacts (user_id, contact_id) VALUES (?, ?)',
                (user_id, contact_id)
            )
            conn.commit()
            flash('Contact added successfully', 'success')
        
        conn.close()
        return redirect(url_for('chat'))
    
    # Get users who are not already contacts
    conn = get_db_connection()
    users = conn.execute(
        '''SELECT * FROM users 
           WHERE id != ? AND id NOT IN 
           (SELECT contact_id FROM contacts WHERE user_id = ?)''',
        (user_id, user_id)
    ).fetchall()
    conn.close()
    
    return render_template('add_contact.html', users=users)

# API routes
@app.route('/api/messages/<int:contact_id>', methods=['GET'])
def api_get_messages(contact_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    messages = get_messages(user_id, contact_id)
    
    # Update last seen
    update_last_seen(user_id)
    
    return jsonify(messages)

@app.route('/api/messages/send', methods=['POST'])
def api_send_message():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.json
    sender_id = session['user_id']
    recipient_id = data.get('recipient_id')
    message_body = data.get('message')
    
    if not recipient_id or not message_body:
        return jsonify({'error': 'Missing parameters'}), 400
    
    message = send_message(sender_id, recipient_id, message_body)
    
    # Update last seen
    update_last_seen(sender_id)
    
    return jsonify(message)

@app.route('/api/contacts/unread', methods=['GET'])
def api_get_unread_counts():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    contacts = get_contacts(user_id)
    
    result = {}
    for contact in contacts:
        result[contact['id']] = get_unread_count(user_id, contact['id'])
    
    return jsonify(result)

# Long polling endpoint for checking new messages
@app.route('/api/poll', methods=['GET'])
def poll_messages():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    last_id = request.args.get('last_id', type=int, default=0)
    
    # Connect to DB
    conn = get_db_connection()
    
    # Start time for polling
    start_time = time.time()
    timeout = 30  # 30 seconds timeout
    
    while time.time() - start_time < timeout:
        # Check for new messages
        messages = conn.execute(
            '''SELECT * FROM messages 
               WHERE id > ? AND recipient_id = ?
               ORDER BY timestamp ASC''',
            (last_id, user_id)
        ).fetchall()
        
        if messages:
            result = []
            for msg in messages:
                result.append({
                    'id': msg['id'],
                    'sender_id': msg['sender_id'],
                    'recipient_id': msg['recipient_id'],
                    'body': msg['body'],
                    'timestamp': msg['timestamp'],
                    'is_read': bool(msg['is_read']),
                    'is_sender': False
                })
            
            conn.close()
            return jsonify(result)
        
        # Sleep for a bit to avoid hammering the database
        time.sleep(1)
    
    conn.close()
    return jsonify([])  # Return empty if timeout

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
