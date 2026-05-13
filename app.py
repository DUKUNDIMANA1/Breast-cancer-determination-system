"""
BreastCare AI — MongoDB Atlas Edition
Roles: Receptionist → Doctor → Lab Technician → Doctor → Admin
Model: Logistic Regression | Accuracy: 97.37%
Database: MongoDB Atlas Cloud
"""

from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, send_file, jsonify)
from pymongo import MongoClient, DESCENDING
from bson import ObjectId
from bson.errors import InvalidId
import hashlib, secrets, os, pickle, json
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv
import re
import phonenumbers

# ── Absolute paths ────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH  = os.path.join(BASE_DIR, 'artifacts', 'model.pkl')
SCALER_PATH = os.path.join(BASE_DIR, 'artifacts', 'scaler.pkl')
CSV_PATH    = os.path.join(BASE_DIR, 'data', 'breast-cancer.csv')

# Load environment variables from a single source of truth.
load_dotenv(os.path.join(BASE_DIR, '.env'), override=False)

app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))

app.secret_key = os.environ.get('SECRET_KEY', 'breastcare-ai-secret-2024')

# On Render, use /tmp for uploads (ephemeral but writable)
# Locally, use static/uploads so images are served directly
IS_RENDER = os.environ.get('RENDER', False)
if IS_RENDER:
    app.config['UPLOAD_FOLDER']  = '/tmp/uploads'
    app.config['REPORTS_FOLDER'] = '/tmp/reports'
else:
    app.config['UPLOAD_FOLDER']  = os.path.join(BASE_DIR, 'static', 'uploads')
    app.config['REPORTS_FOLDER'] = os.path.join(BASE_DIR, 'static', 'reports')
os.makedirs(app.config['UPLOAD_FOLDER'],  exist_ok=True)
os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)

# ── MongoDB Atlas Connection ───────────────────────────────────────────────────
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/breastcare_ai')
MONGO_URI_DIRECT = os.environ.get('MONGO_URI_DIRECT')

MONGO_DB  = os.environ.get('MONGO_DB_NAME', 'breastcare_ai')

# Global variables for MongoDB connection
client = None
db = None
MONGO_OK = False
MONGO_ERROR = None

def connect_mongodb():
    """Establish MongoDB connection with retry logic."""
    global client, db, MONGO_OK, MONGO_ERROR
    
    try:
        import urllib.parse
        
        # Try primary URI first. If SRV/SSL fails and direct URI exists, fallback.
        uri_candidates = [MONGO_URI]
        if MONGO_URI_DIRECT:
            uri_candidates.append(MONGO_URI_DIRECT)

        last_error = None
        for idx, uri in enumerate(uri_candidates):
            parsed = urllib.parse.urlparse(uri)
            is_srv = parsed.scheme.startswith('mongodb+srv')
            is_local = parsed.hostname in ('localhost', '127.0.0.1')

            if is_local:
                current_client = MongoClient(
                    uri,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=5000,
                    socketTimeoutMS=5000,
                    directConnection=True
                )
            else:
                # Atlas / SRV — no directConnection, no socketKeepAlive (removed in newer PyMongo)
                current_client = MongoClient(
                    uri,
                    serverSelectionTimeoutMS=15000,
                    connectTimeoutMS=15000,
                    socketTimeoutMS=15000,
                    retryWrites=True,
                    retryReads=True,
                    maxPoolSize=50,
                    minPoolSize=5
                )

            try:
                current_client.admin.command('ping')
                client = current_client
                db = client[MONGO_DB]
                if is_srv or not is_local:
                    print(f"[BreastCare AI] [OK] Connected to MongoDB Atlas - database: '{MONGO_DB}'")
                    if idx == 1:
                        print("[BreastCare AI] ℹ️  Connected using MONGO_URI_DIRECT fallback.")
                else:
                    print(f"[BreastCare AI] [OK] Connected to Local MongoDB - database: '{MONGO_DB}'")
                break
            except Exception as e:
                last_error = e
                if idx == 0 and MONGO_URI_DIRECT:
                    print("[BreastCare AI] [WARN] Primary MongoDB URI failed. Trying MONGO_URI_DIRECT fallback...")
                continue
        else:
            raise last_error
        
        MONGO_OK = True
        MONGO_ERROR = None
        return True
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        
        # Provide helpful error messages
        if "DNS query name does not exist" in error_msg:
            print("[BreastCare AI] [ERROR] MongoDB Atlas DNS resolution failed.")
            print("[BreastCare AI]    Please check your MongoDB Atlas cluster name and URI.")
            print("[BreastCare AI]    To fix: Update MONGO_URI in .env with correct Atlas URI")
        elif "SSL handshake failed" in error_msg or "TLSV1_ALERT_INTERNAL_ERROR" in error_msg:
            print("[BreastCare AI] [ERROR] MongoDB Atlas TLS handshake failed.")
            print("[BreastCare AI]    Check Atlas Network Access (IP allowlist) and try MONGO_URI_DIRECT in .env.")
            print("[BreastCare AI]    Also ensure no VPN/antivirus/proxy is intercepting TLS traffic.")
        elif "Connection refused" in error_msg or "failed to connect" in error_msg:
            print("[BreastCare AI] [ERROR] Local MongoDB connection failed.")
            print("[BreastCare AI]    Please ensure MongoDB is installed and running locally.")
            print("[BreastCare AI]    To install: Download MongoDB Community Server")
        else:
            print(f"[BreastCare AI] [WARN] MongoDB connection failed: {error_msg}")
        
        print("[BreastCare AI]    Running in OFFLINE mode - data will not persist.")
        print("[BreastCare AI]    Full error traceback:")
        traceback.print_exc()
        
        client = None
        db = None
        MONGO_OK = False
        MONGO_ERROR = error_msg
        return False

# Initialize MongoDB connection (Windows-compatible, direct call)
import threading

def _connect_with_timeout(timeout_seconds=30):
    """Run connect_mongodb() in a background thread with a timeout."""
    result_holder = [False]
    exc_holder = [None]

    def _target():
        try:
            result_holder[0] = connect_mongodb()
        except Exception as e:
            exc_holder[0] = e

    t = threading.Thread(target=_target, daemon=True)
    t.start()
    t.join(timeout=timeout_seconds)

    if t.is_alive():
        global MONGO_OK, MONGO_ERROR
        MONGO_OK = False
        MONGO_ERROR = "Connection timed out"
        print("[BreastCare AI] [ERROR] MongoDB connection timed out after 30 seconds.")
    elif exc_holder[0]:
        print(f"[BreastCare AI] [ERROR] Unexpected error: {exc_holder[0]}")

_connect_with_timeout(30)
print(f"[BreastCare AI] MONGO_OK={MONGO_OK}, MONGO_ERROR={MONGO_ERROR}")

# MongoDB collections
def col(name):
    """Get a MongoDB collection, with reconnection attempt."""
    global db, client
    
    if db is None:
        # Try to reconnect
        if connect_mongodb():
            print(f"[BreastCare AI] [INFO] Reconnected to MongoDB Atlas")
        else:
            raise RuntimeError("MongoDB is not connected. Please check your Atlas URI in .env")
    
    return db[name]

