import sys
import os

# Add parent directory to path so we can import client
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from client import Client, sign_up, normalize_email
import io
import json
import tempfile
from functools import wraps

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Store client instances per session
clients = {}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'client_id' not in session or session['client_id'] not in clients:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'client_id' in session and session['client_id'] in clients:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        email = normalize_email(data.get('email', ''))
        password = data.get('password')
        host = data.get('host', 'localhost')
        port = int(data.get('port', 1200))
        
        try:
            client = Client(host, port, email, password)
            client_id = os.urandom(16).hex()
            clients[client_id] = client
            session['client_id'] = client_id
            session['email'] = email
            return jsonify({'success': True, 'redirect': url_for('dashboard')})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 401
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        email = normalize_email(data.get('email', ''))
        password = data.get('password')
        host = data.get('host', 'localhost')
        port = int(data.get('port', 1200))
        
        try:
            sign_up(email, password, host, port)
            return jsonify({'success': True, 'message': 'Account created. Please login.'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    return render_template('signup.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', email=session['email'])

@app.route('/api/mails')
@login_required
def get_mails():
    client_id = session['client_id']
    client = clients[client_id]
    
    try:
        mails = client.get_mail(sent=False, no=20)
        if not mails:
            return jsonify([])
        
        # Format mails for display
        formatted_mails = []
        for mail in mails:
            if mail:
                print(mail)
                mail_id, from_addr, to_addr, mail_type, data, timestamp = mail
                
                # Check if it's a file
                is_file = False
                file_info = None
                if mail_type == 'file':
                    try:
                        file_info = json.loads(data)
                        is_file = True
                    except:
                        pass
                
                formatted_mails.append({
                    'id': mail_id,
                    'from': from_addr,
                    'to': to_addr,
                    'type': mail_type,
                    'data': data,
                    'is_file': is_file,
                    'file_info': file_info,
                    'timestamp': timestamp
                })
        
        return jsonify(formatted_mails)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sent')
@login_required
def get_sent():
    client_id = session['client_id']
    client = clients[client_id]
    
    try:
        mails = client.get_mail(sent=True, no=20)
        if not mails:
            return jsonify([])
        
        formatted_mails = []
        for mail in mails:
            if mail:
                mail_id, from_addr, to_addr, mail_type, data,timestamp = mail
                is_file = False
                file_info = None
                if mail_type == 'file':
                    try:
                        file_info = json.loads(data)
                        is_file = True
                    except:
                        pass
                
                formatted_mails.append({
                    'id': mail_id,
                    'from': from_addr,
                    'to': to_addr,
                    'type': mail_type,
                    'data': data,
                    'is_file': is_file,
                    'file_info': file_info,
                    'timestamp': timestamp
                })
        return jsonify(formatted_mails)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/send-mail', methods=['POST'])
@login_required
def send_mail():
    client_id = session['client_id']
    client = clients[client_id]
    
    data = request.get_json()
    to_addr = data.get('to')
    mail_type = data.get('type')
    print(mail_type, data)
    content = data.get('content')
    
    try:
        result = client.send_mail(to_addr, mail_type, content)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/send-message', methods=['POST'])
@login_required
def send_message():
    """Send message with optional file attachment"""
    client_id = session['client_id']
    client = clients[client_id]
    
    to_addr = request.form.get('to')
    mail_type = request.form.get('type', 'text')
    content = request.form.get('content')
    file = request.files.get('file')
    
    if not to_addr or not content:
        return jsonify({'success': False, 'error': 'Missing recipient or content'}), 400
    
    try:
        file_path = None
        if file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
                file.save(tmp.name)
                file_path = tmp.name
        
        try:
            result = client.send_mail(to_addr, mail_type, content, file_path)
            return jsonify({'success': True, 'result': result})
        finally:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/send-file', methods=['POST'])
@login_required
def send_file_api():
    client_id = session['client_id']
    client = clients[client_id]
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    to_addr = request.form.get('to')
    
    if not file or not to_addr:
        return jsonify({'success': False, 'error': 'Missing file or recipient'}), 400
    
    try:
        # Save file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            file.save(tmp.name)
            temp_path = tmp.name
        
        try:
            # Send file
            result = client.send_file(to_addr, temp_path)
            return jsonify({'success': True, 'result': result})
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/download-file/<file_hash>', methods=['GET'])
@login_required
def download_file_api(file_hash):
    client_id = session['client_id']
    client = clients[client_id]
    
    try:
        file_data = client.download_file(file_hash)
        
        if not file_data:
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        return send_file(
            io.BytesIO(file_data['data']),
            as_attachment=True,
            download_name=file_data['filename']
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/delete-mail/<mail_id>', methods=['DELETE'])
@login_required
def delete_mail(mail_id):
    client_id = session['client_id']
    client = clients[client_id]
    
    try:
        result = client.NYAP(mail_id)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/logout')
def logout():
    client_id = session.get('client_id')
    if client_id in clients:
        try:
            clients[client_id].nrizz()
        except Exception as e:
            print(f"Error closing client connection: {e}")
        try:
            del clients[client_id]
        except:
            pass
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
