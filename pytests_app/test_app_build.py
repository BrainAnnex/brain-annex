import pytest
import app_build
import os
from brainannex import GraphAccess, GraphSchema
from app_libraries.media_manager import MediaManager


def test_create_app():

    db = GraphAccess(debug=False)

    app = app_build.create_app(db=db, test=True)

    assert app.config['DB_COUNT'] == 1
    assert app.config['PORT_NUMBER'] == 5000
    assert app.config['DATABASE'] == db
    assert GraphSchema.db == db


    app2 = app_build.create_app(db=db, test=False)

    assert app2.config['DB_COUNT'] == 2  # Set in the test config files


    # Use the credentials stored in PyCharm (on the dev computer) for unit testing
    host = os.getenv("NEO4J_HOST")
    user = os.getenv("NEO4J_USER")
    passwd = os.getenv("NEO4J_PASSWORD")
    override={'DB_DEFAULT_INDEX': 1, 'DB_HOST_1': host, 'DB_USERNAME_1': user, 'DB_PASSWORD_1': passwd,
              'MEDIA_FOLDER': 'my_test/'}

    app3 = app_build.create_app(test=True, config_override=override)
    assert app3.config['DB_HOST_1'] == host
    assert app3.config['MEDIA_FOLDER'] == 'my_test/'
    new_db = app3.config['DATABASE']
    new_db.test_dbase_connection()
    assert GraphSchema.db == new_db
    assert MediaManager.MEDIA_FOLDER == 'my_test/'
