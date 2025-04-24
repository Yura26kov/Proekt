from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    plate = db.Column(db.String(20), unique=True, nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    vin = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    year = db.Column(db.Integer)
    mileage = db.Column(db.Float, default=0)
    last_maintenance_date = db.Column(db.DateTime)
    next_maintenance_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    fuel_records = db.relationship('FuelRecord', backref='vehicle', lazy=True)
    maintenance_records = db.relationship('MaintenanceRecord', backref='vehicle', lazy=True)

class FuelRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    fuel_quantity = db.Column(db.Float, nullable=False)
    fuel_cost = db.Column(db.Float, nullable=False)
    mileage = db.Column(db.Float, nullable=False)
    fuel_type = db.Column(db.String(20), nullable=False)  # Тип топлива (АИ-92, АИ-95, ДТ и т.д.)
    notes = db.Column(db.Text)  # Добавляем поле для заметок
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MaintenanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text, nullable=False)
    mileage = db.Column(db.Float, nullable=False)
    cost = db.Column(db.Float)
    next_maintenance_mileage = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow) 