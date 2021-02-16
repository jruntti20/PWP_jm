from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project_database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    budget = db.Column(db.Float, nullable=False)
    avg_hourly_cost = db.Column(db.Float, nullable=False)
    total_hours = db.Column(db.Float, nullable=False)
    total_costs = db.Column(db.Float, nullable=False)
    project_manager_id = db.Column(db.Integer, nullable=False, db.ForeignKey("members.id"))
    status = db.Column(db.String(64), nullable=False, db.ForeignKey(""))

class Phase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(64), nullable=False)
    project_id = db.Column(db.Integer, nullable=False)

class Costs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, nullable=False)
    phase_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(64), nullable=False)
    hourly_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    total_costs = db.Column(db.Float, nullable=False)

class Members(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    hourly_cost = db.Column(db.Float, nullable=False)

class Tasks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(64), nullable=False)
    phase = db.Column(db.String(64), nullable=False)
    total_hours = db.Column(db.Float, nullable=False)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(64), nullable=False)

class Teams(db.Model):
    task_id = db.Column(db.Integer)
    member_id = db.Column(db.Integer)

class Hours(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, nullable=False)
    project_id = db.Column(db.Integer, nullable=False)
    employee_id = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    time = db.Column(db.Float, nullable=False)

db.create_all()
