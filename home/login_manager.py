# 2 Classes : "User" and "FlaskUserManagement" (to support flask_login)

from typing import Union
from brainannex import UserManager



class User():
    """
    Class needed by Flask.

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
        # (and that's the ONLY type of user login we're using)
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False



    def __str__(self) -> str:
        """
        :return:    A string with a brief description of this object
        """
        return f"<User Object - ID: {self.user_id} , username: `{self.username}`>"



    def get_id(self) -> str:
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


class FlaskUserManagement:
    """
    Class for User Management for Flask logins.
    All interaction with the database goes thru the class UserManager

    This is a STATIC class that doesn't get initialized.
    """

    user_dict = {}      # Dictionary of "User" objects, indexed by the user ID (an integer value)
                        # This is used as a "local lookup table" for user info



    @classmethod
    def show_users(cls) -> None:
        """
        Print out a list of users stored in the local lookup table
        (implemented with the dict kept in the class property user_dict).  Meant for debugging

        :return:    None
        """
        print("show_users(): list of users in UserManagerNeo4j:")
        for k, v in cls.user_dict.items():
            print(f"    ({k}): {str(v)}")



    @classmethod
    def fetch_user_obj(cls, user_id: int) -> Union[User, None]:
        """
        Attempt to locate the user, specified by the given ID, in local lookup table.
        If found, return its "User" object; otherwise, return None

        :param user_id:     An integer that is meant to identify a particular user
        :return:            Object of type "User", if the specified user was found in the local lookup table;
                                otherwise, None
        """
        # Attempt to locate the requested user in the local lookup table, which
        #   is implemented in the form of the dictionary:  cls.user_dict
        return cls.user_dict.get(user_id, None)    # None is returned if the dictionary lookup fails



    @classmethod
    def prepare_user_obj(cls, user_id: int, username = "") -> User:
        """
        Attempt to locate the user, specified by the given ID (or by the given username), in the local lookup table;
        if not found, create an object of type "User", with the passed user ID and username

        :param user_id:     An integer identifying a particular user
        :param username:    A string containing the username - needed if the specified user ID wasn't found
        :return:            Object of type "User"
        """

        # Look up, in local lookup table, the User object corresponding to the specified user ID
        user_obj  = cls.fetch_user_obj(user_id)     # If not found, None will be returned

        if user_obj is not None:    # The requested "User" object was found
            print("Re-using an existing 'User' object, for User ID: ", user_id)
        else:                       # The requested "User" object was NOT found
            user_obj = cls.create_user_obj(user_id, username)    # Create a "User" object, as needed by flask_login
            print(f"Creating a new 'User' object, for User ID: {user_id} (username {username})")

        return  user_obj



    @classmethod
    def obtain_user_obj(cls, user_id: int, cache_users=True) -> Union[User, None]:
        """
        Attempt to locate the user in the local lookup table;
        if not found, consult the database to create (if present there) an object of type "User"
        based on the given user ID.
        If unable to locate the given user ID, either locally or in the database, return None

        This method is needed by a callback function - implemented in HomeRouting.load_user() - required
        by the "flask_login" package.

        NOTE on user-login caching:
                While fast and convenient, it also means that there's no way to administratively
                force a user out of login by making changes in the database - the app would also require a restart.
                (Maybe an "inactivate_user" API could be implemented, to knock off the user from the local table;
                 however, such an approach wouldn't work if there are multiple instances of the web app - for example,
                 multiple worker threads or multiple VM's for load-balancing.
                 A better remediation might be by means of a Time-To-Live, sketched below, commented out; if a certain
                 amount of time has elapsed from the last database check, consult the database again)

        :param user_id:     An integer that is meant to identify a particular user
        :param cache_users: If True (default), user-login caching is used.  See not above
        :return:            Object of type "User", if the specified user was found in the local lookup table or in the database;
                                otherwise, None
        """

        if cache_users:
            # Attempt to locate the user in the local lookup table
            # (see the NOTE, above, about possible consequence of this login caching;
            #  below, commented out, is a draft of a possible remedy based on a Time-To-Live)
            '''
            # Assume two class variables, cls.last_checked and cls.time_to_live    
            if cls.last_checked is None:
                cls.last_checked = datetime.now()   # Checking for the 1st time
            elif time_difference(datetime.now(), cls.last_checked) < cls.time_to_live:  # If this hold, we'll use the cached copy
                # Here place the next few lines, to locate the user in the local lookup table
            '''
            user_obj  = cls.fetch_user_obj(user_id) # Attempt to locate the user in the local lookup table

            if user_obj is not None:    # The requested "User" object was found
                #print("obtain_user_obj(): Re-using an existing 'User' object, for User ID: ", user_id)
                return  user_obj


        # The requested "User" object was NOT found in the local lookup table; attempt instead to retrieve it from the database

        username = UserManager.get_username(user_id)


        if username is None:
            return None         # Not found
        """ 
        # Query the database.   TODO: being moved to UserManager class
        #print(f"obtain_user_obj(): querying the dbase for node labeled `User Login`, "
              #f"with attribute `user_id` having a value of `{user_id}`")
        result_dict = cls.db.get_record_by_primary_key(labels="User Login",
                                                       primary_key_name="user_id", primary_key_value=user_id)
        if (result_dict is None) or ("username" not in result_dict):
            #print("obtain_user_obj(): node not found in the database, or missing an attribute `username`")
            return None     # Not found

        username = result_dict["username"]
        """

        user_obj = cls.create_user_obj(user_id, username)    # Create a "User" object, as needed by flask_login
        #print(f"obtain_user_obj(): Creating a new 'User' object from database data, "
              #f"for User ID: {user_id} , username {username}")

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
