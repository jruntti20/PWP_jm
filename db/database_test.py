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
        name=name,
        status=status
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

    #tests for unique violations, adding 2 projects with same names
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

def test_all_member_tests(db_handle):
    #test adds new member to database
    member = _get_member()
    db_handle.session.add(member)
    db_handle.session.commit()
    assert Members.query.count() == 1
    #this works

    #test retrieves member from database and compares it to the added one
    new_member = Members.query.first()
    assert new_member == member
    #this works

    #test modifies an existing member in the database
    member.name = "uusi ukko"
    db_handle.session.add(member)
    db_handle.session.commit()
    assert Members.query.first().name == "uusi ukko"
    #this works

    #test removes a member from the database
    db_handle.session.delete(member)
    assert Members.query.count() == 0
    #this works

    #tests for unique violations, adding 2 members with same names
    member = _get_member()
    member2 = _get_member()
    db_handle.session.add(member)
    db_handle.session.add(member2)
    with pytest.raises(IntegrityError):
        db_handle.session.commit()
    #this works

#tests all the constraints in the Members table, name not null and hourly cost >= 0
def test_member_constraints(db_handle):
    member = Members(hourly_cost=-1)
    db_handle.session.add(member)
    with pytest.raises(IntegrityError):
        db_handle.session.commit()

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

def test_all_costs_tests(db_handle):
    #test adds new cost to database
    cost = _get_cost()
    db_handle.session.add(cost)
    db_handle.session.commit()
    assert Costs.query.count() == 1
    #this works

    #test retrieves cost from database and compares it to the added one
    new_cost = Costs.query.first()
    assert new_cost == cost
    #this works

    #test modifies an existing cost in the database
    cost.name = "uusi kustannus"
    db_handle.session.add(cost)
    db_handle.session.commit()
    assert Costs.query.first().name == "uusi kustannus"
    #this works

    #test removes a cost from the database
    db_handle.session.delete(cost)
    assert Project.query.count() == 0
    #this works

    #tests onDelete, by deleting the phase and project from database
    phase = _get_phase()
    project = _get_project()
    cost = _get_cost()
    cost.phase = phase
    cost.project = project
    db_handle.session.add(cost)
    db_handle.session.commit()
    db_handle.session.delete(phase)
    assert Costs.query.first().phase == None
    db_handle.session.delete(project)
    assert Costs.query.first().project == None
    #this works

    #tests onModify, by changing the phase and project
    phase1 = _get_phase()
    phase2 = _get_phase()
    phase2.name = "phase2"
    project1 = _get_project()
    project2 = _get_project(name="toinen projekti")
    cost.phase = phase1
    cost.project = project1
    db_handle.session.add(cost)
    db_handle.session.commit()
    assert Costs.query.first().phase.name == "testi phase"
    assert Costs.query.first().project.name == "projekti"
    cost.phase = phase2
    cost.project = project2
    db_handle.session.add(cost)
    db_handle.session.commit()
    assert Project.query.filter_by(name="toinen projekti").first().costs[0].name == "testi cost"
    assert Phase.query.filter_by(name="phase2").first().costs[0].name == "testi cost"
    #this works

#tests all the constraints in the Costs table, hourly_price and quantity >= 0
def test_cost_constraints(db_handle):
    cost = Costs(hourly_price=-1,
                 quantity=-1)
    db_handle.session.add(cost)
    with pytest.raises(IntegrityError):
        db_handle.session.commit()


def test_all_task(db_handle):
    # test adds new task to database
    task = _get_task()
    db_handle.session.add(task)
    db_handle.session.commit()
    assert Tasks.query.count() == 1

    # test retrieves task from database and compares it to the added one
    new_task = Tasks.query.first()
    assert new_task == task
    # this works

    #test modifies an existing task in the database
    task.name = "uusi taski"
    db_handle.session.add(task)
    db_handle.session.commit()
    assert Tasks.query.first().name == "uusi taski"
    #this works

    #test removes a task from the database
    db_handle.session.delete(task)
    assert Tasks.query.count() == 0
    #this works

    ##tests onDelete, by deleting the phase and project from database
    task = _get_task()
    project = _get_project()
    phase = _get_phase()
    task.project = project
    task.phase = phase
    db_handle.session.add(task)
    db_handle.session.commit()
    db_handle.session.delete(project)
    assert Tasks.query.first().project == None
    db_handle.session.delete(phase)
    assert Tasks.query.first().phase == None
    #this works

    #tests onModify, by changing the phase and project
    phase1 = _get_phase()
    phase2 = _get_phase()
    phase2.name = "phase2"
    project1 = _get_project()
    project2 = _get_project(name="toinen projekti")
    task.phase = phase1
    task.project = project1
    db_handle.session.add(task)
    db_handle.session.commit()
    assert Tasks.query.first().phase.name == "testi phase"
    assert Tasks.query.first().project.name == "projekti"
    task.phase = phase2
    task.project = project2
    db_handle.session.add(task)
    db_handle.session.commit()
    assert Project.query.filter_by(name="toinen projekti").first().tasks[0].name == "task"
    assert Phase.query.filter_by(name="phase2").first().task[0].name == "task"
    #this works

    # tests for foreign key violations, adding 2 tasks with same names
    task2 = _get_task()
    task2.name = "task"
    db_handle.session.add(task2)
    with pytest.raises(IntegrityError):
        db_handle.session.commit()
    # this works

    # tests all the constraints in the Costs table, name not null and hourly_price, quantity and total_costs >= 0
    def test_task_constraints(db_handle):
        task = Tasks(name="taski",
                          start=datetime.date(2020, 1, 1),
                          end=datetime.date(2019, 1, 1),
                          total_hours=-1,
                          total_cost=-1,
                          status="asdasd")
        db_handle.session.add(task)
        with pytest.raises(IntegrityError):
            db_handle.session.commit()


def test_all_team(db_handle):
    # test adds new team to database
    team = _get_team()
    db_handle.session.add(team)
    db_handle.session.commit()
    assert Teams.query.count() == 1
    #this works

    # test retrieves team from database and compares it to the added one
    new_team = Teams.query.first()
    assert new_team == team
    # this works

    # test removes a task from the database
    db_handle.session.delete(team)
    assert Teams.query.count() == 0
    # this works

    ##tests onDelete, by deleting the member and team from database
    team = _get_team()
    member = _get_member()
    task = _get_task()
    team.team_members = member
    team.team_tasks = task
    db_handle.session.add(team)
    db_handle.session.commit()
    db_handle.session.delete(member)
    assert Teams.query.first().team_members == None
    db_handle.session.delete(task)
    assert Teams.query.first().team_tasks == None
    #this works

    #tests onModify, by changing the member and task
    member1= _get_member()
    member2= _get_member()
    member2.name = "member2"
    task1 = _get_task()
    task2 = _get_task()
    task2.name = "task2"
    team.team_members = member1
    team.team_tasks = task1
    db_handle.session.add(team)
    db_handle.session.commit()
    assert Teams.query.first().team_members.name == "testiukko"
    assert Teams.query.first().team_tasks.name == "task"
    team.team_members = member2
    team.team_tasks = task2
    db_handle.session.add(team)
    db_handle.session.commit()
    assert Members.query.filter_by(name="member2").first().membership[0].id == 1
    assert Tasks.query.filter_by(name="task2").first().team[0].id == 1
    #this works

#test adds new hour to database
def test_create_hour(db_handle):
    hour = _get_hour()
    db_handle.session.add(hour)
    db_handle.session.commit()
    assert Hours.query.count() == 1
