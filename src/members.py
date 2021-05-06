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
                         f"/api/members/{member}",
                         method="PATCH",
                         encoding="json",
                         title="Edit member",
                         schema=self.member_schema())
    
    def add_control_up_project(self, project):
        self.add_control("up",
                         f"/api/projects/{project}/members")
    
    def add_control_up_task(self, project, phase, task):
        self.add_control("up",
                         f"/api/projects/{project}/phases/{phase}/tasks/{task}/members")
    
    def add_control_delete_member(self, member, project=None, phase=None, task=None):
        if project == None:
            self.add_control("promana:delete",
                             f"/api/members/{member}",
                             method="DELETE")
        elif task == None:
            self.add_control("promana:delete",
                             f"/api/projects/{project}/members/{member}",
                             method="DELETE")
        else:
            self.add_control("promana:delete",
                             f"/api/projects/{project}/phases/{phase}/tasks/{task}/members/{member}",
                             method="DELETE")

class MemberCollection(Resource):
    def get(self):
        # get all members
        db_members = Members.query.all()

        if db_members == None:
            return Response(status=501)

        body = MemberBuilder()
        body.add_namespace("promana", LINK_RELATIONS_URI)
        body.add_control("self", api.url_for(MemberCollection))
        body.add_control_add_member()
        body["items"] = []

        for member in db_members:
            item = MemberBuilder(
                name=member.name)
            item.add_control("self", api.url_for(MemberItem, member=member.name))
            body["items"].append(item)

        return Response(json.dumps(body), 200)

    def post(self):
        # add new member
        new_member = Members(
            name=request.json["name"])
        
        try:
            db.session.add(new_member)
            db.session.commit()
        except IntegrityError:
            return 409

        return Response(status=201, headers={"location": api.url_for(MemberItem, member=new_member.name)})

class MemberItem(Resource):
    #get member
    def get(self, member):
        db_member = Members.query.filter_by(name=member).first()
        body = MemberBuilder(
            name=db_member.name)
        body.add_namespace("promana", LINK_RELATIONS_URI)
        body.add_control("self", api.url_for(MemberItem, member=member))
        body.add_control("collection", api.url_for(MemberCollection))
        body.add_control_edit_member(member)
        body.add_control_delete_member(member)

        return Response(json.dumps(body), 200)

    #edit member
    def patch(self, member):
        db_member = Members.query.filter_by(name=member).first()
        db_member.name = request.json["name"]

        try:
            db.session.commit()
        except IntegrityError:
            return 409

        return Response(status=204, headers={"location":api.url_for(MemberItem, member=db_member.name)})

    # delete member
    def delete(self, member):
        db_member = Members.query.filter_by(name=member).first()
        db.session.delete(db_member)
        db.session.commit()
        
        return Response(status=204)

class ProjectMemberCollection(Resource):
    def get(self):
        # get all members from project
        pass
    def post(self):
        # add new member to project
        pass
    def delete(self):
        # delete member from project
        pass

class TaskMemberCollection(Resource):
    def get(self):
        # get all members from task
        pass
    def post(self):
        # add new member to task
        pass
    def delete(self):
        # delete member from task
        pass


api.add_resource(MemberCollection, "/api/members/")
api.add_resource(MemberItem, "/api/members/<member>/")