import pytest
from brainannex.modules.utilities.comparisons import compare_unordered_lists, compare_recordsets
from neoaccess import NeoAccess
from brainannex.modules.neo_schema.neo_schema import NeoSchema
from brainannex.modules.user_manager.user_manager import UserManager



# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = NeoAccess(debug=False)
    NeoSchema.set_database(neo_obj)
    UserManager.set_database(neo_obj)

    yield neo_obj



# ************************************************************************************************************

def test_create_user(db):

    db.empty_dbase()

    with pytest.raises(Exception):
        UserManager.create_user(username="", password="top_secret!!", email="me@you.com", admin=True)

    with pytest.raises(Exception):
        UserManager.create_user(username=123, password="top_secret!!", email="me@you.com", admin=True)

    with pytest.raises(Exception):      # Password too short
        UserManager.create_user(username="julian", password="1234567", email="me@you.com", admin=True)

    with pytest.raises(Exception):
        UserManager.create_user(username="julian", password="top_secret!!", email="", admin=True)


    UserManager.create_user(username="julian", password="top_secret!!", email="me@you.com", admin=True)

    q = '''
        MATCH (:CLASS {name:"User"})<-[:SCHEMA]-(u :User {username: $username, email: $email, admin: $admin}) 
        RETURN count(u) AS number_users
        '''
    result = db.query(q, data_binding={"username": "julian", "email": "me@you.com", "admin": True},
                         single_cell="number_users")

    assert result == 1


    with pytest.raises(Exception):      # Attempting to create a 2nd user with the same username
        UserManager.create_user(username="julian", password="another_pass", email="me2@you.com", admin=False)



def test_create_hashed_password(db):
    passwd = UserManager.create_hashed_password("top_secret!!")
    assert len(passwd) == 60
    assert type(passwd) == bytes



def test_check_password(db):
    hashed_password = UserManager.create_hashed_password("top_secret!!")

    assert UserManager.check_password(provided_password="top_secret!!", hashed_password=hashed_password)
