from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import Engine
from sqlalchemy import event
import datetime
import enum

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project_database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

class status_type(enum.Enum):
    NOT_STARTED = "not started"
    STARTED = "started"
    FINISHED = "finished"

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)
    start = db.Column(db.DateTime, default=datetime.datetime.today().date(), nullable=True)
    end = db.Column(db.DateTime, db.CheckConstraint("start <= end"), nullable=True)
    budget = db.Column(db.Float, db.CheckConstraint("budget >= 0"), nullable=True)
    avg_hourly_cost = db.Column(db.Float, db.CheckConstraint("avg_hourly_cost >= 0"), nullable=True)
    total_hours = db.Column(db.Float, db.CheckConstraint("total_hours >= 0"), nullable=True)
    total_costs = db.Column(db.Float, db.CheckConstraint("total_costs >= 0"), nullable=True)
    project_manager_id = db.Column(db.Integer, db.ForeignKey("members.id", ondelete="SET NULL", onupdate="CASCADE"))
    '''status = db.Column(db.String(16),
                       db.CheckConstraint("status == 'not started' OR status == 'started' OR status == 'finished'"),
                       default="not started", nullable=False)'''
    status = db.Column(db.Enum(status_type), nullable=False)
    tasks = db.relationship("Tasks", back_populates="project")
    phases = db.relationship("Phase", back_populates="project")
    project_manager = db.relationship("Members", back_populates="managed_project")
    costs = db.relationship("Costs", back_populates="project")
    hours = db.relationship("Hours", back_populates="project")


class Phase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), default="hankesuunnittelu", nullable=False)
 
    deadline = db.Column(db.DateTime, nullable=True)
    '''status = db.Column(db.String(16),
                       db.CheckConstraint("status == 'not started' OR status == 'started' OR status == 'finished'"),
                       default="not started", nullable=False)'''
    status = db.Column(db.Enum(status_type))
    project_id = db.Column(db.Integer, db.ForeignKey("project.id", ondelete="SET NULL", onupdate="CASCADE"))

    project = db.relationship("Project", back_populates="phases")
    task = db.relationship("Tasks", back_populates="phase")
    costs = db.relationship("Costs", back_populates="phase")

class Costs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id", ondelete="SET NULL", onupdate="CASCADE"))
    phase_id = db.Column(db.Integer, db.ForeignKey("phase.id", ondelete="SET NULL", onupdate="CASCADE"))
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(64), nullable=True)
    hourly_price = db.Column(db.Float, db.CheckConstraint("hourly_price >= 0"), nullable=True)
    quantity = db.Column(db.Float, db.CheckConstraint("quantity >= 0"), nullable=True)
    total_costs = db.column_property(hourly_price * quantity)
    #total_costs = db.Column(db.Float, db.CheckConstraint("total_costs >= 0"), nullable=True)
    project = db.relationship("Project", back_populates="costs")
    phase = db.relationship("Phase", back_populates="costs")

class Members(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)
    hourly_cost = db.Column(db.Float, db.CheckConstraint("hourly_cost >= 0"), nullable=True)

    # managed_project = db.relationship("Project", cascade="delete-orphan", back_populates="project_manager")
    managed_project = db.relationship("Project", back_populates="project_manager")
    membership = db.relationship("Teams", back_populates="team_members")
    hours = db.relationship("Hours", back_populates="employee")


class Tasks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id", ondelete="SET NULL", onupdate="CASCADE"))
    phase_id = db.Column(db.Integer, db.ForeignKey("phase.id", ondelete="SET NULL", onupdate="CASCADE"))
    name = db.Column(db.String(64), nullable=False, unique=True)
    total_hours = db.Column(db.Float, db.CheckConstraint("total_hours >= 0"), nullable=True)
    total_cost = db.Column(db.Float, db.CheckConstraint("total_cost >= 0"), nullable=True)
    start = db.Column(db.DateTime, default=datetime.datetime.today().date(), nullable=True)
    end = db.Column(db.DateTime, db.CheckConstraint("start <= end"), nullable=True)
    '''status = db.Column(db.String(16),
                       db.CheckConstraint("status == 'not started' OR status == 'started' OR status == 'finished'"),
                       default="not started", nullable=False)'''
    status = db.Column(db.Enum(status_type), default=status_type.NOT_STARTED)
    project = db.relationship("Project", back_populates="tasks")
    team = db.relationship("Teams", back_populates="team_tasks")
    phase = db.relationship("Phase", back_populates="task")
    hours = db.relationship("Hours", back_populates="task")


class Teams(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id", ondelete="SET NULL", onupdate="CASCADE"))
    member_id = db.Column(db.Integer, db.ForeignKey("members.id", ondelete="SET NULL", onupdate="CASCADE"))

    team_members = db.relationship("Members", back_populates="membership")
    team_tasks = db.relationship("Tasks", back_populates="team")

class Hours(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id", ondelete="SET NULL", onupdate="CASCADE"))
    project_id = db.Column(db.Integer, db.ForeignKey("project.id", ondelete="SET NULL", onupdate="CASCADE"))
    employee_id = db.Column(db.Integer, db.ForeignKey("members.id", ondelete="SET NULL", onupdate="CASCADE"))
    date = db.Column(db.DateTime, default=datetime.datetime.today().date(), nullable=True)
    time = db.Column(db.Float, db.CheckConstraint("time >= 0") , nullable=True)

    project = db.relationship("Project", back_populates="hours")
    task = db.relationship("Tasks", back_populates="hours")
    employee = db.relationship("Members", back_populates="hours")

<<<<<<< HEAD
db.create_all()
=======
if __name__ == "__main__":
    db.create_all()
>>>>>>> 8acf5420535ef0a9617f54f0cc8f0e78fcee71c9
