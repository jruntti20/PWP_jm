import os
import pytest
import tempfile

import database_gen

@pytest.fixture
def db_handle():
    db_fd, db_fname = tempfile.mkstemp()
    database_gen.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_fname
    database_gen.app.config["TESTING"] = True

    with database_gen.app.app_context():
        database_gen.db.create_all()

    yield app.db

    database_gen.db.session.remove()
    os.close(db_fd)
    os.unlink(db_fname)
