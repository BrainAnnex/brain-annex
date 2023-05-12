# 2 Classes : "User" and "user_manager_neo4j"
from typing import Union


class User():
    """
    The "flask_login" package used for authentication
    expects user objects that have the following 3 properties and 1 method:

        is_authenticated
        is_active
        is_anonymous

        get_id()
    """

    def __init__(self, user_id: int, username = ""):
        self.user_id = user_id      # Integer user ID
        self.username = username

        # Properties required by Flask-Login
        # By default, we're instantiating authenticated, active, non-anonymous users
        # (that's the ONLY type of user login we're using)
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False



    def __str__(self) -> str:
        """
        :return:    A string with a brief description of this object
        """
        return f"<User Object - ID: {self.user_id} , username: `{self.username}`>"



    def get_id(self):
        """
        Method required by the "flask_login" package.

        From the docs:
        "This method must return a unicode that uniquely identifies this user,
        and can be used to load the user from the user_loader callback.
        Note that this must be a unicode - if the ID is natively an int or some other type,
        you will need to convert it to unicode."

        :return:    A Unicode string
        """

        return chr(self.user_id)    # TODO: ought to make sure that user_id doesn't exceed the max for a 1-character Unicode string
                                    #       however, all good as long as value doesn't exceed 1,114,111

        #return self.user_id        # In my test, this also worked if load_user is modified to expect an int




##################################################################################################################################


class UserManagerNeo4j:
    """
    Class for User Management (Neo4j version)

    This is a STATIC class that doesn't get initialized.
    IMPORTANT: prior to use, its class variable "db" must be set
    """

    db = None           # "NeoAccess" object.  MUST be set before using this class!

    user_dict = {}      # Dictionary of "User" objects, indexed by the user ID (an integer value)



    @classmethod
    def show_users(cls) -> None:
        """
        Show a list of users stored in the local lookup table
        (implemented with the dict kept in the class property user_dict).  Meant for debugging

        :return:    None
        """
        print("show_users(): list of users in UserManagerNeo4j:")
        for k, v in cls.user_dict.items():
            print(f"    ({k}): {str(v)}")



    @classmethod
    def fetch_user_obj(cls, user_id: int) -> Union[User, None]:
        """
        Look up and return the "User" object corresponding to the specified user ID; if not found, return None

        :param user_id:     An integer that is meant to identify a particular user
        :return:            Object of type "User", if the specified user was found in the local lookup table;
                                otherwise, None
        """
        # Attempt to locate the requested user in the local lookup table, which
        # is implemented in the form of the dictionary:  cls.user_dict
        return cls.user_dict.get(user_id, None)    # None is returned if the dictionary lookup fails



    @classmethod
    def obtain_user_obj(cls, user_id: int) -> Union[User, None]:
        """
        Attempt to locate the user in local lookup table;
        if not found, consult the database to create (if present there) an object of type "User"
        based on the given user ID.
        If unable to locate the given user ID, either locally or in the database, return None

        NOTE:   this is a form of user-login caching.  While fast and convenient, it also means that
                there's no way to kick a user out from changes in the database (the app would also require a restart)
                (Maybe an "inactivate_user" API could be implemented, to knock off the user from the local table;
                 however, such an approach wouldn't work if there are multiple instances of the web app - for example,
                 multiple workers or multiple VM's for load-balancing)

        :param user_id:     An integer that is meant to identify a particular user
        :return:            Object of type "User", if the specified user was found in the local lookup table or in the database;
                                otherwise, None
        """

        # First, attempt to locate the user in the local lookup table
        # (see the NOTE, above, about possible consequence of this login caching)
        user_obj  = cls.fetch_user_obj(user_id)

        if user_obj is not None:    # The requested "User" object was found
            print("obtain_user_obj(): Re-using an existing 'User' object, for User ID: ", user_id)
            return  user_obj


        # The requested "User" object was NOT found in the local lookup table; now attempt to retrieve it from the database

        # Query the database
        print(f"obtain_user_obj(): querying the dbase for node labeled `User Login`, "
              f"with attribute `user_id` having a value of `{user_id}`")
        result_dict = cls.db.get_record_by_primary_key(labels="User Login",
                                                        primary_key_name="user_id", primary_key_value=user_id)
        if (result_dict is None) or ("username" not in result_dict):
            print("obtain_user_obj(): node not found in the database, or missing an attribute `username`")
            return None     # Not found

        username = result_dict["username"]

        user_obj = cls.create_user_obj(user_id, username)    # Create a "User" object, as needed by flask_login
        print(f"obtain_user_obj(): Creating a new 'User' object from database data, "
              f"for User ID: {user_id} , username {username}")

        return  user_obj



    @classmethod
    def prepare_user_obj(cls, user_id: int, username = "") -> User:
        """
        Look up or, if not found, create an object of type "User"

        :param user_id:     An integer identifying a particular user
        :param username:    A string containing the username - needed if the specified user ID wasn't found
        :return:            Object of type "User"
        """

        # Look up and return the User object corresponding to the specified user ID; if not found, return None
        user_obj  = cls.fetch_user_obj(user_id)

        if user_obj is not None:    # The requested "User" object was found
            print("Re-using an existing 'User' object, for User ID: ", user_id)
        else:                       # The requested "User" object was NOT found
            user_obj = cls.create_user_obj(user_id, username)    # Create a "User" object, as needed by flask_login
            print(f"Creating a new 'User' object, for User ID: {user_id} (username {username})")

        return  user_obj



    @classmethod
    def create_user_obj(cls, user_id: int, username = "") -> User:
        """
        Create a new "User" object,
        and add it to a running listing of them, indexed by the user ID.
        Return the newly-created object

        :param user_id:     An integer identifying a particular user
        :param username:    A string containing the username
        :return:            Object of type "User"
        """
        user_obj = User(user_id, username)      # Instantiate a new "User" object

        # Save the newly-created "User" object,
        # by adding it to a dict of other such objects, indexed by the user ID
        cls.user_dict[user_id] = user_obj

        return user_obj



    @classmethod
    def check_login_credentials(cls, username: str, password: str) -> int:
        """
        Verify the validity of the specified password for the given username,
        by consulting the database.
        If successful, return the User ID; otherwise, return -1

        TODO: introduce encryption in the passwords stored in the database

        :param username:    A string with the username
        :param password:    A string with the password
        :return:            If the login credentials are valid, return an integer with the User ID; otherwise, return -1
        """

        # Query the database to get back a list of values for User ID's (ideally, exactly 1)
        credentials = {"username": username, "password": password}
        match = cls.db.match(labels="User Login", properties=credentials)
        result_list = cls.db.get_single_field(match=match, field_name="user_id")

        print("In check_login_credentials(). List of matching User ID's:", result_list)

        if len(result_list) == 1:
            user_id = result_list[0]
            print("check_login_credentials(): successful validation of user credentials. User ID: ", user_id)
            return user_id      # Successful login
        else:
            print("check_login_credentials(): failed validation of user credentials. No matches or more than one")
            print(f"Credentials used in database query: {credentials}")
            return -1           # Unsuccessful login
