"""
BreastCare AI — MongoDB Atlas Edition
Roles: Receptionist → Doctor → Lab Technician → Doctor → Admin
Model: Logistic Regression | Accuracy: 97.37%
Database: MongoDB Atlas Cloud
"""

from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, send_file)
from pymongo import MongoClient, DESCENDING
from bson import ObjectId
from bson.errors import InvalidId
import hashlib, secrets, os, pickle, json
from datetime import datetime
from functools import wraps
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ── Absolute paths ────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH  = os.path.join(BASE_DIR, 'model.pkl')
SCALER_PATH = os.path.join(BASE_DIR, 'scaler.pkl')
CSV_PATH    = os.path.join(BASE_DIR, 'breast_cancer_cleaned.csv')

app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))

app.secret_key = os.environ.get('SECRET_KEY', 'breastcare-ai-secret-2024')
app.config['UPLOAD_FOLDER']  = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['REPORTS_FOLDER'] = os.path.join(BASE_DIR, 'static', 'reports')
os.makedirs(app.config['UPLOAD_FOLDER'],  exist_ok=True)
os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)

# ── MongoDB Atlas Connection ───────────────────────────────────────────────────
# Read MONGO_URI directly to avoid truncation issues
try:
    with open(os.path.join(BASE_DIR, '.env'), 'r') as f:
        for line in f:
            if line.startswith('MONGO_URI='):
                MONGO_URI = line.strip().split('=', 1)[1]
                break
        else:
            MONGO_URI = 'mongodb://localhost:27017/breastcare_ai'
except Exception:
    MONGO_URI = 'mongodb://localhost:27017/breastcare_ai'

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
        # Enhanced connection with proper SSL handling
        import ssl
        import urllib.parse
        
        # Parse URI and configure connection parameters
        parsed = urllib.parse.urlparse(MONGO_URI)
        
        if parsed.scheme.startswith('mongodb+srv'):
            # MongoDB Atlas connection
            query = urllib.parse.parse_qs( parsed.query)
            query['tlsAllowInvalidCertificates'] = ['true']
            query['retryWrites'] = ['true']
            new_query = urllib.parse.urlencode(query, doseq=True)
            modified_uri = parsed._replace(query=new_query).geturl()
            
            client = MongoClient(
                modified_uri,
                serverSelectionTimeoutMS=30000,
                connectTimeoutMS=20000,
                socketTimeoutMS=20000,
                retryWrites=True,
                tlsAllowInvalidCertificates=True,
                retryReads=True
            )
        else:
            # Local MongoDB connection
            client = MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
        
        # Test connection
        client.admin.command('ping')
        db = client[MONGO_DB]
        
        if parsed.scheme.startswith('mongodb+srv'):
            print(f"[BreastCare AI] ✅ Connected to MongoDB Atlas — database: '{MONGO_DB}'")
        else:
            print(f"[BreastCare AI] ✅ Connected to Local MongoDB — database: '{MONGO_DB}'")
        
        MONGO_OK = True
        MONGO_ERROR = None
        return True
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        
        # Provide helpful error messages
        if "DNS query name does not exist" in error_msg:
            print("[BreastCare AI] ❌ MongoDB Atlas DNS resolution failed.")
            print("[BreastCare AI]    Please check your MongoDB Atlas cluster name and URI.")
            print("[BreastCare AI]    To fix: Update MONGO_URI in .env with correct Atlas URI")
        elif "Connection refused" in error_msg or "failed to connect" in error_msg:
            print("[BreastCare AI] ❌ Local MongoDB connection failed.")
            print("[BreastCare AI]    Please ensure MongoDB is installed and running locally.")
            print("[BreastCare AI]    To install: Download MongoDB Community Server")
        else:
            print(f"[BreastCare AI] ⚠️  MongoDB connection failed: {error_msg}")
        
        print("[BreastCare AI]    Running in OFFLINE mode — data will not persist.")
        print("[BreastCare AI]    Full error traceback:")
        traceback.print_exc()
        
        client = None
        db = None
        MONGO_OK = False
        MONGO_ERROR = error_msg
        return False

# Initialize MongoDB connection
connect_mongodb()

# MongoDB collections
def col(name):
    """Get a MongoDB collection, with reconnection attempt."""
    global db, client
    
    if db is None:
        # Try to reconnect
        if connect_mongodb():
            print(f"[BreastCare AI] 🔗 Reconnected to MongoDB Atlas")
        else:
            raise RuntimeError("MongoDB is not connected. Please check your Atlas URI in .env")
    
    return db[name]

