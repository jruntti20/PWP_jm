from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project_database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    start = db.Column(db.DateTime, nullable=True)
    end = db.Column(db.DateTime, nullable=True)
    budget = db.Column(db.Float, nullable=True)
    avg_hourly_cost = db.Column(db.Float, nullable=True)
    total_hours = db.Column(db.Float, nullable=True)
    total_costs = db.Column(db.Float, nullable=True)
    project_manager_id = db.Column(db.Integer, db.ForeignKey("members.id"))
    status = db.Column(db.String(64), nullable=False)

    tasks = db.relationship("Tasks", back_populates="project")
    phases = db.relationship("Phase", back_populates="project")
    project_manager = db.relationship("Members", back_populates="managed_project")
    costs = db.relationship("Costs", back_populates="project")
    hours = db.relationship("Hours", back_populates="project")


class Phase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    deadline = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(64), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"))

    project = db.relationship("Project", back_populates="phases")
    task = db.relationship("Tasks", back_populates="phase")
    costs = db.relationship("Costs", back_populates="phase")

class Costs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"))
    phase_id = db.Column(db.Integer, db.ForeignKey("phase.id"))
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(64), nullable=True)
    hourly_price = db.Column(db.Float, nullable=True)
    quantity = db.Column(db.Float, nullable=True)
    total_costs = db.Column(db.Float, nullable=True)

    project = db.relationship("Project", back_populates="costs")
    phase = db.relationship("Phase", back_populates="costs")

class Members(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    hourly_cost = db.Column(db.Float, nullable=True)

    managed_project = db.relationship("Project", back_populates="project_manager")
    membership = db.relationship("Teams", back_populates="team_members")
    hours = db.relationship("Hours", back_populates="employee")


class Tasks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"))
    phase_id = db.Column(db.Integer, db.ForeignKey("phase.id"))
    name = db.Column(db.String(64), nullable=False)
    total_hours = db.Column(db.Float, nullable=True)
    start = db.Column(db.DateTime, nullable=True)
    end = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(64), nullable=False)

    project = db.relationship("Project", back_populates="tasks")
    team = db.relationship("Teams", back_populates="team_tasks")
    phase = db.relationship("Phase", back_populates="task")
    hours = db.relationship("Hours", back_populates="task")


class Teams(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"))
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"))

    team_members = db.relationship("Members", back_populates="membership")
    team_tasks = db.relationship("Tasks", back_populates="team")

class Hours(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"))
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"))
    employee_id = db.Column(db.Integer, db.ForeignKey("members.id"))
    date = db.Column(db.DateTime, nullable=True)
    time = db.Column(db.Float, nullable=True)

    project = db.relationship("Project", back_populates="hours")
    task = db.relationship("Tasks", back_populates="hours")
    employee = db.relationship("Members", back_populates="hours")

#db.create_all()