# ── Features ──────────────────────────────────────────────────────────────────
FEATURES = [
    'radius_mean','texture_mean','perimeter_mean','area_mean','smoothness_mean',
    'compactness_mean','concavity_mean','concave points_mean','symmetry_mean','fractal_dimension_mean',
    'radius_se','texture_se','perimeter_se','area_se','smoothness_se',
    'compactness_se','concavity_se','concave points_se','symmetry_se','fractal_dimension_se',
    'radius_worst','texture_worst','perimeter_worst','area_worst','smoothness_worst',
    'compactness_worst','concavity_worst','concave points_worst','symmetry_worst','fractal_dimension_worst'
]
FEATURE_DEFAULTS = {
    'radius_mean':14.1273,'texture_mean':19.2896,'perimeter_mean':91.969,'area_mean':654.8891,
    'smoothness_mean':0.0964,'compactness_mean':0.1043,'concavity_mean':0.0888,
    'concave points_mean':0.0489,'symmetry_mean':0.1812,'fractal_dimension_mean':0.0628,
    'radius_se':0.4052,'texture_se':1.2169,'perimeter_se':2.8661,'area_se':40.3371,
    'smoothness_se':0.007,'compactness_se':0.0255,'concavity_se':0.0319,
    'concave points_se':0.0118,'symmetry_se':0.0205,'fractal_dimension_se':0.0038,
    'radius_worst':16.2692,'texture_worst':25.6772,'perimeter_worst':107.2612,'area_worst':880.5831,
    'smoothness_worst':0.1324,'compactness_worst':0.2543,'concavity_worst':0.2722,
    'concave points_worst':0.1146,'symmetry_worst':0.2901,'fractal_dimension_worst':0.0839
}

# ── ML Model loader with auto-retrain on version mismatch ─────────────────────
def _load_model():
    def _train_fresh():
        import pandas as pd
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler
        print("[BreastCare AI] Retraining model on breast-cancer.csv (30 features)...")
        df  = pd.read_csv(CSV_PATH)
        # Map M→1 (Malignant), B→0 (Benign)
        df['diagnosis'] = df['diagnosis'].map({'M': 1, 'B': 0})
        X   = df[FEATURES]; y = df['diagnosis']
        Xtr,Xte,ytr,yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        sc  = StandardScaler()
        Xtr = sc.fit_transform(Xtr)
        lr  = LogisticRegression(max_iter=1000, random_state=42)
        lr.fit(Xtr, ytr)
        with open(MODEL_PATH,  'wb') as f: pickle.dump(lr, f)
        with open(SCALER_PATH, 'wb') as f: pickle.dump(sc, f)
        from sklearn.metrics import accuracy_score
        acc = accuracy_score(yte, lr.predict(sc.transform(Xte)))
        print(f"[BreastCare AI] Retrained. Accuracy: {acc*100:.2f}%")
        return lr, sc
    try:
        with open(MODEL_PATH,  'rb') as f: mdl = pickle.load(f)
        with open(SCALER_PATH, 'rb') as f: sc  = pickle.load(f)
        import pandas as pd
        _X = sc.transform(pd.DataFrame([FEATURE_DEFAULTS], columns=FEATURES))
        mdl.predict_proba(_X)
        return mdl, sc
    except Exception as e:
        print(f"[BreastCare AI] Model issue ({e}). Retraining...")
        return _train_fresh()

model, scaler = _load_model()

# ── Helpers ───────────────────────────────────────────────────────────────────
def hash_pw(p):  return hashlib.sha256(p.encode()).hexdigest()
def gen_pid():   return f"BC-{datetime.now().strftime('%Y%m')}-{secrets.token_hex(3).upper()}"
def now_str():   return datetime.now().isoformat()

def is_valid_email(email):
    """Basic but strict email format validation."""
    if not email:
        return False
    return re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) is not None

def normalize_phone_number(raw_phone):
    """
    Validate and normalize phone to E.164 format.
    Requires international format with country code (+...).
    """
    if not raw_phone:
        return "", None

    phone = raw_phone.strip()
    digit_count = sum(ch.isdigit() for ch in phone)
    if digit_count < 10:
        return None, "Phone number must contain at least 10 digits."
    if not phone.startswith("+"):
        return None, "Phone number must start with '+' and include country code."

    try:
        parsed = phonenumbers.parse(phone, None)
        if not phonenumbers.is_valid_number(parsed):
            return None, "Enter a valid phone number with country code."
        normalized = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        return normalized, None
    except phonenumbers.NumberParseException:
        return None, "Enter a valid international phone number (example: +2507XXXXXXXX)."

def oid(id_str):
    """Safely convert string to ObjectId."""
    try:    return ObjectId(id_str)
    except: return None

def doc(mongo_doc):
    """Convert MongoDB doc to dict with string _id and id fields."""
    if not mongo_doc: return None
    d = dict(mongo_doc)
    raw_id = d.get('_id')
    id_str = str(raw_id) if raw_id is not None else ''
    d['id']  = id_str
    d['_id'] = id_str
    return d

def docs(cursor):
    return [doc(d) for d in cursor]

def run_prediction(feat_dict):
    import pandas as pd
    X = scaler.transform(pd.DataFrame([feat_dict], columns=FEATURES))
    r = int(model.predict(X)[0])
    c = float(max(model.predict_proba(X)[0])) * 100
    return r, c

def determine_stage(feat_dict):
    """Estimate breast cancer stage (I–IV) for MALIGNANT predictions."""
    radius      = feat_dict.get('radius_mean', 0)
    concavity   = feat_dict.get('concavity_mean', 0)
    comp_worst  = feat_dict.get('compactness_worst', 0)
    conc_worst  = feat_dict.get('concavity_worst', 0)

    size_score  = 0 if radius < 12 else (1 if radius < 16 else 2)
    shape_score = 0 if concavity < 0.05 else (1 if concavity < 0.15 else 2)
    aggr_score  = 0 if comp_worst < 0.15 else (1 if comp_worst < 0.35 else 2)
    worst_score = 0 if conc_worst < 0.15 else (1 if conc_worst < 0.35 else 2)

    total = size_score + shape_score + aggr_score + worst_score

    if total <= 1:   return 'Stage I'
    elif total <= 3: return 'Stage II'
    elif total <= 5: return 'Stage III'
    else:            return 'Stage IV'

# ── Notifications ─────────────────────────────────────────────────────────────
def notify(user_id, message, link=None):
    col('notifications').insert_one({
        'user_id':  str(user_id),
        'message':  message,
        'link':     link,
        'is_read':  False,
        'created_at': now_str()
    })

def notify_role(role, message, link=None):
    users = col('users').find({'role': role}, {'_id': 1})
    for u in users:
        notify(str(u['_id']), message, link)

def unread_count():
    if 'user_id' not in session: return 0
    if not MONGO_OK:             return 0
    if session.get('role') == 'receptionist': return 0  # receptionists don't receive notifications
    try:
        return col('notifications').count_documents(
            {'user_id': session['user_id'], 'is_read': False})
    except: return 0

app.jinja_env.globals['unread_count'] = unread_count
app.jinja_env.globals['MONGO_OK']     = lambda: MONGO_OK

