from flask import Flask, Response, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_restful import Resource
from flask_restful import Api
from utils import MasonBuilder, LINK_RELATIONS_URL, MASON, create_error_response
from sqlalchemy.exc import IntegrityError, OperationalError
from jsonschema import validate, ValidationError
import datetime
import enum
import json

app = Flask(__name__, static_folder="static")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
api = Api(app)
db = SQLAlchemy(app)

from models import *

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

class ProjectBuilder(MasonBuilder):
    @staticmethod
    def project_schema(method=None):
        if method == None:
            schema = {
                "type": "object",
                "required": ["name", "status"]
                }
        else:
            schema = {
                "type": "object",
                "required": ["name"]
                }
        props = schema["properties"] = {}
        props["name"] = {
            "description": "Name of the project",
            "type": "string"
            }
        props["start"] = {
            "description": "Start date of the project",
            "type": "string",
            "pattern": "^[0-9]{4}-[01][0-9]-[0-3][0-9]$"
            }
        props["end"] = {
            "description": "End date of the project",
            "type": "string",
            "pattern": "^[0-9]{4}-[01][0-9]-[0-3][0-9]$"
            }
        props["project_manager"] = {
            "description": "Name of the project manager",
            "type": "string"
            }
        props["status"] = {
            "description": "Status of the project",
            "type": "string",
            "enum": ["NOT_STARTED", "STARTED", "FINISHED"]
            }
        return schema

    def add_control_add_project(self):
        self.add_control("promana:add-project",
                         "/api/projects/",
                         method="POST",
                         encoding="json",
                         title="Add new project",
                         schema=self.project_schema())

    def add_control_edit_project(self, project):
        self.add_control("edit",
                         f"/api/projects/{project}/",
                         method="PUT",
                         encoding="json",
                         title="Edit project",
                         schema=self.project_schema())

    def add_control_project_members(self, project):
        self.add_control("promana:project-members",
                         f"/api/projects/{project}/members/")

    def add_control_project_phase(self, project):
        self.add_control("promana:project-phase",
                         f"/api/projects/{project}/phase/")
    
    def add_control_delete_project(self, project):
        self.add_control("promana:delete",
                         f"/api/projects/{project}/",
                         method="DELETE")

class MemberBuilder(MasonBuilder):
    @staticmethod
    def member_schema():
        schema = {
            "type": "object",
            "required": ["name"]
            }
        props = schema["properties"] = {}
        props["name"] = {
            "description": "Name of the member",
            "type": "string"
            }
        return schema


    def add_control_add_member(self, project=None, phase=None, task=None):
        if project == None:
            self.add_control("promana:add-member",
                             "/api/members/",
                             method="POST",
                             encoding="json",
                             title="Add new member",
                             schema=self.member_schema())
        elif task == None:
            self.add_control("promana:add-member",
                             f"/api/projects/{project}/members/",
                             method="POST",
                             encoding="json",
                             title="Add new member to project",
                             schema=self.member_schema())
        else:
            self.add_control("promana:add-member",
                             f"/api/projects/{project}/phases/{phase}/tasks/{task}/members/",
                             method="POST",
                             encoding="json",
                             title="Add new member to task",
                             schema=self.member_schema())
    
    def add_control_edit_member(self, member):
        self.add_control("edit",
                         f"/api/members/{member}/",
                         method="PUT",
                         encoding="json",
                         title="Edit member",
                         schema=self.member_schema())
    
    def add_control_up_project(self, project):
        self.add_control("up",
                         f"/api/projects/{project}/members/")
    
    def add_control_up_task(self, project, phase, task):
        self.add_control("up",
                         f"/api/projects/{project}/phases/{phase}/tasks/{task}/members/")
    
    def add_control_delete_member(self, member, project=None, phase=None, task=None):
        if project == None:
            self.add_control("promana:delete",
                             api.url_for(MemberItem, member=member),
                             #f"/api/members/{member}/",
                             method="DELETE")
        elif task == None:
            self.add_control("promana:delete",
                             f"/api/projects/{project}/members/{member}/",
                             method="DELETE")
        else:
            self.add_control("promana:delete",
                             f"/api/projects/{project}/phases/{phase}/tasks/{task}/members/{member}/",
                             method="DELETE")

