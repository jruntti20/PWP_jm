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

    tasks = db.relationships("Tasks", back_populates="project")
    phases = db.relationships("Phase", back_populates="project")
    project_manager = db.relatioships("Members", back_populates("managed_project"))
    costs = db.relationships("Costs", back_populates="project")
    hours = db.relationships("Hours", back_populates="project")


class Phase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(64), nullable=False)
    project_id = db.Column(db.Integer, nullable=False, db.ForegnKey("project.id"))

    project = db.relationships("Project", back_populates="phases")
    task = db.relationships("Tasks", back_populates="phase")
    costs = db.relationships("Costs", back_populates="phase")

class Costs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, nullable=False, db.ForegnKey("project.id"))
    phase_id = db.Column(db.Integer, nullable=False, db.ForegnKey("phase.id"))
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(64), nullable=False)
    hourly_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    total_costs = db.Column(db.Float, nullable=False)

    project = db.relationships("Project", back_populates="costs")
    phase = db.relationships("Phase", back_populates="costs")

class Members(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    hourly_cost = db.Column(db.Float, nullable=False)

    managed_project = db.relationship("Project", back_populates="project_manager")
    membership = db.relationships("Teams", back_populates="team_members")
    hours = db.relationships("Hours", back_populates="employee")


class Tasks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, nullable=False, db.ForegnKey("project.id"))
    phase_id = db.Column(db.Integer, nullable=False, db.ForegnKey("phase.id"))
    name = db.Column(db.String(64), nullable=False)
    total_hours = db.Column(db.Float, nullable=False)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(64), nullable=False)

    project = db.relationships("Project", back_populates="tasks")
    team = db.relationships("Teams", back_populates="team_tasks")
    phase = db.relationships("Phase", back_populates="task")
    hours = db.relationships("Hours", back_populates="task")


class Teams(db.Model):
    task_id = db.Column(db.Integer, nullable=False, db.ForegnKey("tasks.id"))
    member_id = db.Column(db.Integer, nullable, db.ForegnKey("members.id"))

    team_members = db.relationships("Members", back_populates="membership")
    team_tasks = db.relationships("Tasks", back_populates="team")

class Hours(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, nullable=False, db.ForegnKey("tasks.id"))
    project_id = db.Column(db.Integer, nullable=False, db.ForeignKey="project.id")
    employee_id = db.Column(db.Integer, nullable=False, db.ForegnKey("members.id"))
    date = db.Column(db.DateTime, nullable=False)
    time = db.Column(db.Float, nullable=False)

    project = db.relationships("Project", back_populates="hours")
    task = db.relationships("Tasks", back_populates="hours")
    employee = db.relationships("Members", back_populates="hours")

db.create_all()
