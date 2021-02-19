import os
import pytest
import tempfile

import database_gen

from database_gen import Project, Phase, Costs, Members, Tasks, Teams, Hours
from sqlalchemy.engine import Engine
from sqlalchemy import event

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture
def db_handle():
    db_fd, db_fname = tempfile.mkstemp()
    database_gen.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_fname
    database_gen.app.config["TESTING"] = True

    with database_gen.app.app_context():
        database_gen.db.create_all()

    yield database_gen.db

    database_gen.db.session.remove()
    os.close(db_fd)
    os.unlink(db_fname)

def _get_project():
    project = Project(
        name="projekti 1",
        status="not started"
    )
    return project

def _get_member():
    member = Members(
        name="testiukko",
        hourly_cost=1.2
    )
    return member

def _get_phase():
    phase = Phase(
        name="testi phase",
        status="not started"
    )
    return phase

def _get_cost():
    cost = Costs(
        name="testi cost",
    )
    return cost

def _get_task():
    task = Tasks(
        name="testi task",
        status="not started"
    )
    return task

def _get_team():
    team = Teams(
    )
    return team

def _get_hour():
    hour = Hours(
    )
    return hour

#test adds new member to database
def test_create_member(db_handle):
    member = _get_member()
    db_handle.session.add(member)
    db_handle.session.commit()
    assert Members.query.count() == 1

def test_create_project(db_handle):
    #test adds new project and new member and add this member to test the foreign key project_manager
    project = _get_project()
    member = _get_member()
    project.project_manager = member
    db_handle.session.add(project)
    db_handle.session.commit()
    assert Project.query.count() == 1
    assert Members.query.count() == 1
    db_project = Project.query.first()
    db_member = Members.query.first()
    assert db_project.project_manager == db_member
    assert db_project in db_member.managed_project

    #test adds a new member and changes the project_manager to be this one
    member2 = _get_member()
    project.project_manager = member2
    db_handle.session.add(project)
    db_handle.session.commit()
    assert Project.query.count() == 1
    assert Members.query.count() == 2
    db_project = Project.query.first()
    db_member2 = Members.query.all()[-1]
    assert db_project.project_manager == db_member2
    assert db_project in db_member2.managed_project

    #test removes a member from the database
    db_handle.session.delete(db_member)
    db_handle.session.commit()
    assert Members.query.count() == 1

#test adds new phase to database
def test_create_phase(db_handle):
    phase = _get_phase()
    db_handle.session.add(phase)
    db_handle.session.commit()
    assert Phase.query.count() == 1

#test adds new cost to database
def test_create_cost(db_handle):
    cost = _get_cost()
    db_handle.session.add(cost)
    db_handle.session.commit()
    assert Costs.query.count() == 1

#test adds new task to database
def test_create_task(db_handle):
    task = _get_task()
    db_handle.session.add(task)
    db_handle.session.commit()
    assert Tasks.query.count() == 1

#test adds new team to database
def test_create_team(db_handle):
    team = _get_team()
    db_handle.session.add(team)
    db_handle.session.commit()
    assert Teams.query.count() == 1

#test adds new hour to database
def test_create_hour(db_handle):
    hour = _get_hour()
    db_handle.session.add(hour)
    db_handle.session.commit()
    assert Hours.query.count() == 1