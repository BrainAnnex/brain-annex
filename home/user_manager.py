# Classes "User" and "user_manager_neo4j"
from typing import Union


class User():
    """
    The "flask_login" package used for authentication
    expects user objects that have the following properties and methods:

        is_authenticated
        is_active
        is_anonymous
        get_id()
    """

    def __init__(self, user_id: int, username = ""):
        self.user_id = user_id      # Integer user ID
        self.username = username

        # Properties required by Flask-Login
        # By default, we're instantiating authenticate, active, non-anonymous users
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

    This class does NOT get instantiated.
    """

    db = None           # "NeoAccess" object.  MUST be set before using this class!

    user_dict = {}      # Dictionary of "User" objects, indexed by the user ID (an integer value)



    @classmethod
    def show_users(cls) -> None:
        """
        Show a list of users added to the class' user_dict property.  Meant for debugging

        :return:    None
        """
        print("List of users in UserManagerNeo4j:")
        for k, v in cls.user_dict.items():
            print(f"    ({k}): {str(v)}")



    @classmethod
    def fetch_user_obj(cls, user_id: int) -> Union[User, None]:
        """
        Look up and return the "User" object corresponding to the specified user ID; if not found, return None

        :param user_id:     An integer identifying a particular user
        :return:            A "User" object, if the specified user was found; otherwise, None
        """
        return cls.user_dict.get(user_id, None)    # None is returned if the dictionary lookup fails



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

        :param user_id:     An integer identifying a particular user
        :param username:    A string containing the username
        :return:            Object of type "User"
        """
        user_obj = User(user_id, username)      # Instantiate a new "User" object
        cls.set_user_obj(user_id, user_obj)     # Add the newly-created "User" object to their complete listing
        return user_obj



    @classmethod
    def set_user_obj(cls, user_id: int, user_obj) -> None:
        """
        Add a "User" object to a listing of them, indexed by the user ID

        :param user_id:     An integer identifying a particular user
        :param user_obj:    Object of type "User"
        :return:            None
        """
        cls.user_dict[user_id] = user_obj



    @classmethod
    def check_login_credentials(cls, username: str, password: str) -> int:
        """
        Verify the validity of the specified password for the given username.
        If successful, return the User ID; otherwise, return -1

        :param username:    A string with the username
        :param password:    A string with the password
        :return:            If the login credentials are valid, return an integer with the User ID; otherwise, return -1
        """

        # Query the database to get back a list of values for User ID's (ideally, exactly 1)
        credentials = {"username": username, "password": password}
        match = cls.db.find(labels="User Login", properties=credentials)
        result_list = cls.db.get_single_field(match=match, field_name="user_id")

        print("In check_login_credentials(). List of matching User ID's:", result_list)

        if len(result_list) == 1:
            user_id = result_list[0]
            print("In check_login_credentials(): successful validation of user credentials. User ID: ", user_id)
            return user_id
        else:
            print("In check_login_credentials(): failed validation of user credentials. No matches or more than one")
            print(f"Credentials used in database query: {credentials}")
            return -1           # Unsuccessful login
