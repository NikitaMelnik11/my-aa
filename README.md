# ChatConnect

A beautiful and functional messaging application similar to Telegram or Facebook. Users can register, login, and exchange messages with each other in real-time.

## Features

- User registration and authentication
- Real-time messaging using WebSockets
- Beautiful, responsive UI
- User profiles
- Message persistence (messages are saved in the database)
- Modern and intuitive interface

## Technologies Used

- **Backend**: Python with Flask
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML, CSS, JavaScript
- **Real-time Communication**: Socket.IO
- **UI Framework**: Bootstrap 5
- **Icons**: Font Awesome

## Installation and Setup

1. Make sure you have Python 3.8 or newer installed on your computer

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python app.py
   ```

4. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

## Usage

1. Register a new account
2. Login with your credentials
3. Browse the user list and click on a contact to start a conversation
4. Type your message and press Enter or click the send button

## Database

The application uses SQLite as the database, which means all data is stored in a local file (`chatconnect.db`). This makes the app simple to set up and use without requiring a separate database server.

## Security

- Passwords are stored securely using password hashing
- User sessions are managed securely with Flask-Login
- CSRF protection is included with Flask-WTF

## Future Enhancements

- Group chats
- File sharing
- End-to-end encryption
- Voice and video calls
- Customizable themes
- Mobile applications

## License

This project is open source. Feel free to use, modify, and distribute it as needed.