class ProjectCollection(Resource):
    def get(self):
        # get all projects
        db_projects = Project.query.all()

        if db_projects == None:
            return Response(status=501)

        body = ProjectBuilder()
        body.add_namespace("promana", LINK_RELATIONS_URL)
        body.add_control("self", api.url_for(ProjectCollection))
        body.add_control_add_project()
        body["items"] = []

        for project in db_projects:
            try:
                start=project.start.strftime("%Y-%m-%d")
            except AttributeError:
                start = None
            try:
                end=project.end.strftime("%Y-%m-%d")
            except AttributeError:
                end = None
            if project.project_manager == None:
                manager=None
            else:
                manager=project.project_manager.name
            item = ProjectBuilder(
                name=project.name,
                start=start,
                end=end,
                project_manager=manager,
                status=str(project.status.value)
                )
            item.add_control("self", api.url_for(ProjectItem, project=project.name))
            item.add_control_delete_project(project.name)
            body["items"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self):
        # add new project
        db.session.rollback()
        if not request.json:
            return create_error_response(415,
                                         "Unsupported media type",
                                         "Requests must be JSON")
        try:
            validate(request.json, ProjectBuilder.project_schema())
        except ValidationError as e:
            return create_error_response(400,
                                         "Invalid JSON document",
                                         str(e))

        manager, start, end = None, None, None
        new_project = Project(name=request.json["name"],
                              status=status_type[request.json["status"]])
        try:
            manager = Members.query.filter_by(name=request.json["project_manager"]).first()
        except KeyError:
            pass
        try:
            start = request.json["start"]
        except KeyError:
            pass
        try:
            end = request.json["end"]
        except KeyError:
            pass
        if manager != None:
            new_project.project_manager = manager
        if start != None:
            new_project.start=datetime.datetime.strptime(start, "%Y-%m-%d")
        if end != None:
            new_project.end=datetime.datetime.strptime(end, "%Y-%m-%d")
        try:
            db.session.add(new_project)
            db.session.commit()
        except IntegrityError:
            return create_error_response(409,
                                         "Already exists",
                                         "Project with name '{}' already exists.".format(request.json["name"]))

        return Response(status=201, headers={"location": api.url_for(ProjectItem, project=new_project.name)})


