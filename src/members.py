from flask import Flask, Response, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_restful import Resource
from flask_restful import Api
from utils import MasonBuilder, LINK_RELATIONS_URI

app = Flask(__name__)
api = Api(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Members(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)

    # managed_project = db.relationship("Project", cascade="delete-orphan", back_populates="project_manager")
    managed_project = db.relationship("Project", back_populates="project_manager")
    membership = db.relationship("Teams", back_populates="team_members")

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

        body = MemberBuilder()
        body.add_namespace("promana", LINK_RELATIONS_URI)
        body.add_control("self", api.url_for(MemberCollection))
        body.add_control_add_member()
        body["items"] = []

        for member in db_members:
            item = MemberBuilder(
                name=member.name)
            item.add_control("self", api.url_for(MemberItem, id=member.id))
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

        return Response(status=201, headers={"location": api.url_for(MemberItem, id=new_member.id)})

class MemberItem(Resource):
    #get member
    def get(self, id):
        db_member = Members.query.filter_by(id=id).first()
        body = MemberBuilder(
            name=db_member.name)
        body.add_namespace("promana", LINK_RELATIONS_URI)
        body.add_control("self", api.url_for(MemberItem, id=id))
        body.add_control("collection", api_url_for(MemberCollection))
        body.add_control_edit_member(id)
        body.add_control_delete_member(id)

    #edit member
    def patch(self, id):
        db_member = Members.query.filter_by(id=id).first()
        db_member.name = request.json["name"]

        try:
            db.session.commit()
        except IntegrityError:
            return 409

        return Response(status=204)

    # delete member
    def delete(self, id):
        db_member = Members.query.filter_by(id=id).first()
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