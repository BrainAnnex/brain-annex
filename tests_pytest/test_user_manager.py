import pytest
from neoaccess import NeoAccess
from brainannex.neo_schema.neo_schema import NeoSchema
from brainannex.user_manager import UserManager



# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = NeoAccess(debug=False)
    neo_obj.empty_dbase()
    NeoSchema.set_database(neo_obj)
    UserManager.set_database(neo_obj)
    UserManager.create_schema()

    yield neo_obj



def clear_users(db):
    # Clear out all the Users registered in the database
    db.delete_nodes_by_label(delete_labels="User")




# ************************************************************************************************************
def test_create_schema(db):
    pass



def test_create_user(db):
    clear_users(db)

    with pytest.raises(Exception):
        UserManager.create_user(username="", password="top_secret!!", email="me@you.com", admin=True)

    with pytest.raises(Exception):
        UserManager.create_user(username=123, password="top_secret!!", email="me@you.com", admin=True)

    with pytest.raises(Exception):      # Password too short
        UserManager.create_user(username="julian", password="1234567", email="me@you.com", admin=True)

    with pytest.raises(Exception):
        UserManager.create_user(username="julian", password="top_secret!!", email=666, admin=True)


    user_id = UserManager.create_user(username="julian", password="top_secret!!", email="me@you.com", admin=True)

    q = '''
        MATCH (:CLASS {name:"User"})<-[:SCHEMA]-(u :User {user_id: $user_id, username: $username, email: $email, admin: $admin}) 
        RETURN count(u) AS number_users
        '''
    result = db.query(q, data_binding={"user_id": user_id, "username": "julian", "email": "me@you.com", "admin": True},
                         single_cell="number_users")
    assert result == 1

    with pytest.raises(Exception):      # Attempting to create a 2nd user with the same username
        UserManager.create_user(username="julian", password="another_pass", email="", admin=False)


    user_id = UserManager.create_user(username="einstein", password="e=mc^2", email="", admin=False, min_pass_len=6)

    q = '''
        MATCH (:CLASS {name:"User"})<-[:SCHEMA]-(u :User {user_id: $user_id, username: $username, admin: $admin}) 
        RETURN count(u) AS number_users
        '''
    result = db.query(q, data_binding={"user_id": user_id, "username": "einstein", "admin": False},
                      single_cell="number_users")
    assert result == 1



def test_create_hashed_password(db):
    clear_users(db)

    passwd = UserManager.create_hashed_password("top_secret!!")
    assert len(passwd) == 60
    assert type(passwd) == bytes



def test_check_password(db):
    clear_users(db)

    hashed_password = UserManager.create_hashed_password("top_secret!!")

    assert UserManager.check_password(provided_password="top_secret!!", hashed_password=hashed_password)



def test_get_username(db):
    clear_users(db)

    assert UserManager.get_username(123) is None            # No users in dbase yet

    user_id = UserManager.create_user(username="julian", password="top_secret!!", email="me@you.com", admin=True)
    assert UserManager.get_username(user_id) == "julian"
    assert UserManager.get_username(user_id+1) is None      # No such user in dbase

    user_id = UserManager.create_user(username="einstein", password="e=mc^2", email="albert@princeton.edu",
                                      admin=False, min_pass_len=6)
    assert UserManager.get_username(user_id) == "einstein"
    assert UserManager.get_username("Not an integer") is None



def test_check_login_credentials(db):
    clear_users(db)

    assert UserManager.check_login_credentials(username="ghost", password="666") is None    # No users in dbase yet

    user_id_1 = UserManager.create_user(username="julian", password="top_secret!!", email="me@you.com", admin=True)
    assert UserManager.check_login_credentials(username="julian", password="top_secret!!") == user_id_1
    assert UserManager.check_login_credentials(username="julian", password="bad_pass") is None
    assert UserManager.check_login_credentials(username="julian_twin", password="top_secret!!") is None  # No such user

    user_id_2 = UserManager.create_user(username="einstein", password="e=mc^2", email="albert@princeton.edu",
                                      admin=False, min_pass_len=6)
    assert UserManager.check_login_credentials(username="einstein", password="e=mc^2") == user_id_2
    assert UserManager.check_login_credentials(username="einstein", password="spooky_action") is None
    assert UserManager.check_login_credentials(username="einstein", password="top_secret!!") is None

    assert UserManager.check_login_credentials(username="julian", password="top_secret!!") == user_id_1 # Still works
    assert UserManager.check_login_credentials(username="einstein", password="top_secret!!") is None    # Other user's password
    assert UserManager.check_login_credentials(username="julian", password="e=mc^2") is None    # Other user's password



def test_authenticate_user(db):
    clear_users(db)

    assert not UserManager.authenticate_user(username="ghost", password="666")    # No users in dbase yet

    UserManager.create_user(username="julian", password="top_secret!!", email="me@you.com", admin=True)
    assert UserManager.authenticate_user(username="julian", password="top_secret!!")
    assert not UserManager.authenticate_user(username="julian", password="bad_pass")
    assert not UserManager.authenticate_user(username="julian_twin", password="top_secret!!")   # No such user

    UserManager.create_user(username="einstein", password="e=mc^2", email="albert@princeton.edu",
                            admin=False, min_pass_len=6)
    assert UserManager.authenticate_user(username="einstein", password="e=mc^2")
    assert not UserManager.authenticate_user(username="einstein", password="spooky_action")
    assert not UserManager.authenticate_user(username="einstein", password="top_secret!!")

    assert UserManager.authenticate_user(username="julian", password="top_secret!!")            # Still works
    assert not UserManager.authenticate_user(username="einstein", password="top_secret!!")      # Other user's password
    assert not UserManager.check_login_credentials(username="julian", password="e=mc^2")        # Other user's password
