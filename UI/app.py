import json
import re
from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
import sys
import os
import markdown

# Add parent directory to Python path to import client
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from client import Client, sign_up

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

# YCAP server configuration
YCAP_HOST = "localhost"
YCAP_PORT = 1200

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('inbox'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        try:
            client = Client(YCAP_HOST, YCAP_PORT, email, password)
            session['user'] = email
            session['client'] = {
                'host': YCAP_HOST,
                'port': YCAP_PORT,
                'email': email,
                'password': password
            }
            flash('Logged in successfully!', 'success')
            return redirect(url_for('inbox'))
        except Exception as e:
            flash(f'Login failed: {str(e)}', 'error')
            
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        try:
            if sign_up(email, password, YCAP_HOST, YCAP_PORT):
                flash('Account created successfully! Please login.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Failed to create account.', 'error')
        except Exception as e:
            flash(f'Signup failed: {str(e)}', 'error')
            
    return render_template('signup.html')

@app.route('/logout')
def logout():
    if 'user' in session:
        client_data = session.get('client', {})
        if client_data:
            try:
                client = Client(client_data['host'], client_data['port'], 
                              client_data['email'], client_data['password'])
                client.nrizz()
            except:
                pass
    session.clear()
    return redirect(url_for('login'))

@app.route('/inbox')
@login_required
def inbox():
    try:
        client_data = session['client']
        client = Client(client_data['host'], client_data['port'], 
                       client_data['email'], client_data['password'])
        
        valid_emails = client.get_mail(sent=False, no=100)
            
        return render_template('inbox.html', emails=valid_emails)
    except Exception as e:
        flash(f'Error fetching emails: {str(e)}', 'error')
        return redirect(url_for('login'))

@app.route('/sent')
@login_required
def sent():
    try:
        client_data = session['client']
        client = Client(client_data['host'], client_data['port'], 
                       client_data['email'], client_data['password'])
        
        # Get mail IDs first
        valid_emails = client.get_mail(sent=True)
        
                
        return render_template('sent.html', emails=valid_emails)
    except Exception as e:
        flash(f'Error fetching sent emails: {str(e)}', 'error')
        return redirect(url_for('login'))

@app.route('/compose', methods=['GET', 'POST'])
@login_required
def compose():
    if request.method == 'POST':
        to_addr = request.form['to']
        mail_type = request.form['type']
        mail_data = request.form['content']
        
        if not to_addr.endswith('^ycap.com'):
            to_addr += '^ycap.com'
            
        try:
            client_data = session['client']
            client = Client(client_data['host'], client_data['port'], 
                          client_data['email'], client_data['password'])
            response = client.send_mail(to_addr, mail_type, mail_data)
            
            if response:
                response_data = response.get('return', [])
                if response_data[0] == 'MAIL_SENT':
                    mail_id = response_data[1]  # Get the mail ID from response
                    flash(f'Email sent successfully! Mail ID: {mail_id}', 'success')
                    return redirect(url_for('sent'))
                else:
                    error_msg = response_data[1]
                    flash(f'Failed to send email: {error_msg}', 'error')
            else:
                flash('No response received from server', 'error')
        except Exception as e:
            flash(f'Error sending email: {str(e)}', 'error')
            
    return render_template('compose.html')
def clean_email_text(text: str) -> str:

    
    # Step 1: Replace literal \r\n with actual newlines
    text = re.sub(
        r'\\u[dD][89ABab][0-9A-Fa-f]{2}\\u[dD][CDEFcdef][0-9A-Fa-f]{2}',
        '',
        text
    )
    
    # Step 2: Remove escaped surrogate pairs
    text = text.replace(r'\r\n', "\n")
    
    
    # Step 3: Convert Markdown to HTML with line breaks
    html = markdown.markdown(text, extensions=['nl2br'])
    
    return html
@app.route('/view/<mail_id>')
@login_required
def view_email(mail_id):
    try:
        client_data = session['client']
        client = Client(client_data['host'], client_data['port'], 
                       client_data['email'], client_data['password'])
        email = client.GMA(mail_id)
        if email[3] == "markdown":
            email[4] = clean_email_text(email[4])
            return render_template('view_email.html', email=email)
        else:
            email[4] = clean_email_text(email[4])
            return render_template('view_email.html', email=email)

            

        flash('Email not found or invalid format.', 'error')
    except Exception as e:
        flash(f'Error viewing email: {str(e)}', 'error')
    
    # Redirect back to the appropriate page
    referrer = request.referrer
    if referrer and 'sent' in referrer: 
        return redirect(url_for('sent'))
    return redirect(url_for('inbox'))

@app.route('/delete/<mail_id>')
@login_required
def delete_email(mail_id):
    client = None
    source = 'inbox'
    if request.referrer and 'sent' in request.referrer:
        source = 'sent'
    
    try:
        client_data = session['client']
        client = Client(client_data['host'], client_data['port'], 
                       client_data['email'], client_data['password'])
        response = client.NYAP(mail_id)
        response_data = response.get('return', [])
        print(response)
        
        if response_data and response_data[0] == 'MAIL_DELETED':
            return render_template('delete_confirmation.html', mail_id=mail_id, source=source)
        else:
            error_msg = response_data[1] 
            flash(f'Failed to delete email: {error_msg}', 'error')

    except Exception as e:
        flash(f'Error deleting email: {str(e)}', 'error')

    return redirect("delete_confirmation.html", mail_id=mail_id, source=source)
if __name__ == '__main__':
    app.run(debug=True)