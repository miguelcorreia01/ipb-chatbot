import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash, generate_password_hash
from flask import jsonify, send_file, abort
import pytz
from FetchStats import fetch_chat_statistics, get_chatbot_files, users_collection

load_dotenv()



app = Flask(__name__)


portugal_tz = pytz.timezone('Europe/Lisbon')
app.config["SECRET_KEY"] = '6fb09c1410e8adb991728c2821b911e26ab9c08d8d605048'



    

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = users_collection.find_one({"username": username})

        if user and check_password_hash(user['password'], password):
            user_obj = User(user_id=user['_id'], username=user['username'], role=user['role'])
            login_user(user_obj)
            session['username'] = user['username']
            flash('Login successful', 'success')
            return redirect(url_for('home'))
        else:
            flash('Username or password inválido!', 'danger')

    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/management')
@login_required
def management():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('management.html')

@app.route('/api/stats')
def api_stats():
    time_range = request.args.get('time_range', '30d')
    stats = fetch_chat_statistics(time_range)
    return jsonify(stats)


@app.route('/api/chatbot-files')
def api_chatbot_files():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    files = get_chatbot_files()
    return jsonify(files)

@app.route('/api/read-file/<filename>')
def api_read_file(filename):
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    chatbot_files_dir = os.path.join(app.root_path, '..', 'mdfiles')
    file_path = os.path.join(chatbot_files_dir, filename)
    
    print(f"Attempting to read file: {file_path}")
    
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        print(f"File not found: {file_path}")
        abort(404)
    
    return send_file(file_path, mimetype='text/plain')

last_update_time = None

last_update_file = os.path.join(app.root_path, 'last_update_time.txt')

@app.route('/api/update-ipb-data', methods=['POST'])
def api_update_ipb_data():
    global last_update_time
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:

        utc_time = datetime.utcnow()
        portugal_time = utc_time.replace(tzinfo=pytz.utc).astimezone(portugal_tz)

        last_update_time = portugal_time.strftime('%d/%m/%Y %H:%M:%S')

        with open(last_update_file, 'w') as f:
            f.write(last_update_time)

        return jsonify({'message': 'Data updated successfully', 'last_updated': last_update_time})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/last-update')
def api_last_update():
    try:
        if os.path.exists(last_update_file):
            with open(last_update_file, 'r') as f:
                last_update_time = f.read().strip()
            return jsonify({'last_updated': last_update_time})
        else:
            return jsonify({'last_updated': 'No updates yet'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)