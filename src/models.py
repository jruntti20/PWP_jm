from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import Engine
from sqlalchemy import event
import datetime
import enum
from app import db

class status_type(enum.Enum):
    NOT_STARTED = "not started"
    STARTED = "started"
    FINISHED = "finished"

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)
    start = db.Column(db.DateTime, default=datetime.datetime.today().date(), nullable=True)
    end = db.Column(db.DateTime, db.CheckConstraint("start <= end"), nullable=True)
    project_manager_id = db.Column(db.Integer, db.ForeignKey("members.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)

    status = db.Column(db.Enum(status_type), default=status_type.NOT_STARTED, nullable=False)
    tasks = db.relationship("Tasks", back_populates="project")
    phases = db.relationship("Phase", back_populates="project")
    project_manager = db.relationship("Members", back_populates="managed_project")


class Phase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), default="hankesuunnittelu", nullable=False)
 
    deadline = db.Column(db.DateTime, nullable=True)

    status = db.Column(db.Enum(status_type))
    project_id = db.Column(db.Integer, db.ForeignKey("project.id", ondelete="SET NULL", onupdate="CASCADE"))

    project = db.relationship("Project", back_populates="phases")
    task = db.relationship("Tasks", back_populates="phase")

class Members(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)

    managed_project = db.relationship("Project", back_populates="project_manager")
    membership = db.relationship("Teams", back_populates="team_members")


class Tasks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id", ondelete="SET NULL", onupdate="CASCADE"))
    phase_id = db.Column(db.Integer, db.ForeignKey("phase.id", ondelete="SET NULL", onupdate="CASCADE"))
    name = db.Column(db.String(64), nullable=False, unique=True)
    start = db.Column(db.DateTime, default=datetime.datetime.today().date(), nullable=True)
    end = db.Column(db.DateTime, db.CheckConstraint("start <= end"), nullable=True)

    status = db.Column(db.Enum(status_type))
    project = db.relationship("Project", back_populates="tasks")
    team = db.relationship("Teams", back_populates="team_tasks")
    phase = db.relationship("Phase", back_populates="task")


class Teams(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id", ondelete="SET NULL", onupdate="CASCADE"))
    member_id = db.Column(db.Integer, db.ForeignKey("members.id", ondelete="SET NULL", onupdate="CASCADE"))

    team_members = db.relationship("Members", back_populates="membership")
    team_tasks = db.relationship("Tasks", back_populates="team")
