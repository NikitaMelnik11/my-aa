from flask import Flask, render_template, flash, redirect, url_for, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this in production

# Simple in-memory database for demonstration
users = {}
messages = []

# Routes
@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if username or email already exists
        if username in users:
            flash('Username already exists', 'danger')
            return render_template('register.html')
        
        # Create new user
        users[username] = {
            'id': len(users) + 1,
            'username': username,
            'email': email,
            'password_hash': generate_password_hash(password),
            'profile_pic': 'default.png',
            'about_me': '',
            'last_seen': datetime.utcnow()
        }
        
        flash('Congratulations, you are now registered!', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = users.get(username)
        
        if user is None or not check_password_hash(user['password_hash'], password):
            flash('Invalid username or password', 'danger')
            return render_template('login.html')
        
        # Set session (simplified for demo)
        # In a real app, use Flask-Login for session handling
        
        return redirect(url_for('chat'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    return redirect(url_for('index'))

@app.route('/chat')
def chat():
    other_users = [user for username, user in users.items()]
    return render_template('chat.html', users=other_users)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    # In a real app, get the current user from session
    return render_template('profile.html', current_user={
        'username': 'Demo User',
        'email': 'demo@example.com',
        'about_me': 'This is a demo profile',
        'profile_pic': 'default.png',
        'last_seen': datetime.utcnow()
    })

@app.route('/get_messages/<recipient_id>')
def get_messages(recipient_id):
    # Filter messages (simplified for demo)
    filtered_messages = []
    for message in messages:
        if (message['sender_id'] == 1 and message['recipient_id'] == int(recipient_id)) or \
           (message['sender_id'] == int(recipient_id) and message['recipient_id'] == 1):
            filtered_messages.append(message)
    
    return jsonify(filtered_messages)

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    
    message = {
        'id': len(messages) + 1,
        'sender_id': 1,  # For demo: current user id
        'recipient_id': int(data['recipient_id']),
        'body': data['message'],
        'timestamp': datetime.utcnow().strftime('%H:%M | %d.%m.%Y'),
        'read': False,
        'is_sender': True
    }
    
    messages.append(message)
    
    return jsonify(message)

# Create a demo user
users['demo'] = {
    'id': 1,
    'username': 'demo',
    'email': 'demo@example.com',
    'password_hash': generate_password_hash('password'),
    'profile_pic': 'default.png',
    'about_me': 'This is a demo user',
    'last_seen': datetime.utcnow()
}

# Create some other users
users['alex'] = {
    'id': 2,
    'username': 'alex',
    'email': 'alex@example.com',
    'password_hash': generate_password_hash('password'),
    'profile_pic': 'default.png',
    'about_me': 'Hi, I am Alex',
    'last_seen': datetime.utcnow()
}

users['maria'] = {
    'id': 3,
    'username': 'maria',
    'email': 'maria@example.com',
    'password_hash': generate_password_hash('password'),
    'profile_pic': 'default.png',
    'about_me': 'Hello from Maria',
    'last_seen': datetime.utcnow()
}

if __name__ == '__main__':
    app.run(debug=True)
