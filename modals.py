from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# 1. Guardian Model (Main Account)
class Guardian(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    # Relationships
    patients = db.relationship('Patient', backref='guardian', lazy=True)
    notifications = db.relationship('Notification', backref='receiver', lazy=True)

# 2. Patient Model (Linked to Guardian)
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    medical_records = db.Column(db.String(255)) # Stores filename
    is_emergency = db.Column(db.Boolean, default=False) # For SOS tracking
    guardian_id = db.Column(db.Integer, db.ForeignKey('guardian.id'), nullable=False)
    # Relationships
    reminders = db.relationship('Reminder', backref='patient', lazy=True)

# 3. Reminder Model (For Voice Bot)
class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(200), nullable=False)
    time = db.Column(db.String(10), nullable=False) # Format: "HH:MM"
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)

# 4. Notification Model (Refill, SOS, Connections)
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('guardian.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

# 5. Connection Model (Guardian to Guardian Requests)
class Connection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('guardian.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('guardian.id'), nullable=False)
    status = db.Column(db.String(20), default='pending') # 'pending' or 'accepted'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)