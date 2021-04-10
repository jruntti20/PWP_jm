import json
import os
import pytest
import tempfile
import time
from datetime import datetime
from jsonschema import validate
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, StatementError

from app import app, db
from models import *


@pytest.fixture
def client():
    db_fd, db_fname = tempfile.mkstemp()
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_fname
    app.config["TESTING"] = True

    db.create_all()
    _populate_db()

    yield app.test_client()

    db.session.remove()
    os.close(db_fd)
    os.unlink(db_fname)

def _populate_db():
    pr = Project(name="projekti1",
                status=status_type.NOT_STARTED)
    pr2 = Project(name="projekti2",
                  status=status_type.NOT_STARTED)
    ph = Phase(name="phase1",
               status=status_type.NOT_STARTED)
    ph2 = Phase(name="phase2",
               status=status_type.NOT_STARTED)
    ta = Tasks(name="task1",
               project=pr,
               phase=ph,
              status=status_type.NOT_STARTED)
    ta2 = Tasks(name="task2",
                project=pr2,
                phase=ph2,
                status=status_type.NOT_STARTED)
    ta3 = Tasks(name="task3",
                project=pr,
                phase=ph,
                status=status_type.NOT_STARTED)
    for i in range(1, 4):
        m = Members(
            name="test-member-{}".format(i)
        )
        db.session.add(m)
        te = Teams(team_tasks=ta,
                    team_members=m)
        db.session.add(te)

    m=Members(
        name="test-member-4")
    db.session.add(m)
    te = Teams(team_tasks=ta2,
               team_members=m)
    db.session.add(te)

    db.session.add(pr)
    db.session.add(pr2)
    db.session.add(ph)
    db.session.add(ph2)
    db.session.add(ta)
    db.session.add(ta2)
    db.session.add(ta3)
    db.session.commit()

def _get_member_json(number=1):    
    return {"name": f"extra-member-{number}"}

def _check_namespace(client, response):
    namespace = response["@namespaces"]["promana"]["name"]
    resp = client.get(namespace)
    assert resp.status_code == 200

class TestMemberCollection(object):

    RESOURCE_URL = "/api/members/"

    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert len(body["items"]) == 4
        for item in body["items"]:
            assert "name" in item

    def test_post(self, client):
        valid = _get_member_json()
        
        # test with wrong content type
        resp = client.post(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        
        # test with valid and see that it exists afterward
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        assert resp.headers["Location"].endswith(self.RESOURCE_URL + valid["name"] + "/")
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["name"] == "extra-member-1"
        
        # send same data again for 409
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409

        # send with invalid schema
        invalid = {"n": "member"}
        resp = client.post(self.RESOURCE_URL, json=invalid)
        assert resp.status_code == 400

class TestMemberItem(object):

    RESOURCE_URL = "/api/members/test-member-1/"
    INVALID_URL = "/api/members/non-member-x/"
    MODIFIED_URL = "/api/members/extra-member-1/"

    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["name"] == "test-member-1"
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_patch(self, client):       
        valid = _get_member_json()
        
        # test with wrong content type
        resp = client.patch(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        
        resp = client.patch(self.INVALID_URL, json=valid)
        assert resp.status_code == 404
        
        # test with another member's name
        valid["name"] = "test-member-2"
        resp = client.patch(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409
        
        # test with valid
        valid["name"] = "test-member-1"
        resp = client.patch(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 204
        
        # send with invalid schema
        invalid = {"n": "member"}
        resp = client.patch(self.RESOURCE_URL, json=invalid)
        assert resp.status_code == 400
        
        valid = _get_member_json()
        resp = client.patch(self.RESOURCE_URL, json=valid)
        resp = client.get(self.MODIFIED_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["name"] == valid["name"]
    
    def test_delete(self, client):
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 404
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404

class TestProjectMemberCollection(object):

    RESOURCE_URL = "/api/projects/projekti1/members/"

    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert len(body["items"]) == 3
        for item in body["items"]:
            assert "name" in item

class TestProjectMemberItem(object):
    RESOURCE_URL = "/api/projects/projekti1/members/test-member-1/"
    INVALID_URL = "/api/projects/projekti1/members/test-member-x/"
    INVALID_URL2 = "/api/projects/projekti1/members/test-member-4/"

    def test_delete(self, client):
        # delete existing member from project
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204
        # try to delete non-existing member frm project
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404
        # try to delete member that is not in the project
        resp = client.delete(self.INVALID_URL2)
        assert resp.status_code == 404

class TestTaskMemberCollection(object):

    RESOURCE_URL = "/api/projects/projekti1/phases/phase1/tasks/task1/members/"
    RESOURCE_URL2 = "/api/projects/projekti1/phases/phase1/tasks/task3/members/"

    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert len(body["items"]) == 3
        for item in body["items"]:
            assert "name" in item

    def test_post(self, client):
        valid = {"name": "test-member-1"}
        
        # test with wrong content type
        resp = client.post(self.RESOURCE_URL2, data=json.dumps(valid))
        assert resp.status_code == 415
        
        # test with valid and see that it exists afterward
        resp = client.post(self.RESOURCE_URL2, json=valid)
        assert resp.status_code == 201
        assert resp.headers["Location"].endswith(self.RESOURCE_URL2 + valid["name"] + "/")
        
        # send same data again for 409
        resp = client.post(self.RESOURCE_URL2, json=valid)
        assert resp.status_code == 409

        # send with invalid schema
        invalid = {"n": "member"}
        resp = client.post(self.RESOURCE_URL2, json=invalid)
        assert resp.status_code == 400

class TestTaskMemberItem(object):
    RESOURCE_URL = "/api/projects/projekti1/phases/phase1/tasks/task1/members/test-member-2"
    INVALID_URL = "/api/projects/projekti1/phases/phase1/tasks/task1/members/test-member-x"
    INVALID_URL2 = "/api/projects/projekti2/phases/phase1/tasks/task1/members/test-member-4/"
    #not working
    def test_delete(self, client):
        # delete existing member from project
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204
        # try to delete non-existing member frm project
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404
        # try to delete member that is not in the project
        resp = client.delete(self.INVALID_URL2)
        assert resp.status_code == 404