class ProjectItem(Resource):
    #get project
    def get(self, project):
        db_project = Project.query.filter_by(name=project).first()
        if db_project == None:
            return create_error_response(404, "Not found", f"Project with name {project} not found.")

        if db_project.project_manager == None:
            manager=None
        else:
            manager=db_project.project_manager.name

        if db_project.start != None:
            db_project.start=datetime.datetime.strftime(db_project.start, "%Y-%m-%d")

        if db_project.end != None:
            db_project.end=datetime.datetime.strftime(db_project.end, "%Y-%m-%d")

        body = ProjectBuilder(name=db_project.name,
                              start=str(db_project.start),
                              end=str(db_project.end),
                              project_manager=str(manager),
                              status=str(db_project.status.value))

        body.add_namespace("promana", LINK_RELATIONS_URL)
        body.add_control("self", api.url_for(ProjectItem, project=project))
        body.add_control("collection", api.url_for(ProjectCollection))
        body.add_control_edit_project(project)
        body.add_control_delete_project(project)

        return Response(json.dumps(body), 200, mimetype=MASON)

    #edit project
    def put(self, project):
        db.session.rollback()

        if not request.json:
            return create_error_response(415,
                                         "Unsupported media type",
                                         "Requests must be JSON")

        try:
            validate(request.json, ProjectBuilder.project_schema("put"))
        except ValidationError as e:
            return create_error_response(400,
                                         "Invalid JSON document",
                                         str(e))

        db_project = Project.query.filter_by(name=project).first()
        if db_project == None:
            return create_error_response(404,
                                         "not found",
                                         f"project with name {project} not found")
        manager=None
        try:
            manager = Members.query.filter_by(name=request.json["project_manager"]).first()
        except (KeyError, TypeError):
            pass

        if manager != None:
            db_project.project_manager = manager

        try:
            db_project.name = request.json["name"]
        except (KeyError, TypeError):
            pass

        try:
            db_project.start = datetime.datetime.strptime(request.json["start"], "%Y-%m-%d")
        except (KeyError, TypeError):
            pass

        try:
            db_project.end = datetime.datetime.strptime(request.json["end"], "%Y-%m-%d")
        except (KeyError, TypeError):
            pass

        try:
            db_project.status = request.json["status"]
        except (KeyError, TypeError):
            pass

        try:
            db.session.commit()
        except IntegrityError:
            return create_error_response(409,
                                         "already exists",
                                         "project with name already exists")

        return Response(status=204, headers={"location":api.url_for(ProjectItem, project=db_project.name)})

    # delete project
    def delete(self, project):
        db_project = Project.query.filter_by(name=project).first()
        if db_project is None:
            return create_error_response(404,
                                         "Not found", 
                                         "No project was found with the name {}".format(project))
        db.session.delete(db_project)
        db.session.commit()
        
        return Response(status=204)

class MemberCollection(Resource):
    def get(self):
        # get all members
        db_members = Members.query.all()

        if db_members == None:
            return Response(status=200)

        body = MemberBuilder()
        body.add_namespace("promana", LINK_RELATIONS_URL)
        body.add_control("self", api.url_for(MemberCollection))
        body.add_control_add_member()
        body["items"] = []

        for member in db_members:
            item = MemberBuilder(name=member.name)
            item.add_control("self", api.url_for(MemberItem, member=member.name))
            body["items"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self):
        # add new member
        if not request.json:
            return create_error_response(415,
                                         "Unsupported media type",
                                         "Requests must be JSON")

        try:
            validate(request.json, MemberBuilder.member_schema())
        except ValidationError as e:
            return create_error_response(400,
                                         "Invalid JSON document",
                                         str(e))

        new_member = Members(name=request.json["name"])
        
        try:
            db.session.add(new_member)
            db.session.commit()
        except IntegrityError:
            return create_error_response(409,
                                         "Already exists", 
                                         "Member with name '{}' already exists.".format(request.json["name"]))

        return Response(status=201, headers={"Location": api.url_for(MemberItem, member=new_member.name)})

