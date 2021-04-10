from flask import Flask, Response, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_restful import Resource
from flask_restful import Api
from utils import MasonBuilder, LINK_RELATIONS_URI
from models import *
import datetime
import enum
import json

app = Flask(__name__)
api = Api(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class ProjectBuilder(MasonBuilder):
    @staticmethod
    def project_schema():
        schema = {
            "type": "object",
            "required": ["name", "project_manager"]
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
            "href": "/api/members/{manager}"
            }
        props["status"] = {
            "description": "Status of the project",
            "type": "string",
            "enum": ["NOT_STARTED", "STARTED", "FINISHED"]
            }
        return schema

    def add_control_add_project(self):
        self.add_control(
            "promana:add-project",
            "/api/projects/",
            method="POST",
            encoding="json",
            title="Add new project",
            schema=self.project_schema()
         )

    def add_control_edit_project(self, project):
        self.add_control(
            "edit",
            f"/api/projects/{project}",
            method="PUT",
            encoding="json",
            title="Edit project",
            schema=self.project_schema()
        )

    def add_control_project_members(self, project):
        self.add_control(
            "promana:project-members",
            f"/api/projects/{project}/members"
        )

    def add_control_project_phase(self, project):
        self.add_control(
            "promana:project-phase",
            f"/api/projects/{project}/phase"
        )
    
    def add_control_delete_project(self, project):
        self.add_control(
            "promana:delete",
             f"/api/projects/{project}",
             method="DELETE"
        )

class ProjectCollection(Resource):
    def get(self):
        # get all projects
        db_projects = Project.query.all()

        if db_projects == None:
            return Response(status=501)

        body = ProjectBuilder()
        body.add_namespace("promana", LINK_RELATIONS_URI)
        body.add_control("self", api.url_for(ProjectCollection))
        body.add_control_add_project()
        body["items"] = []

        for project in db_projects:
            item = ProjectBuilder(
                name=project.name,
                start=project.start,
                end=project.end,
                project_manager=project.project_manager,
                status=project.status
                )
            item.add_control("self", api.url_for(ProjectItem, project=project.name))
            body["items"].append(item)

        return Response(json.dumps(body), 200)

    def post(self):
        # add new project
        new_project = Project(
            name=request.json["name"],
            start=request.json["start"],
            end=request.json["end"],
            project_manager=request.json["project_manager"],
            status=status_type[request.json["status"]]
            )
        
        try:
            db.session.add(new_project)
            db.session.commit()
        except IntegrityError:
            return 409

        return Response(status=201, headers={"location": api.url_for(ProjectItem, project=new_project.name)})


class ProjectItem(Resource):
    #get project
    def get(self, project):
        db_project = Project.query.filter_by(name=project).first()
        body = ProjectBuilder(
            name=db_project.name)
        body.add_namespace("promana", LINK_RELATIONS_URI)
        body.add_control("self", api.url_for(ProjectItem, project=project))
        body.add_control("collection", api.url_for(ProjectCollection))
        body.add_control_edit_project(project)
        body.add_control_delete_project(project)

        return Response(json.dumps(body), 200)

    #edit project
    def put(self, project):
        db_project = Project.query.filter_by(name=project).first()
        db_project.name = request.json["name"]

        try:
            db.session.commit()
        except IntegrityError:
            return 409

        return Response(status=204, headers={"location":api.url_for(ProjectItem, project=db_project.name)})

    # delete member
    def delete(self, project):
        db_project = Project.query.filter_by(name=project).first()
        db.session.delete(db_project)
        db.session.commit()
        
        return Response(status=204)

api.add_resource(ProjectCollection, "/api/projects/")
api.add_resource(ProjectItem, "/api/projects/<project>/")
