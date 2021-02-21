import os
import pytest
import tempfile
import sys

import database_gen

from database_gen import Project, Phase, Costs, Members, Tasks, Teams, Hours
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
import datetime


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

def _get_project(name="projekti", status="not started"):
    project = Project(
        name=name
        #status=status
    )
    return project

def _get_member():
    member = Members(
        name="testiukko",
        hourly_cost=1.2
    )
    return member

def _get_phase(name="testi phase", status="not started"):
    phase = Phase(
        name=name,
        status=status
    )
    return phase

def _get_cost():
    cost = Costs(
        name="testi cost",
    )
    return cost

def _get_task():
    task = Tasks(
        name="task",
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

def test_all_project_tests(db_handle):
    #test adds new project to database
    project = _get_project("p1","not started")
    phase = _get_phase()
    phase.project = project
    db_handle.session.add(project)
    db_handle.session.add(phase)
    db_handle.session.commit()
    assert Project.query.count() == 1
    #this works

    #test retrieves project from database and compares it to the added one
    new_project = Project.query.first()
    assert new_project == project
    #this works

    #test modifies an existing project in the database
    project.name = "uusi projekti"
    db_handle.session.add(project)
    db_handle.session.commit()
    assert Project.query.first().name == "uusi projekti"
    #this works

    #test removes a project from the database
    db_handle.session.delete(project)
    assert Project.query.count() == 0
    #this works

    #tests onDelete, by deleting the project_manager member from database
    member = _get_member()
    project = _get_project()
    project.project_manager = member
    db_handle.session.add(project)
    db_handle.session.commit()
    db_handle.session.delete(member)
    assert Project.query.first().project_manager == None
    #this works

    #tests onModify, by changing the project_manager
    member = _get_member()
    member2 = _get_member()
    member2.name = "uusi manageri"
    project.name = "projekti1"
    project.project_manager = member
    db_handle.session.add(project)
    db_handle.session.commit()
    assert Project.query.first().project_manager.name == "testiukko"
    project.project_manager = member2
    db_handle.session.add(project)
    db_handle.session.commit()
    #print([a.name for a in Members.query.filter_by(name="uusi manageri").first().managed_project])
    assert Members.query.filter_by(name="uusi manageri").first().managed_project[0].name == "projekti1"
    #this works

    #tests for foreign key violations, adding 2 projects with same names
    project2 = _get_project()
    project2.name = "projekti1"
    db_handle.session.add(project2)
    with pytest.raises(IntegrityError):
        db_handle.session.commit()
    #this works

#tests all the constraints in the Project table
def test_project_constraints(db_handle):
    project = Project(name="p1", 
                      start=datetime.date(2020,1,1),
                      end=datetime.date(2019,1,1),
                      budget=-1,
                      avg_hourly_cost=-1,
                      total_hours=-1,
                      total_costs=-1,
                      status="asdasd")
    db_handle.session.add(project)
    with pytest.raises(IntegrityError):
        db_handle.session.commit()


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
    member2.name = "uusi ukko"
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

def test_phase_constraints(db_handle):
    
    project = _get_project()
    phase = _get_phase()
    phase.project = project
    phase.status = "asdasd"
    db_handle.session.add(phase)

    with pytest.raises(IntegrityError):

        db_handle.session.commit()
        print(Phase.query.first().name)

    db_handle.session.rollback()
    phase.status = "not started"
    db_handle.session.add(phase)
    db_handle.session.commit()

    print(Phase.query.first().name)
    print(Phase.query.first().status)

    assert Phase.query.count() == 1

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