class MemberItem(Resource):
    #get member
    def get(self, member):
        db_member = Members.query.filter_by(name=member).first()
        if db_member == None:
            return create_error_response(404,
                                         "Not found", 
                                         "No member was found with the name {}".format(member))

        body = MemberBuilder(name=db_member.name)
        body.add_namespace("promana", LINK_RELATIONS_URL)
        body.add_control("self", api.url_for(MemberItem, member=member))
        body.add_control("collection", api.url_for(MemberCollection))
        body.add_control_edit_member(member)
        body.add_control_delete_member(member)

        return Response(json.dumps(body), 200, mimetype=MASON)

    #edit member
    def put(self, member):

        if not request.json:
            return create_error_response(415,
                                         "Unsupported media type",
                                         "Requests must be JSON")

        try:
            validate(request.json, MemberBuilder.member_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        db_member = Members.query.filter_by(name=member).first()
        if db_member == None:
            return create_error_response(404,
                                         "Not found", 
                                         "No member was found with the name {}".format(member))

        db_member.name = request.json["name"]

        try:
            db.session.commit()
        except IntegrityError:
            return create_error_response(409,
                                         "Already exists", 
                                         "Member with name '{}' already exists.".format(request.json["name"]))

        return Response(status=204, headers={"location":api.url_for(MemberItem, member=db_member.name)})

    # delete member
    def delete(self, member):
        db_member = Members.query.filter_by(name=member).first()
        if db_member is None:
            return create_error_response(404,
                                         "Not found", 
                                         "No member was found with the name {}".format(member))

        db.session.delete(db_member)
        db.session.commit()
        
        return Response(status=204)

class ProjectMembers(Resource):
    # get all project members
    def get(self, project):
        db_project = Project.query.filter_by(name=project).first()
        if db_project == None:
            return create_error_response(404,
                                         "Project not found",
                                         f"Project with name {project} not found")

        body = MemberBuilder()
        body.add_namespace("promana", LINK_RELATIONS_URL)
        body.add_control("self", api.url_for(ProjectMembers, project=project))
        body.add_control("up", f"/api/projects/{project}/")
        body.add_control_delete_member("member", project=project)
        body.add_control_add_member(project=project)
        body["items"] = []

        db_tasks = Tasks.query.filter_by(project_id=db_project.id)

        for task in db_tasks:
            db_teams = Teams.query.filter_by(team_tasks=task)
            for team in db_teams:
                member = team.team_members
                if member is not None:
                    try:
                        if member.name not in body["items"]:
                            item = MemberBuilder(name=member.name)
                            item.add_control("self", api.url_for(ProjectMemberItem, project=project, member=member.name))
                            body["items"].append(item)
                    except AttributeError:
                        return create_error_response(404, "not found", "user not found")

        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self, project):
        if not request.json:
            return create_error_response(415, "Unsupported media type",
                "Requests must be JSON"
            )
        try:
            validate(request.json, MemberBuilder.member_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))
        # add new member to task
        db_member = Members.query.filter_by(name=request.json["name"]).first()
        db_task = Tasks.query.filter_by(name=f"{project}-default").first()
        db_project = Project.query.filter_by(name=project).first()

        if db_member == None:
            return create_error_response(404, "not found", f"member {request.json['name']} not in database")
        if db_task == None:
            new_task = Tasks(project=db_project, name=f"{project}-default", status=status_type["NOT_STARTED"])
            db.session.add(new_task)
            db.session.commit()

        db_task = Tasks.query.filter_by(name=f"{project}-default").first()
        db_team = Teams.query.filter_by(task_id=db_task.id, member_id=db_member.id).first()
        if db_team != None:
            return create_error_response(409, "Already exists", 
                "Member already in task '{}'.".format(db_task.name)
            )
        new_team = Teams(team_tasks=db_task,
                         team_members=db_member)

        try:
            db.session.add(new_team)
            db.session.commit()
        except IntegrityError:
            return create_error_response(409, "Already exists", 
                "Member already in task '{}'.".format(task)
            )
        return Response(status=201, headers={"Location": api.url_for(ProjectMemberItem, project=project, member=db_member.name)})

class ProjectMemberItem(Resource):
    def get(self, project, member):
        db_member = Members.query.filter_by(name=member).first()
        if db_member == None:
            return create_error_response(404,
                                         "Not found", 
                                         "No member was found with the name {}".format(member))

        body = MemberBuilder(name=db_member.name)
        body.add_control("self", api.url_for(ProjectMemberItem, project=project, member=member))
        body.add_control("up", api.url_for(ProjectMembers, project=project))

        return Response(json.dumps(body), 200, mimetype=MASON)

    # delete member from project
    def delete(self, project, member):
        db_project = Project.query.filter_by(name=project).first()
        if db_project == None:
            return create_error_response(404, "Project not found", f"Project with name {project} not found")
        

        db_tasks = Tasks.query.filter_by(project_id=db_project.id)
        if db_tasks == []:
            return create_error_response(404, "not found", f"no tasks for this project")

        db_member = Members.query.filter_by(name=member).first()
        if db_member == None:
            return create_error_response(404, "not found", f"member {member} not in database")

        for task in db_tasks:
            db_team = Teams.query.filter_by(task_id=task.id, member_id=db_member.id).first()
            if db_team != None:
                db.session.delete(db_team)
                db.session.commit()
                return Response(status=204)
        return create_error_response(404, "not found", f"member {member} not in project {project}")