# ── DB seed default users ─────────────────────────────────────────────────────
def seed_users():
    if not MONGO_OK: return
    seeds = [
        ('System Admin',   'admin@bcpred.com',  '0700000000', 'admin',         hash_pw('Admin@123'),   'admin'),
        ('Reception Desk', 'recep@bcpred.com',  '0700000001', 'receptionist',   hash_pw('Recep@123'),   'receptionist'),
        ('Lab Technician', 'lab@bcpred.com',    '0700000002', 'lab_tech',       hash_pw('Lab@12345'),   'lab'),
        ('Dr. Default',    'doctor@bcpred.com', '0700000003', 'doctor',         hash_pw('Doctor@123'),  'doctor'),
    ]
    for full_name,email,contact,username,password,role in seeds:
        if not col('users').find_one({'username': username}):
            col('users').insert_one({
                'full_name': full_name, 'email': email, 'contact': contact,
                'username': username,   'password': password, 'role': role,
                'created_at': now_str()
            })

try:
    seed_users()
except Exception as e:
    print(f"[BreastCare AI] Seed skipped: {e}")

# ── Auth decorators ───────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def d(*a, **k):
        if 'user_id' not in session:
            flash('Please sign in to continue.', 'warning')
            return redirect(url_for('signin'))
        return f(*a, **k)
    return d

