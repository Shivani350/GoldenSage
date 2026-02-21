import os
from flask import Flask, render_template, request, redirect, session, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from modals import db, Guardian, Patient, Reminder, Notification, Connection # Ensure these are in modals.py

# 1. Setup and Configurations
load_dotenv()
app = Flask(__name__)
CORS(app) # Allows UnityHub to communicate with Flask

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or "a_very_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///seniorcare.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Create upload folder if missing
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize Database
db.init_app(app)

# --- ROUTES START HERE ---

# FIX FOR 404: The Landing Page
@app.route('/')
def index():
    return render_template('front.html')


@app.route('/main-page')
def main_landing():
    # This must match your "Main-page.html" filename exactly
    return render_template('Main-page.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = Guardian.query.filter_by(email=email, password=password).first()
        if user:
            session['guardian_id'] = user.id
            return redirect('/guardian-dashboard')
        return "Invalid credentials", 401
    return render_template('logincommon.html')

@app.route('/signup', methods=['GET'])
def show_signup():
    return render_template('signupcommon.html')

@app.route('/signup-patient', methods=['POST'])
def signup_patient():
    if 'guardian_id' not in session:
        return redirect('/login')
    
    new_patient = Patient(
        name=request.form['name'],
        email=request.form['email'],
        password=request.form['password'], 
        phone=request.form['phone'],
        medical_records=None, 
        guardian_id=session['guardian_id']
    )
    db.session.add(new_patient)
    db.session.commit()
    return redirect('/guardian-dashboard')

@app.route('/guardian-dashboard')
def dashboard():
    
    # 1. Fetch the guardian object from the database
    guardian = Guardian.query.get(session['guardian_id'])
    
    # 2. If the guardian exists, pass the patients list to the HTML
    if guardian:
        return render_template('guardian-dashboard.html', patients=guardian.patients, guardian=guardian)
    
   
@app.route('/patient-dashboard')
def patient_dashboard():
    # You need to know WHICH patient to show. 
    # For now, let's get the first one in the database as a test:
    patient_data = Patient.query.first() 
    
    # You MUST pass the variable to the template like this:
    return render_template('patient-dashboard.html', patient=patient_data)

@app.route('/gardian-login')
def gardian_login():
    return render_template('gardianlogin.html')

@app.route('/patient-login')
def patient_login():
    return render_template('patient-login.html')

@app.route('/patient-signup')
def patient_signup():
    return render_template('patient-signup.html')

# --- OTHER UTILITY PAGES ---
@app.route('/get-started')
def get_started():
    return render_template('get-started.html')

@app.route('/connection')
def connection_page():
    return render_template('connection.html')

@app.route('/after-gardian')
def after_guardian():
    return render_template('aftergardian.html')

@app.route('/create-user')
def create_user_page():
    return render_template('create-user.html')

@app.route('/stu-ngo-login')
def stu_ngo_login():
    return render_template('stu-ngo-login.html')

@app.route('/notifications')
def notifications():
    if 'guardian_id' not in session:
        return redirect('/login')
    feed = Notification.query.filter_by(user_id=session['guardian_id']).order_by(Notification.timestamp.desc()).all()
    return render_template('notifications.html', feed=feed)

@app.route('/trigger-refill/<int:patient_id>', methods=['POST'])
def trigger_refill(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    medicine_name = request.form.get('medicine_name', 'Medication')
    new_notif = Notification(
        user_id=patient.guardian_id,
        message=f"Refill requested for {medicine_name} by {patient.name}",
        timestamp=db.func.now()
    )
    db.session.add(new_notif)
    db.session.commit()
    return jsonify({"status": "success"})

@app.route('/trigger-sos/<int:patient_id>', methods=['POST'])
def trigger_sos(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    patient.is_emergency = True
    new_notif = Notification(
        user_id=patient.guardian_id,
        message=f"🚨 EMERGENCY: {patient.name} needs help!"
    )
    db.session.add(new_notif)
    db.session.commit()
    return jsonify({"status": "success"})

@app.route('/check-emergency')
def check_emergency():
    if 'guardian_id' in session:
        emergency = Patient.query.filter_by(guardian_id=session['guardian_id'], is_emergency=True).first()
        if emergency:
            return jsonify({"emergency_detected": True, "patient_name": emergency.name})
    return jsonify({"emergency_detected": False})

@app.route('/upload-record/<int:patient_id>', methods=['POST'])
def upload_record(patient_id):
    file = request.files.get('file')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        patient = Patient.query.get(patient_id)
        patient.medical_records = filename
        db.session.commit()
        return redirect('/guardian-dashboard')
    return "Invalid file", 400

@app.route('/api/create-account', methods=['POST'])
def create_account_from_unity():
    data = request.json
    if data['role'] == 'guardian':
        new_user = Guardian(email=data['email'], password=data['password'])
    else:
        new_user = Patient(name=data['name'], email=data['email'], guardian_id=data['guardian_id'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"status": "account created"}), 201

# --- EXECUTION BLOCK ---
if __name__ == "__main__":
    with app.app_context():
        db.create_all() 
    app.run(debug=True)