class TaskMembers(Resource):
    def get(self, project, phase, task):
        db_task = Tasks.query.filter_by(name=task).first()
        if db_task == None:
            return create_error_response(404, "Task not found", f"Task with name {task} not found")

        body = MemberBuilder()
        body.add_namespace("promana", LINK_RELATIONS_URL)
        body.add_control("self", api.url_for(TaskMembers, project=project, phase=phase, task=task))
        body.add_control("up", f"/api/projects/{project}/phases/{phase}/tasks/{task}/")
        body.add_control_delete_member("member", project=project, phase=phase, task=task)
        body.add_control_add_member(project=project, phase=phase, task=task)
        body["items"] = []

        db_teams = Teams.query.filter_by(task_id=db_task.id)
        for team in db_teams:
            member = team.team_members
            try:
                if member.name not in body["items"]:
                    item = MemberBuilder(name=member.name)
                    item.add_control("self", api.url_for(TaskMemberItem, project=project, phase=phase, task=task, member=member.name))
                    body["items"].append(item)
            except AttributeError:
                return create_error_response(404, "not found", "user not found")

        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self, project, phase, task):
        if not request.json:
            return create_error_response(415, "Unsupported media type",
                "Requests must be JSON"
            )
        try:
            validate(request.json, MemberBuilder.member_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))
        # add new member to task
        db_member = Members.query.filter_by(name=request.json["name"]).first()
        db_task = Tasks.query.filter_by(name=task).first()

        if db_member == None:
            return create_error_response(404, "not found", f"member {request.json['name']} not in database")
        if db_task == None:
            return create_error_response(404, "Task not found", f"Task with name {task} not found")
        
        db_team = Teams.query.filter_by(task_id=db_task.id, member_id=db_member.id).first()
        if db_team != None:
            return create_error_response(409, "Already exists", 
                "Member already in task '{}'.".format(task)
            )
        new_team = Teams(team_tasks=db_task,
                         team_members=db_member)

        try:
            db.session.add(new_team)
            db.session.commit()
        except IntegrityError:
            return create_error_response(409, "Already exists", 
                "Member already in task '{}'.".format(task)
            )
        return Response(status=201, headers={"location": api.url_for(TaskMemberItem, project=project, phase=phase, task=task, member=db_member.name)})


class TaskMemberItem(Resource):
    def delete(self, project, phase, task, member):
        db_task = Tasks.query.filter_by(name=task).first()
        db_member = Members.query.filter_by(name=member).first()
        if db_member == None:
            return create_error_response(404, "not found", f"member {member} not in database")
        if db_task == None:
            return create_error_response(404, "Task not found", f"Task with name {task} not found")

        db_team = Teams.query.filter_by(task_id=db_task.id, member_id=db_member.id).first()
        if db_team == None:
            return create_error_response(404, "not found", f"member {member} not in project {project}")
        else:
            db.session.delete(db_team)
            db.session.commit()
        
        return Response(status=204)


api.add_resource(ProjectCollection, "/api/projects/")
api.add_resource(ProjectItem, "/api/projects/<project>/")
api.add_resource(MemberCollection, "/api/members/")
api.add_resource(MemberItem, "/api/members/<member>/")
api.add_resource(ProjectMembers, "/api/projects/<project>/members/")
api.add_resource(ProjectMemberItem, "/api/projects/<project>/members/<member>/")
api.add_resource(TaskMembers, "/api/projects/<project>/phases/<phase>/tasks/<task>/members/")
api.add_resource(TaskMemberItem, "/api/projects/<project>/phases/<phase>/tasks/<task>/members/<member>/")

@app.route(LINK_RELATIONS_URL)
def send_link_relations():
    return "link relations"

@app.route("/admin/")
def admin_site():
    return app.send_static_file("html/admin.html")