def role_required(*roles):
    def dec(f):
        @wraps(f)
        def d(*a, **k):
            if 'user_id' not in session:
                flash('Please sign in.', 'warning')
                return redirect(url_for('signin'))
            if session.get('role') not in roles:
                flash('Access restricted.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*a, **k)
        return d
    return dec

def cu():
    if 'user_id' not in session: return None
    if not MONGO_OK: return {'full_name': session.get('full_name','?'), 'role': session.get('role','?')}
    u = col('users').find_one({'_id': oid(session['user_id'])})
    return doc(u)

# ── Auth Routes ───────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return redirect(url_for('dashboard') if 'user_id' in session else url_for('signin'))

@app.route('/signin', methods=['GET','POST'])
def signin():
    if 'user_id' in session: return redirect(url_for('dashboard'))
    if request.method == 'POST':
        # Check if MongoDB is connected
        if not MONGO_OK:
            flash('Database connection error. Please check your MongoDB connection and try again.', 'danger')
            return render_template('signin.html', mongo_ok=MONGO_OK)
        
        username = request.form.get('username','').strip()
        password = request.form.get('password','')
        try:
            u = col('users').find_one({'username': username, 'password': hash_pw(password)})
            if u:
                u = doc(u)
                session.update({'user_id': u['id'], 'username': u['username'],
                                'full_name': u['full_name'], 'role': u['role']})
                flash(f"Welcome, {u['full_name']}!", 'success')
                return redirect(url_for('dashboard'))
            flash('Invalid username or password.', 'danger')
        except RuntimeError as e:
            flash('Database connection error. Please try again later.', 'danger')
    return render_template('signin.html', mongo_ok=MONGO_OK)

# Signup route removed - users can only be created by admin

@app.route('/forgot-password', methods=['GET','POST'])
def forgot_password():
    """Forgot password — user submits their email/username, receives reset link."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        identifier = request.form.get('identifier','').strip()

        if not identifier:
            flash('Please enter your username or email.', 'danger')
            return render_template('forgot_password.html')

        if not MONGO_OK:
            flash('Database connection error. Please try again later.', 'danger')
            return render_template('forgot_password.html')

        # Find user by username or email
        u = col('users').find_one({
            '$or': [{'username': identifier}, {'email': identifier}]
        })
        if not u:
            flash('No account found with that username or email.', 'danger')
            return render_template('forgot_password.html')

        # Generate reset token
        import secrets
        token = secrets.token_urlsafe(32)
        expiry = datetime.now() + timedelta(hours=1)
        
        # Store reset token
        col('password_resets').insert_one({
            'user_id': str(u['_id']),
            'token': token,
            'expires_at': expiry.isoformat(),
            'created_at': now_str()
        })

        # Generate reset URL
        reset_url = url_for('reset_password', token=token, _external=True)
        
        # Try to send email
        try:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            
            # Get email settings (you can configure these in admin_email_settings)
            smtp_server = os.environ.get('EMAIL_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.environ.get('EMAIL_PORT', '587'))
            smtp_user = os.environ.get('EMAIL_USERNAME', '')
            smtp_password = os.environ.get('EMAIL_PASSWORD', '')
            
            # Debug logging
            print(f"[DEBUG] SMTP Server: {smtp_server}")
            print(f"[DEBUG] SMTP Port: {smtp_port}")
            print(f"[DEBUG] SMTP User: {smtp_user}")
            print(f"[DEBUG] SMTP Password Configured: {'Yes' if smtp_password else 'No'}")
            
            if smtp_user and smtp_password:
                print(f"[DEBUG] Attempting to send email to {u.get('email', identifier)}")
                # Create email message
                msg = MIMEMultipart()
                msg['From'] = smtp_user
                msg['To'] = u.get('email', identifier)
                msg['Subject'] = 'Password Reset - BreastCare AI'
                
                body = f"""
Hello {u.get('full_name', 'User')},

You requested a password reset for your BreastCare AI account.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour for security reasons.

If you didn't request this password reset, please ignore this email.

Best regards,
BreastCare AI Team
                """
                
                msg.attach(MIMEText(body, 'plain'))
                
                # Send email
                try:
                    print(f"[DEBUG] Starting email send process...")
                    if smtp_port == 465:
                        print(f"[DEBUG] Using SSL connection on port {smtp_port}")
                        import ssl
                        context = ssl.create_default_context()
                        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
                            print(f"[DEBUG] Connected to SMTP server via SSL")
                            server.login(smtp_user, smtp_password)
                            print(f"[DEBUG] SMTP login successful")
                            server.sendmail(smtp_user, u.get('email', identifier), msg.as_string())
                            print(f"[DEBUG] Email sent successfully via SSL")
                    else:
                        print(f"[DEBUG] Using STARTTLS connection on port {smtp_port}")
                        with smtplib.SMTP(smtp_server, smtp_port) as server:
                            server.ehlo()
                            print(f"[DEBUG] EHLO sent")
                            server.starttls()
                            print(f"[DEBUG] STARTTLS initiated")
                            server.login(smtp_user, smtp_password)
                            print(f"[DEBUG] SMTP login successful")
                            server.sendmail(smtp_user, u.get('email', identifier), msg.as_string())
                            print(f"[DEBUG] Email sent successfully via STARTTLS")
                    
                    flash('Password reset link sent to your email. Check your inbox.', 'success')
                    print(f"[DEBUG] Success message flashed to user")
                    return render_template('forgot_password.html')
                except Exception as e:
                    print(f"[DEBUG] Email sending failed: {str(e)}")
                    print(f"[DEBUG] Error type: {type(e).__name__}")
                    raise
            else:
                # Email not configured - show reset link directly
                return render_template('forgot_password.html', 
                                 show_link=True, 
                                 reset_url=reset_url,
                                 user_name=u.get('full_name', 'User'),
                                 user_email=u.get('email', identifier))
                
        except Exception as e:
            print(f"[BreastCare AI] Failed to send reset email: {e}")
            # Show reset link directly if email fails
            return render_template('forgot_password.html', 
                             show_link=True, 
                             reset_url=reset_url,
                             user_name=u.get('full_name', 'User'),
                             user_email=u.get('email', identifier))

    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET','POST'])
def reset_password(token):
    """Handle password reset with token."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if not MONGO_OK:
        flash('Database connection error. Please try again later.', 'danger')
        return redirect(url_for('signin'))
    
    # Find valid reset token
    from datetime import datetime
    reset = col('password_resets').find_one({
        'token': token,
        'expires_at': {'$gt': datetime.now().isoformat()}
    })
    
    if not reset:
        flash('Invalid or expired reset link. Please request a new password reset.', 'danger')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password','').strip()
        confirm_password = request.form.get('confirm_password','').strip()
        
        if not new_password or len(new_password) < 6:
            flash('New password must be at least 6 characters.', 'danger')
            return render_template('reset_password.html', token=token)
        
        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_password.html', token=token)
        
        # Update user password
        col('users').update_one(
            {'_id': oid(reset['user_id'])},
            {'$set': {'password': hash_pw(new_password), 'updated_at': now_str()}}
        )
        
        # Delete used token
        col('password_resets').delete_one({'_id': reset['_id']})
        
        flash('Password reset successfully. You can now sign in.', 'success')
        return redirect(url_for('signin'))
    
    return render_template('reset_password.html', token=token)

@app.route('/signout')
def signout():
    session.clear()
    flash('Signed out.','info')
    return redirect(url_for('signin'))

# ── Notifications ─────────────────────────────────────────────────────────────
@app.route('/notifications')
@login_required
def notifications():
    if session.get('role') == 'receptionist':
        flash('Notifications are not available for your role.', 'info')
        return redirect(url_for('dashboard'))
    notes = docs(col('notifications').find(
        {'user_id': session['user_id']}).sort('created_at', DESCENDING).limit(60))
    col('notifications').update_many(
        {'user_id': session['user_id']}, {'$set': {'is_read': True}})
    return render_template('notifications.html', user=cu(), notifications=notes)

# ── Dashboard ─────────────────────────────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    role = session['role']; uid = session['user_id']; data = {}
    if role == 'admin':
        data['total_patients']     = col('patients').count_documents({})
        data['total_predictions']  = col('predictions').count_documents({})
        data['malignant']          = col('predictions').count_documents({'result':1})
        data['benign']             = col('predictions').count_documents({'result':0})
        data['pending_requests']   = col('lab_requests').count_documents({'status':'pending'})
        data['total_users']        = col('users').count_documents({})
        # Recent predictions with patient names
        pipeline = [
            {'$sort': {'created_at': -1}}, {'$limit': 6},
            {'$addFields': {'patient_id_str': '$patient_id'}},
            {'$lookup': {'from':'patients','localField':'patient_id','foreignField':'patient_id','as':'pt'}},
            {'$lookup': {'from':'users','localField':'determined_by','foreignField':'_id','as':'dr'}},
            {'$unwind': {'path':'$pt','preserveNullAndEmptyArrays':True}},
            {'$unwind': {'path':'$dr','preserveNullAndEmptyArrays':True}},
        ]
        raw = list(col('predictions').aggregate(pipeline))
        data['recent_predictions'] = []
        for r in raw:
            d = doc(r)
            d['full_name']   = r.get('pt',{}).get('full_name','—') if 'pt' in r else '—'
            d['doctor_name'] = r.get('dr',{}).get('full_name','—') if 'dr' in r else '—'
            data['recent_predictions'].append(d)

    elif role == 'receptionist':
        data['total_patients'] = col('patients').count_documents({'registered_by': uid})
        data['today_patients'] = col('patients').count_documents({
            'registered_by': uid,
            'created_at': {'$regex': f'^{datetime.now().strftime("%Y-%m-%d")}'}})
        data['total_all']      = col('patients').count_documents({})
        data['recent_patients']= docs(col('patients').find().sort('created_at',-1).limit(6))

    elif role == 'lab':
        data['pending_count'] = col('lab_requests').count_documents({'status':'pending'})
        data['done_today']    = col('lab_results').count_documents({
            'submitted_by': uid,
            'submitted_at': {'$regex': f'^{datetime.now().strftime("%Y-%m-%d")}'}})
        data['total_done']    = col('lab_results').count_documents({'submitted_by': uid})
        pending_raw = list(col('lab_requests').find({'status':'pending'})
                           .sort([('priority',-1),('created_at',1)]).limit(8))
        pending = []
        for r in pending_raw:
            d = doc(r)
            pt = col('patients').find_one({'patient_id': r['patient_id']})
            dr = col('users').find_one({'_id': oid(r.get('requested_by',''))})
            d['patient_name'] = pt['full_name'] if pt else '—'
            d['doctor_name']  = dr['full_name'] if dr else '—'
            pending.append(d)
        data['pending_list'] = pending

    elif role == 'doctor':
        data['my_requests']   = col('lab_requests').count_documents({'requested_by': uid})
        data['awaiting']      = col('lab_requests').count_documents({'requested_by': uid,'status':'results_ready'})
        data['my_predictions']= col('predictions').count_documents({'determined_by': uid})
        data['malignant']     = col('predictions').count_documents({'determined_by': uid,'result':1})
        data['benign']        = col('predictions').count_documents({'determined_by': uid,'result':0})
        ready_raw = list(col('lab_requests').find(
            {'requested_by': uid, 'status':'results_ready'}).sort('updated_at',-1).limit(8))
        ready = []
        for r in ready_raw:
            d = doc(r)
            pt = col('patients').find_one({'patient_id': r['patient_id']})
            d['patient_name'] = pt['full_name'] if pt else '—'
            ready.append(d)
        data['ready_list'] = ready

    return render_template('dashboard.html', user=cu(), **data)

# ── STEP 1: Receptionist — Register Patient ───────────────────────────────────
@app.route('/patients')
@login_required
def patients():
    q = request.args.get('q','').strip()
    query = {'$or':[{'full_name':{'$regex':q,'$options':'i'}},
                    {'patient_id':{'$regex':q,'$options':'i'}}]} if q else {}
    rows = docs(col('patients').find(query).sort('created_at',-1))
    # Attach registrar name
    for r in rows:
        u = col('users').find_one({'_id': oid(r.get('registered_by',''))})
        r['reg_by_name'] = u['full_name'] if u else '—'
    return render_template('patients.html', user=cu(), patients=rows, q=q)

@app.route('/patients/register', methods=['GET','POST'])
@role_required('receptionist','admin')
def register_patient():
    if request.method == 'POST':
        fn = request.form.get('full_name','').strip()
        email = request.form.get('email','').strip()
        contact_input = request.form.get('contact','').strip()
        contact, phone_error = normalize_phone_number(contact_input)

        if not fn:
            flash('Patient name required.','danger')
            return render_template('register_patient.html', user=cu(), patient=None, editing=False)
        if email and not is_valid_email(email):
            flash('Please provide a valid email address.','danger')
            return render_template('register_patient.html', user=cu(), patient=None, editing=False)
        if phone_error:
            flash(phone_error, 'danger')
            return render_template('register_patient.html', user=cu(), patient=None, editing=False)

        pid = gen_pid()
        # Build full address string from Rwanda location fields
        province = request.form.get('province','').strip()
        district = request.form.get('district','').strip()
        sector   = request.form.get('sector','').strip()
        cell     = request.form.get('cell','').strip()
        village  = request.form.get('village','').strip()
        addr_parts = [p for p in [province, district, sector, cell, village] if p]
        full_address = ' / '.join(addr_parts) if addr_parts else request.form.get('address','')

        col('patients').insert_one({
            'patient_id':  pid,
            'full_name':   fn,
            'date_of_birth': request.form.get('date_of_birth',''),
            'gender':      request.form.get('gender',''),
            'contact':     contact,
            'email':       email,
            'address':     full_address,
            'registered_by': session['user_id'],
            'created_at':  now_str()
        })
        notify_role('doctor', f"👤 New patient: {fn} [{pid}]",
                    url_for('patient_detail', patient_id=pid))
        flash(f"Patient registered. ID: {pid}", 'success')
        return redirect(url_for('patients'))
    return render_template('register_patient.html', user=cu(), patient=None, editing=False)

@app.route('/patients/<patient_id>')
@login_required
def patient_detail(patient_id):
    p    = col('patients').find_one({'patient_id': patient_id})
    if not p:
        flash('Patient not found.','danger'); return redirect(url_for('patients'))
    p = doc(p)
    u = col('users').find_one({'_id': oid(p.get('registered_by',''))})
    p['reg_by_name'] = u['full_name'] if u else '—'

    # Split stored address "Province / District / Sector / Cell / Village" into parts
    addr = p.get('address', '') or ''
    if '/' in addr:
        parts = [s.strip() for s in addr.split('/')]
        p['province'] = parts[0] if len(parts) > 0 else ''
        p['district'] = parts[1] if len(parts) > 1 else ''
        p['sector']   = parts[2] if len(parts) > 2 else ''
        p['cell']     = parts[3] if len(parts) > 3 else ''
        p['village']  = parts[4] if len(parts) > 4 else ''
    else:
        p['province'] = p['district'] = p['sector'] = p['cell'] = p['village'] = ''

    reqs = docs(col('lab_requests').find({'patient_id':patient_id}).sort('created_at',-1))
    for r in reqs:
        dr = col('users').find_one({'_id': oid(r.get('requested_by',''))})
        r['doctor_name'] = dr['full_name'] if dr else '—'

    preds = docs(col('predictions').find({'patient_id':patient_id}).sort('created_at',-1))
    for pr in preds:
        dr = col('users').find_one({'_id': oid(pr.get('determined_by',''))})
        pr['doctor_name'] = dr['full_name'] if dr else '—'

    return render_template('patient_detail.html', user=cu(),
                           patient=p, requests=reqs, predictions=preds)

@app.route('/patients/<patient_id>/edit', methods=['GET','POST'])
@role_required('receptionist','admin')
def edit_patient(patient_id):
    p = col('patients').find_one({'patient_id': patient_id})
    if not p:
        flash('Not found.','danger'); return redirect(url_for('patients'))
    p = doc(p)
    if request.method == 'POST':
        full_name = request.form.get('full_name','').strip()
        email = request.form.get('email','').strip()
        contact_input = request.form.get('contact','').strip()
        contact, phone_error = normalize_phone_number(contact_input)

        if not full_name:
            flash('Patient name required.','danger')
            return render_template('register_patient.html', user=cu(), patient=p, editing=True)
        if email and not is_valid_email(email):
            flash('Please provide a valid email address.','danger')
            return render_template('register_patient.html', user=cu(), patient=p, editing=True)
        if phone_error:
            flash(phone_error, 'danger')
            return render_template('register_patient.html', user=cu(), patient=p, editing=True)

        # Build full address from Rwanda location fields
        ep = request.form.get('province','').strip()
        ed = request.form.get('district','').strip()
        es = request.form.get('sector','').strip()
        ec = request.form.get('cell','').strip()
        ev = request.form.get('village','').strip()
        eparts = [x for x in [ep, ed, es, ec, ev] if x]
        edit_address = ' / '.join(eparts) if eparts else request.form.get('address','')

        col('patients').update_one({'patient_id': patient_id}, {'$set':{
            'full_name':     full_name,
            'date_of_birth': request.form.get('date_of_birth',''),
            'gender':        request.form.get('gender',''),
            'contact':       contact,
            'email':         email,
            'address':       edit_address,
        }})
        flash('Patient updated.','success')
        return redirect(url_for('patient_detail', patient_id=patient_id))
    return render_template('register_patient.html', user=cu(), patient=p, editing=True)

# ── STEP 2: Doctor — Lab Request ──────────────────────────────────────────────
@app.route('/requests')
@login_required
def lab_requests_list():
    uid  = session['user_id']; role = session['role']
    q    = request.args.get('q',''); sf = request.args.get('status','')
    query = {}
    if role == 'doctor': query['requested_by'] = uid
    if sf:               query['status'] = sf
    rows_raw = list(col('lab_requests').find(query)
                    .sort([('priority',-1),('created_at',-1)]))
    rows = []
    for r in rows_raw:
        d = doc(r)
        pt = col('patients').find_one({'patient_id': r['patient_id']})
        dr = col('users').find_one({'_id': oid(r.get('requested_by',''))})
        d['patient_name'] = pt['full_name'] if pt else '—'
        d['doctor_name']  = dr['full_name'] if dr else '—'
        if q and q.lower() not in d['patient_name'].lower() and q.lower() not in r['patient_id'].lower():
            continue
        rows.append(d)
    pts = docs(col('patients').find({},{'patient_id':1,'full_name':1}).sort('full_name',1))
    return render_template('lab_requests.html', user=cu(),
                           requests=rows, q=q, status_filter=sf)

@app.route('/requests/new', methods=['GET','POST'])
@role_required('doctor','admin')
def new_request():
    pid  = request.args.get('patient_id','')
    pts  = docs(col('patients').find({},{'patient_id':1,'full_name':1}).sort('full_name',1))
    if request.method == 'POST':
        p  = request.form.get('patient_id','').strip()
        rt = request.form.get('request_type','').strip()
        if not p or not rt:
            flash('Patient and request type required.','danger')
            return render_template('new_request.html', user=cu(), patients=pts, patient_id=pid)
        col('lab_requests').insert_one({
            'patient_id':     p,
            'request_type':   rt,
            'clinical_notes': request.form.get('clinical_notes',''),
            'priority':       request.form.get('priority','normal'),
            'status':         'pending',
            'requested_by':   session['user_id'],
            'created_at':     now_str(),
            'updated_at':     now_str()
        })
        pt = col('patients').find_one({'patient_id': p})
        notify_role('lab',
            f"🔬 Lab request for {pt['full_name'] if pt else p} [{p}]: {rt}",
            url_for('lab_dashboard'))
        flash(f"Lab request submitted.", 'success')
        return redirect(url_for('lab_requests_list'))
    return render_template('new_request.html', user=cu(), patients=pts, patient_id=pid)

# ── STEP 3: Lab Tech — Upload Results ─────────────────────────────────────────
@app.route('/lab')
@role_required('lab','admin')
def lab_dashboard():
    pending_raw = list(col('lab_requests').find({'status':'pending'})
                       .sort([('priority',-1),('created_at',1)]))
    pending = []
    for r in pending_raw:
        d = doc(r)
        pt = col('patients').find_one({'patient_id': r['patient_id']})
        dr = col('users').find_one({'_id': oid(r.get('requested_by',''))})
        d['patient_name'] = pt['full_name'] if pt else '—'
        d['doctor_name']  = dr['full_name'] if dr else '—'
        pending.append(d)

    completed_raw = list(col('lab_requests').find(
        {'status':{'$in':['results_ready','completed']}}).sort('updated_at',-1).limit(10))
    completed = []
    for r in completed_raw:
        d = doc(r)
        pt = col('patients').find_one({'patient_id': r['patient_id']})
        d['patient_name'] = pt['full_name'] if pt else '—'
        res = col('lab_results').find_one({'request_id': d['id']})
        d['submitted_at'] = res['submitted_at'] if res else d['updated_at']
        completed.append(d)

    return render_template('lab_dashboard.html', user=cu(),
                           pending=pending, completed=completed)

@app.route('/lab/upload/<request_id>', methods=['GET','POST'])
@role_required('lab','admin')
def upload_results(request_id):
    req = col('lab_requests').find_one({'_id': oid(request_id)})
    if not req:
        flash('Request not found.','danger'); return redirect(url_for('lab_dashboard'))
    req = doc(req)
    pt = col('patients').find_one({'patient_id': req['patient_id']})
    req['patient_name'] = pt['full_name'] if pt else '—'

    if request.method == 'POST':
        feats = {}
        for f in FEATURES:
            try:    feats[f] = float(request.form.get(f, FEATURE_DEFAULTS[f]))
            except: feats[f] = FEATURE_DEFAULTS[f]

        img_path = None; img_ann = None
        img_file = request.files.get('image')
        if img_file and img_file.filename:
            from src.services.image_processor_advanced import generate_annotated_image
            fb = img_file.read()
            sn = f"{req['patient_id']}_{request_id}.jpg"
            ip = os.path.join(app.config['UPLOAD_FOLDER'], sn)
            with open(ip,'wb') as fp: fp.write(fb)
            img_path = sn          # store filename only, not full path
            img_ann  = generate_annotated_image(fb)
        col('lab_results').insert_one({
            'request_id':       request_id,
            'patient_id':       req['patient_id'],
            'features':         feats,
            'image_path':       img_path,
            'image_annotated':  img_ann,
            'lab_notes':        request.form.get('lab_notes',''),
            'submitted_by':     session['user_id'],
            'submitted_at':     now_str()
        })
        col('lab_requests').update_one(
            {'_id': oid(request_id)},
            {'$set': {'status':'results_ready','updated_at': now_str()}})

        notify(req['requested_by'],
               f"✅ Lab results ready for {req['patient_name']} [{req['patient_id']}]",
               url_for('review_results', request_id=request_id))
        flash("Results uploaded. Doctor notified.", 'success')
        return redirect(url_for('lab_dashboard'))

    img_features = session.pop('img_features', None)
    return render_template('upload_results.html', user=cu(),
                           req=req, features=FEATURES,
                           feat_values=img_features or FEATURE_DEFAULTS.copy(),
                           feature_defaults=FEATURE_DEFAULTS,
                           img_loaded=img_features is not None)

@app.route('/lab/image-extract', methods=['POST'])
@role_required('lab','admin')
def lab_image_extract():
    rid = request.form.get('request_id')
    f   = request.files.get('image')
    if not f or not f.filename:
        flash('Select an image.','danger')
        return redirect(url_for('upload_results', request_id=rid))
    from src.services.image_processor_advanced import extract_features
    try:
        features = extract_features(f.read())
        extracted = {k: float(features.get(k, FEATURE_DEFAULTS[k])) for k in FEATURES}
        session['img_features'] = extracted
        if features.get('validation_failed', False):
            flash('⚠️ Image may not be a standard FNA slide. Features extracted — review and adjust values.', 'warning')
        else:
            flash('✅ Features extracted successfully. Review values below.', 'success')
    except Exception as e:
        flash(f'Image processing failed: {e}','danger')
    return redirect(url_for('upload_results', request_id=rid))

@app.route('/api/extract-features', methods=['POST'])
def api_extract_features():
    """JSON endpoint — returns extracted features for live form fill."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    if session.get('role') not in ('lab', 'admin'):
        return jsonify({'error': 'Access restricted'}), 403
    f = request.files.get('image')
    if not f or not f.filename:
        return jsonify({'error': 'No image provided'}), 400
    from src.services.image_processor_advanced import extract_features
    import math
    try:
        features = extract_features(f.read())
        # Sanitize: replace NaN/Inf with dataset defaults, ensure no zeros for key features
        extracted = {}
        for k in FEATURES:
            raw = features.get(k, FEATURE_DEFAULTS[k])
            try:
                v = float(raw)
                # Replace NaN, Inf, or 0 for features that should never be 0
                if math.isnan(v) or math.isinf(v) or v == 0.0:
                    v = float(FEATURE_DEFAULTS[k])
            except (TypeError, ValueError):
                v = float(FEATURE_DEFAULTS[k])
            extracted[k] = round(v, 6)
        warning = features.get('validation_failed', False)
        return jsonify({'features': extracted, 'warning': warning})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── STEP 4: Doctor — Review & Diagnose ────────────────────────────────────────
@app.route('/results/review/<request_id>', methods=['GET','POST'])
@role_required('doctor','admin')
def review_results(request_id):
    req = col('lab_requests').find_one({'_id': oid(request_id)})
    lab = col('lab_results').find_one({'request_id': request_id})
    if not req or not lab:
        flash('Results not found.','danger')
        return redirect(url_for('lab_requests_list'))
    req = doc(req); lab = doc(lab)
    pt  = col('patients').find_one({'patient_id': req['patient_id']})
    req['patient_name']   = pt['full_name']    if pt else '—'
    req['date_of_birth']  = pt.get('date_of_birth','') if pt else '—'
    req['gender']         = pt.get('gender','') if pt else '—'
    req['contact']        = pt.get('contact','') if pt else '—'
    lab_user = col('users').find_one({'_id': oid(lab.get('submitted_by',''))})
    lab['lab_name'] = lab_user['full_name'] if lab_user else '—'

    feat_values = lab.get('features', FEATURE_DEFAULTS.copy())

    if request.method == 'POST':
        adj = {}
        for f in FEATURES:
            try:    adj[f] = float(request.form.get(f, feat_values.get(f,0)))
            except: adj[f] = feat_values.get(f, 0.0)

        result, confidence = run_prediction(adj)
        stage = determine_stage(adj) if result == 1 else None

        col('predictions').insert_one({
            'patient_id':    req['patient_id'],
            'request_id':    request_id,
            'lab_result_id': lab['id'],
            'features':      adj,
            'result':        result,
            'confidence':    confidence,
            'stage':         stage,
            'doctor_notes':  request.form.get('doctor_notes',''),
            'determined_by': session['user_id'],
            'created_at':    now_str(),
            'updated_at':    now_str()
        })
        lbl = 'MALIGNANT' if result==1 else 'BENIGN'
        stage_str = f' — {stage}' if stage else ''
        col('lab_requests').update_one(
            {'_id': oid(request_id)},
            {'$set': {'status':'completed','updated_at': now_str()}})

        notify_role('admin',
            f"🏥 {req['patient_name']} [{req['patient_id']}] → {lbl}{stage_str} ({confidence:.1f}%)",
            url_for('all_predictions'))

        flash(f"Determination saved: {lbl}{stage_str} ({confidence:.1f}%)", 'success')
        return redirect(url_for('my_predictions'))

    return render_template('review_results.html', user=cu(),
                           req=req, lab_result=lab,
                           features=FEATURES, feat_values=feat_values,
                           feature_defaults=FEATURE_DEFAULTS)

# ── Predictions ───────────────────────────────────────────────────────────────
@app.route('/predictions/mine')
@role_required('doctor','admin')
def my_predictions():
    q   = request.args.get('q','').strip()
    uid = session['user_id']
    raw = list(col('predictions').find({'determined_by': uid}).sort('created_at',-1))
    rows = _enrich_predictions(raw, q)
    return render_template('my_predictions.html', user=cu(), predictions=rows, q=q, is_admin=False)

@app.route('/predictions/all')
@role_required('admin')
def all_predictions():
    q   = request.args.get('q','').strip()
    raw = list(col('predictions').find().sort('created_at',-1))
    rows = _enrich_predictions(raw, q)
    return render_template('my_predictions.html', user=cu(), predictions=rows, q=q, is_admin=True)

def _enrich_predictions(raw, q=''):
    rows = []
    for r in raw:
        d  = doc(r)
        pt = col('patients').find_one({'patient_id': r['patient_id']})
        dr = col('users').find_one({'_id': oid(r.get('determined_by',''))})
        d['full_name']            = pt['full_name']              if pt else '—'
        d['contact']              = pt.get('contact','')         if pt else '—'
        d['gender']               = pt.get('gender','')          if pt else '—'
        d['doctor_name']          = dr['full_name']              if dr else '—'
        d['doctor_specialization']= dr.get('specialization','')  if dr else ''
        if q and q.lower() not in d['full_name'].lower() and q.lower() not in r['patient_id'].lower():
            continue
        rows.append(d)
    return rows

@app.route('/predictions/<pred_id>')
@login_required
def prediction_detail(pred_id):
    pr  = col('predictions').find_one({'_id': oid(pred_id)})
    if not pr:
        flash('Not found.','danger'); return redirect(url_for('dashboard'))
    pr  = doc(pr)
    pt  = col('patients').find_one({'patient_id': pr['patient_id']})
    dr  = col('users').find_one({'_id': oid(pr.get('determined_by',''))})
    pr.update({
        'full_name':             pt['full_name']              if pt else '—',
        'contact':               pt.get('contact','')         if pt else '—',
        'email':                 pt.get('email','')           if pt else '—',
        'gender':                pt.get('gender','')          if pt else '—',
        'date_of_birth':         pt.get('date_of_birth','')   if pt else '—',
        'doctor_name':           dr['full_name']              if dr else '—',
        'doctor_specialization': dr.get('specialization','')  if dr else '',
    })
    lab = col('lab_results').find_one({'request_id': pr.get('request_id','')})
    return render_template('prediction_detail.html', user=cu(),
                           pred=pr, lab_result=doc(lab) if lab else None)

@app.route('/predictions/<pred_id>/delete', methods=['POST'])
@role_required('admin','doctor')
def delete_prediction(pred_id):
    col('predictions').delete_one({'_id': oid(pred_id)})
    flash('Deleted.','success')
    return redirect(url_for('my_predictions'))

# ── PDF Export ─────────────────────────────────────────────────────────────────
@app.route('/export/pdf/<patient_id>')
@role_required('admin')
def export_pdf_single(patient_id):
    from src.services.pdf_generator import generate_single_pdf
    path = generate_single_pdf(patient_id)
    if not path:
        flash('No predictions found.','danger')
        return redirect(url_for('all_predictions'))
    return send_file(path, as_attachment=True,
                     download_name=f'report_{patient_id}.pdf',
                     mimetype='application/pdf')

@app.route('/export/pdf/all')
@role_required('admin')
def export_pdf_all():
    from src.services.pdf_generator import generate_all_pdf
    return send_file(generate_all_pdf(), as_attachment=True,
                     download_name='all_patients_report.pdf',
                     mimetype='application/pdf')

# ── Admin: Users ──────────────────────────────────────────────────────────────
@app.route('/admin/users')
@role_required('admin')
def admin_users():
    users = docs(col('users').find({},{'password':0}))
    return render_template('admin_users.html', user=cu(), users=users)

@app.route('/admin/users/create', methods=['GET','POST'])
@role_required('admin')
def create_user():
    users = docs(col('users').find({},{'password':0}))
    if request.method == 'POST':
        full_name = request.form.get('full_name','').strip()
        username = request.form.get('username','').strip()
        email = request.form.get('email','').strip()
        contact_input = request.form.get('contact','').strip()
        role = request.form.get('role','').strip()
        password = request.form.get('password','').strip()
        specialization = request.form.get('specialization','').strip()
        contact, phone_error = normalize_phone_number(contact_input)
        
        if not all([full_name, username, email, role, password]):
            flash('Please fill all required fields to create a user.','danger')
            return render_template('admin_users.html', user=cu(), users=users)
        if role == 'doctor' and not specialization:
            flash('Please select a specialization for the doctor.','danger')
            return render_template('admin_users.html', user=cu(), users=users)
        if not is_valid_email(email):
            flash('Please provide a valid email address.','danger')
            return render_template('admin_users.html', user=cu(), users=users)
        if phone_error:
            flash(phone_error, 'danger')
            return render_template('admin_users.html', user=cu(), users=users)
        if len(password) < 6:
            flash('Password must be at least 6 characters long.','danger')
            return render_template('admin_users.html', user=cu(), users=users)
        
        # Check if username or email already exists
        if col('users').find_one({'$or': [{'username': username}, {'email': email}]}):
            flash('Username or email already exists.','danger')
            return render_template('admin_users.html', user=cu(), users=users)
        
        # Create new user
        user_data = {
            'full_name': full_name,
            'username': username,
            'email': email,
            'contact': contact,
            'role': role,
            'specialization': specialization if role == 'doctor' else '',
            'password': hash_pw(password),
            'created_at': now_str()
        }
        
        col('users').insert_one(user_data)
        flash(f'User {username} created successfully.','success')
        return redirect(url_for('admin_users'))
    
    return render_template('admin_users.html', user=cu())

@app.route('/admin/users/<uid>/edit', methods=['GET','POST'])
@role_required('admin')
def edit_user(uid):
    uid = str(uid)  # Ensure uid is a string
    edit_user = col('users').find_one({'_id': oid(uid)})
    
    if not edit_user:
        flash('User not found.','danger')
        return redirect(url_for('admin_users'))
    
    edit_user = doc(edit_user)  # convert _id → id
    
    if request.method == 'POST':
        full_name = request.form.get('full_name','').strip()
        username = request.form.get('username','').strip()
        email = request.form.get('email','').strip()
        contact_input = request.form.get('contact','').strip()
        role = request.form.get('role','').strip()
        password = request.form.get('password','').strip()
        specialization = request.form.get('specialization','').strip()
        contact, phone_error = normalize_phone_number(contact_input)
        
        if not all([full_name, username, email, role]):
            flash('Name, username, email, and role are required.','danger')
            return render_template('admin_users.html', user=cu(), edit_user=edit_user)
        if role == 'doctor' and not specialization:
            flash('Please select a specialization for the doctor.','danger')
            return render_template('admin_users.html', user=cu(), edit_user=edit_user)
        if not is_valid_email(email):
            flash('Please provide a valid email address.','danger')
            return render_template('admin_users.html', user=cu(), edit_user=edit_user)
        if phone_error:
            flash(phone_error, 'danger')
            return render_template('admin_users.html', user=cu(), edit_user=edit_user)
        if password and len(password) < 6:
            flash('If changing password, use at least 6 characters.','danger')
            return render_template('admin_users.html', user=cu(), edit_user=edit_user)
        
        # Check if username or email already exists (excluding current user)
        existing_user = col('users').find_one({
            '$and': [
                {'_id': {'$ne': oid(uid)}},
                {'$or': [{'username': username}, {'email': email}]}
            ]
        })
        
        if existing_user:
            flash('Username or email already exists.','danger')
            return render_template('admin_users.html', user=cu(), edit_user=edit_user)
        
        # Update user data
        update_data = {
            'full_name': full_name,
            'username': username,
            'email': email,
            'contact': contact,
            'role': role,
            'specialization': specialization if role == 'doctor' else '',
            'updated_at': now_str()
        }
        
        if password:  # Only update password if provided
            update_data['password'] = hash_pw(password)
        
        col('users').update_one(
            {'_id': oid(uid)},
            {'$set': update_data}
        )
        
        flash('User updated successfully.','success')
        return redirect(url_for('admin_users'))
    
    return render_template('admin_users.html', user=cu(), edit_user=edit_user)

@app.route('/admin/users/<uid>/delete', methods=['POST'])
@role_required('admin')
def delete_user(uid):
    if uid == session['user_id']:
        flash('Cannot delete yourself.','danger')
        return redirect(url_for('admin_users'))
    
    col('users').delete_one({'_id': oid(uid)})
    flash('User removed.','success')
    return redirect(url_for('admin_users'))

# ── Admin: System Monitoring ─────────────────────────────────────────────────────
@app.route('/admin/monitoring')
@role_required('admin')
def admin_monitoring():
    try:
        from src.services.monitoring_system import get_system_performance, check_system_drift, generate_drift_alert
        performance_metrics = get_system_performance()
        drift_result = check_system_drift()
        drift_alert = generate_drift_alert(drift_result) if drift_result.get('drift_detected') else None
    except Exception:
        performance_metrics = {}; drift_result = {'drift_detected': False}; drift_alert = None
    return render_template('admin_monitoring.html', user=cu(),
                           performance_metrics=performance_metrics,
                           drift_result=drift_result, drift_alert=drift_alert)

@app.route('/admin/monitoring/export')
@role_required('admin')
def admin_monitoring_export():
    try:
        from src.services.monitoring_system import export_monitoring_report
        filename = export_monitoring_report()
        if filename:
            return send_file(filename, as_attachment=True,
                             download_name=f'monitoring_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
                             mimetype='application/json')
    except Exception:
        pass
    flash('Failed to export monitoring data.','danger')
    return redirect(url_for('admin_monitoring'))

# ── Serve uploaded files from /tmp on Render ──────────────────────────────────
@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    """Serve uploaded files — works both locally and on Render (/tmp)."""
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ── Rwanda Locations API ──────────────────────────────────────────────────────
_RWANDA_DATA = None

def _rwanda():
    global _RWANDA_DATA
    if _RWANDA_DATA is None:
        fp = os.path.join(BASE_DIR, 'static', 'rwanda_locations.json')
        with open(fp, 'r', encoding='utf-8') as f:
            _RWANDA_DATA = json.load(f)
    return _RWANDA_DATA

@app.route('/api/rwanda/provinces')
def api_rwanda_provinces():
    return jsonify(_rwanda()['provinces'])

@app.route('/api/rwanda/districts/<province>')
def api_rwanda_districts(province):
    d = _rwanda()['districts']
    key = next((k for k in d if k.lower() == province.lower()), None)
    return jsonify(d.get(key, []))

@app.route('/api/rwanda/sectors/<province>/<district>')
def api_rwanda_sectors(province, district):
    d = _rwanda()['sectors']
    key = next((k for k in d if k.lower() == f"{province}/{district}".lower()), None)
    return jsonify(d.get(key, []))

@app.route('/api/rwanda/cells/<province>/<district>/<sector>')
def api_rwanda_cells(province, district, sector):
    d = _rwanda()['cells']
    key = next((k for k in d if k.lower() == f"{province}/{district}/{sector}".lower()), None)
    return jsonify(d.get(key, []))

@app.route('/api/rwanda/villages/<province>/<district>/<sector>/<cell>')
def api_rwanda_villages(province, district, sector, cell):
    d = _rwanda()['villages']
    key = next((k for k in d if k.lower() == f"{province}/{district}/{sector}/{cell}".lower()), None)
    return jsonify(d.get(key, []))

def _get_email_settings():
    """Load email settings from DB, fall back to .env values."""
    try:
        doc_settings = col('system_settings').find_one({'key': 'email_config'})
        if doc_settings:
            return doc_settings.get('value', {})
    except Exception:
        pass
    # Fallback to .env
    return {
        'server': os.environ.get('EMAIL_SERVER', 'smtp.gmail.com'),
        'port': int(os.environ.get('EMAIL_PORT', '587')),
        'username': os.environ.get('EMAIL_USERNAME', ''),
        'password': '',  # never expose stored password in form
        'from_name': os.environ.get('EMAIL_FROM_NAME', 'BreastCare AI'),
    }

# ── Admin: Email Settings ────────────────────────────────────────────────

@app.route('/admin/email-settings', methods=['GET','POST'])
@role_required('admin')
def admin_email_settings():
    """Email settings configuration page for administrators."""
    if request.method == 'POST':
        action = request.form.get('action', 'save')
        
        if action == 'save':
            # Save email settings to database
            settings = {
                'server': request.form.get('server', '').strip(),
                'port': int(request.form.get('port', '587')),
                'username': request.form.get('username', '').strip(),
                'password': request.form.get('password', '').strip(),
                'from_name': request.form.get('from_name', 'BreastCare AI').strip()
            }
            
            col('system_settings').update_one(
                {'key': 'email_config'},
                {'$set': {'value': settings, 'updated_at': now_str()}},
                upsert=True
            )
            
            flash('Email settings saved successfully!', 'success')
            return redirect(url_for('admin_email_settings'))
        
        elif action == 'test':
            # Send test email
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            
            settings = _get_email_settings()
            test_to = request.form.get('test_email', '').strip()
            
            if not test_to:
                flash('Please enter a test email address.', 'danger')
                return redirect(url_for('admin_email_settings'))
            
            try:
                msg = MIMEMultipart()
                msg['From'] = f"{settings['from_name']} <{settings['username']}>"
                msg['To'] = test_to
                msg['Subject'] = 'Test Email - BreastCare AI'
                
                body = f"""
This is a test email from BreastCare AI.

If you receive this, your email configuration is working correctly.

Best regards,
BreastCare AI Team
                """
                
                msg.attach(MIMEText(body, 'plain'))
                
                # Send email
                if settings['port'] == 465:
                    import ssl
                    context = ssl.create_default_context()
                    with smtplib.SMTP_SSL(settings['server'], settings['port'], context=context) as server:
                        server.login(settings['username'], settings['password'])
                        server.sendmail(settings['username'], test_to, msg.as_string())
                else:
                    with smtplib.SMTP(settings['server'], settings['port']) as server:
                        server.ehlo()
                        server.starttls()
                        server.login(settings['username'], settings['password'])
                        server.sendmail(settings['username'], test_to, msg.as_string())
                
                flash('Test email sent successfully!', 'success')
            except Exception as e:
                flash(f'Failed to send test email: {str(e)}', 'danger')
    
    # Load current settings
    settings = _get_email_settings()
    return render_template('admin_email_settings.html', user=cu(), settings=settings)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', debug=debug, port=port, use_reloader=False)
