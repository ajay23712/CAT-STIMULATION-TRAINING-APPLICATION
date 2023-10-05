# import sqlite3
# conn = sqlite3.connect('database.db')
# cursor = conn.cursor()
# table_name = 'Test_Details'
# reset_auto_increment_query = f"UPDATE sqlite_sequence SET seq = 0 WHERE name = '{table_name}'"
# cursor.execute(reset_auto_increment_query)
# conn.commit()
# conn.close()
from flask import Flask
from flask_ngrok import run_with_ngrok  # Import run_with_ngrok

app = Flask(__name__)
run_with_ngrok(app)  # Initialize Flask-Ngrok with your Flask app

@app.route('/')
def hello():
    return "Hello, World!"

if __name__ == '__main__':
    app.run()