# ── Features ──────────────────────────────────────────────────────────────────
FEATURES = [
    'radius_mean','texture_mean','smoothness_mean','compactness_mean',
    'concavity_mean','symmetry_mean','fractal_dimension_mean',
    'radius_se','texture_se','smoothness_se','compactness_se',
    'concavity_se','concave points_se','symmetry_se','fractal_dimension_se',
    'smoothness_worst','compactness_worst','concavity_worst',
    'symmetry_worst','fractal_dimension_worst'
]
FEATURE_DEFAULTS = {
    'radius_mean':13.37,'texture_mean':18.84,'smoothness_mean':0.0962,
    'compactness_mean':0.1043,'concavity_mean':0.0888,'symmetry_mean':0.1812,
    'fractal_dimension_mean':0.0628,'radius_se':0.4051,'texture_se':1.2169,
    'smoothness_se':0.00638,'compactness_se':0.0210,'concavity_se':0.0259,
    'concave points_se':0.0111,'symmetry_se':0.0207,'fractal_dimension_se':0.00380,
    'smoothness_worst':0.1323,'compactness_worst':0.2534,'concavity_worst':0.2720,
    'symmetry_worst':0.2900,'fractal_dimension_worst':0.0839
}

# ── ML Model loader with auto-retrain on version mismatch ─────────────────────
def _load_model():
    def _train_fresh():
        import pandas as pd
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler
        print("[BreastCare AI] Retraining model for current scikit-learn version...")
        df  = pd.read_csv(CSV_PATH)
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

def oid(id_str):
    """Safely convert string to ObjectId."""
    try:    return ObjectId(id_str)
    except: return None

def doc(mongo_doc):
    """Convert MongoDB doc to dict with string _id and id fields."""
    if not mongo_doc: return None
    d = dict(mongo_doc)
    d['id']  = str(d['_id'])
    d['_id'] = str(d['_id'])
    return d

def docs(cursor):
    return [doc(d) for d in cursor]

def run_prediction(feat_dict):
    import pandas as pd
    X = scaler.transform(pd.DataFrame([feat_dict], columns=FEATURES))
    r = int(model.predict(X)[0])
    c = float(max(model.predict_proba(X)[0])) * 100
    return r, c

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

@app.route('/signout')
def signout():
    session.clear()
    flash('Signed out.','info')
    return redirect(url_for('signin'))

# ── Notifications ─────────────────────────────────────────────────────────────
@app.route('/notifications')
@login_required
def notifications():
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
        if not fn:
            flash('Patient name required.','danger')
            return render_template('register_patient.html', user=cu(), patient=None, editing=False)
        pid = gen_pid()
        col('patients').insert_one({
            'patient_id':  pid,
            'full_name':   fn,
            'date_of_birth': request.form.get('date_of_birth',''),
            'gender':      request.form.get('gender',''),
            'contact':     request.form.get('contact',''),
            'email':       request.form.get('email',''),
            'address':     request.form.get('address',''),
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
        col('patients').update_one({'patient_id': patient_id}, {'$set':{
            'full_name':     request.form.get('full_name',''),
            'date_of_birth': request.form.get('date_of_birth',''),
            'gender':        request.form.get('gender',''),
            'contact':       request.form.get('contact',''),
            'email':         request.form.get('email',''),
            'address':       request.form.get('address',''),
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
            from image_processor_advanced import generate_annotated_image, extract_features
            fb = img_file.read()
            sn = f"{req['patient_id']}_{request_id}.jpg"
            ip = os.path.join(app.config['UPLOAD_FOLDER'], sn)
            with open(ip,'wb') as fp: fp.write(fb)
            img_path = ip
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
    from image_processor_advanced import extract_features
    from monitoring_system import log_prediction_event, check_system_drift, generate_drift_alert
    try:
        features = extract_features(f.read())
        
        # Check validation results
        if features.get('validation_failed', False):
            reasons = features.get('validation_reasons', [])
            confidence = features.get('validation_confidence', 0.0)
            flash(f'Image validation failed: {"; ".join(reasons)} (Confidence: {confidence:.2f})','danger')
            
            # Log validation failure to monitoring system
            validation_result = {
                'is_valid': False,
                'rejection_reasons': reasons,
                'confidence': confidence,
                'stage_results': features.get('stage_results', {})
            }
            log_prediction_event(features, validation_result)
            return redirect(url_for('upload_results', request_id=rid))
        
        if features.get('validation_passed', False):
            confidence = features.get('validation_confidence', 0.0)
            flash(f'Image validation passed with confidence: {confidence:.2f}','success')
            
            # Log successful validation
            validation_result = {
                'is_valid': True,
                'rejection_reasons': [],
                'confidence': confidence,
                'stage_results': features.get('stage_results', {})
            }
            log_prediction_event(features, validation_result)
            
        session['img_features'] = features
        flash('Features extracted from image!','success')
    except Exception as e:
        flash(f'Image processing failed: {e}','danger')
    return redirect(url_for('upload_results', request_id=rid))

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

        col('predictions').insert_one({
            'patient_id':    req['patient_id'],
            'request_id':    request_id,
            'lab_result_id': lab['id'],
            'features':      adj,
            'result':        result,
            'confidence':    confidence,
            'doctor_notes':  request.form.get('doctor_notes',''),
            'determined_by': session['user_id'],
            'created_at':    now_str(),
            'updated_at':    now_str()
        })
        col('lab_requests').update_one(
            {'_id': oid(request_id)},
            {'$set': {'status':'completed','updated_at': now_str()}})

        lbl = 'MALIGNANT' if result==1 else 'BENIGN'
        notify_role('admin',
            f"🏥 {req['patient_name']} [{req['patient_id']}] → {lbl} ({confidence:.1f}%)",
            url_for('all_predictions'))
        notify_role('receptionist',
            f"📋 Diagnosis complete: {req['patient_name']} [{req['patient_id']}]",
            url_for('patient_detail', patient_id=req['patient_id']))

        flash(f"Determination saved: {lbl} ({confidence:.1f}%)", 'success')
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
        d['full_name']   = pt['full_name']    if pt else '—'
        d['contact']     = pt.get('contact','') if pt else '—'
        d['gender']      = pt.get('gender','')  if pt else '—'
        d['doctor_name'] = dr['full_name']    if dr else '—'
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
        'full_name':    pt['full_name']         if pt else '—',
        'contact':      pt.get('contact','')    if pt else '—',
        'email':        pt.get('email','')      if pt else '—',
        'gender':       pt.get('gender','')     if pt else '—',
        'date_of_birth':pt.get('date_of_birth','') if pt else '—',
        'doctor_name':  dr['full_name']         if dr else '—',
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
    from pdf_generator import generate_single_pdf
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
    from pdf_generator import generate_all_pdf
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
    if request.method == 'POST':
        full_name = request.form.get('full_name','').strip()
        username = request.form.get('username','').strip()
        email = request.form.get('email','').strip()
        contact = request.form.get('contact','').strip()
        role = request.form.get('role','').strip()
        password = request.form.get('password','').strip()
        
        if not all([full_name, username, email, role, password]):
            flash('All fields are required.','danger')
            return render_template('admin_users.html', user=cu())
        
        # Validate phone number (must be 14 digits)
        if contact and not contact.isdigit():
            flash('Phone number must contain only digits.','danger')
            return render_template('admin_users.html', user=cu())
        
        if contact and len(contact) != 14:
            flash('Phone number must be exactly 14 digits.','danger')
            return render_template('admin_users.html', user=cu())
        
        # Check if username or email already exists
        if col('users').find_one({'$or': [{'username': username}, {'email': email}]}):
            flash('Username or email already exists.','danger')
            return render_template('admin_users.html', user=cu())
        
        # Create new user
        user_data = {
            'full_name': full_name,
            'username': username,
            'email': email,
            'contact': contact,
            'role': role,
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
    
    if request.method == 'POST':
        full_name = request.form.get('full_name','').strip()
        username = request.form.get('username','').strip()
        email = request.form.get('email','').strip()
        contact = request.form.get('contact','').strip()
        role = request.form.get('role','').strip()
        password = request.form.get('password','').strip()
        
        if not all([full_name, username, email, role]):
            flash('Name, username, email, and role are required.','danger')
            return render_template('admin_users.html', user=cu(), edit_user=edit_user)
        
        # Validate phone number (must be 14 digits)
        if contact and not contact.isdigit():
            flash('Phone number must contain only digits.','danger')
            return render_template('admin_users.html', user=cu(), edit_user=edit_user)
        
        if contact and len(contact) != 14:
            flash('Phone number must be exactly 14 digits.','danger')
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
    from monitoring_system import get_system_performance, check_system_drift, generate_drift_alert, export_monitoring_report
    
    # Get current metrics
    performance_metrics = get_system_performance()
    drift_result = check_system_drift()
    drift_alert = generate_drift_alert(drift_result) if drift_result['drift_detected'] else None
    
    return render_template('admin_monitoring.html', user=cu(), 
                           performance_metrics=performance_metrics,
                           drift_result=drift_result,
                           drift_alert=drift_alert)

@app.route('/admin/monitoring/export')
@role_required('admin')
def admin_monitoring_export():
    from monitoring_system import export_monitoring_report
    
    filename = export_monitoring_report()
    if filename:
        return send_file(filename, as_attachment=True,
                         download_name=f'system_monitoring_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
                         mimetype='application/json')
    else:
        flash('Failed to export monitoring data.','danger')
        return redirect(url_for('admin_monitoring'))

if __name__ == '__main__':
    # Use use_reloader=False to prevent SystemExit error when using debugger
    app.run(debug=True, port=5000, use_reloader=False)
