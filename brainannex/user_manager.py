import bcrypt                       # For password encryption
from typing import Union
from neoaccess import NeoAccess
from brainannex import NeoSchema


class UserManager:
    """
    Class for User Management in the database, including handling of encrypted passwords

    This is a STATIC class that doesn't get initialized.
    IMPORTANT: prior to use, its class variable "db" must be set, by calling set_database()
    """

    db = None   # "NeoAccess" object.  MUST be set before using this class!
                # Note: this database-interface object is a CLASS variable, accessible as cls.db



    @classmethod
    def set_database(cls, db :NeoAccess) -> None:
        """
        IMPORTANT: this method MUST be called before using this class!

        :param db:  Database-interface object, created with the NeoAccess library
        :return:    None
        """

        assert type(db) == NeoAccess, \
            "UserManager.set_database(): argument passed isn't a valid NeoAccess object"

        cls.db = db



    @classmethod
    def create_schema(cls) -> None:
        """
        Create the database Schema used by this class

        :return:    None
        """
        NeoSchema.create_class_with_properties(name="User",
                    properties=["user_id", "username", "password", "email", "admin"], strict=True)

        NeoSchema.set_property_attribute(class_name="User", prop_name="user_id", attribute_name="dtype", attribute_value="int")
        NeoSchema.set_property_attribute(class_name="User", prop_name="admin", attribute_name="dtype", attribute_value="bool")

        NeoSchema.set_property_attribute(class_name="User", prop_name="user_id",  attribute_name="required", attribute_value=True)
        NeoSchema.set_property_attribute(class_name="User", prop_name="username", attribute_name="required", attribute_value=True)
        NeoSchema.set_property_attribute(class_name="User", prop_name="password", attribute_name="required", attribute_value=True)



    @classmethod
    def create_user(cls, username :str, password :str, email=None, admin=False, min_pass_len=8) -> int:
        """

        :param username:    A string with a username not already registered;
                                if already present in the database, an Exception is raised
        :param password:
        :param email:
        :param admin:       If True, the new user is declare to be an administrator;
                                otherwise, a "regular" user
        :param min_pass_len:
        :return:            The integer ID automatically assigned to this new user
        """
        # CREATE (n:`User` {user_id: 1, username: "the_desired_username", password: "the_desired_password"})

        assert (type(username) == str) and (username != ""), \
            f"create_user(): bad or missing username ({username})"

        if email is not None:
            assert type(email) == str, \
                f"create_user(): bad email address ({email})"

        assert (type(password) == str) and (len(password) >= min_pass_len), \
            f"create_user(): password must be at least 8 characters"

        hashed_password = cls.create_hashed_password(password)

        user_id = NeoSchema.advance_autoincrement(namespace="user")     # Reserve a unique integer ID for this new user

        # Attempt to create a new data node for the user,
        # if no other node with the same given username already exists
        internal_id, created = NeoSchema.add_data_node_merge(class_name="User",
                                                             properties={"username": username})
        assert created, \
            f"create_user(): the username `{username}` already exists"


        user_fields = {"user_id": user_id, "password": hashed_password, "admin": admin}
        if email:
            user_fields["email"] = email

        number_set = NeoSchema.update_data_node(data_node=internal_id, set_dict=user_fields)

        assert number_set == len(user_fields), \
            f"create_user(): user `{username}` created, but some or all of its properties could not be set"

        return user_id



    @classmethod
    def delete_user(cls, username :str):
        pass        # TODO: implement


    @classmethod
    def update_user(cls, username :str):
        pass        # TODO: implement



    @classmethod
    def create_hashed_password(cls, password :str) -> bytes:
        """
        Create and return a bytes object with a hashed version of the given password,
        including a random portion ("salt")

        :param password:    A user-provided password
        :return:            A hashed version of the above password, including a random portion ("salt")
        """
        # Generate a salt (a random value, of class 'bytes', used to add extra security to the hashed password)
        salt = bcrypt.gensalt(11)   # EXAMPLE: b'$2b$11$S0A.j0tc0G9F38IleZ43QO'
                                    # 29 bytes, starting with the algorithm ($2b$) and the passed parameter (11$)

        # Take the password (encoded to bytes) and the salt, and returns the hashed password
        # Note: encode() converts the password to a 'bytes' type
        hashed_password = bcrypt.hashpw(password.encode(), salt)    # 60 bytes long
        # EXAMPLE : b'$2b$11$S0A.j0tc0G9F38IleZ43QOdyecDS1ylktqdinJTck.Rcvz9CZ1k/6'
        #       salt--^---------------------------^

        return hashed_password



    @classmethod
    def check_password(cls, provided_password :str, hashed_password :bytes) -> bool:
        """
        Verify whether a password provided by the user matches its hashed counterpart
        (the version stored in the database)

        :param provided_password:   A string provided by the user to authenticate
        :param hashed_password:     A bytes object that was stored in the database when the
                                        user first registered
        :return:                    True if the passwords match, or False otherwise
        """
        return bcrypt.checkpw(provided_password.encode(), hashed_password)



    @classmethod
    def get_username(cls, user_id :int) -> Union[str, None]:
        """
        Look up and return the username of a user specified by their user_id;
        if not found, return None

        :param user_id: Integer representing the user being looked up
        :return:        The username of requested user; if not found, None
        """
        # Query the database
        result_dict = cls.db.get_record_by_primary_key(labels="User",
                                                       primary_key_name="user_id", primary_key_value=user_id)
        if (result_dict is None) or ("username" not in result_dict):
            #print("get_username(): node not found in the database, or missing an attribute `username`")
            return None     # Not found

        return result_dict["username"]



    @classmethod
    def check_login_credentials(cls, username: str, password: str) -> Union[int, None]:
        """
        Verify the validity of the specified user-passed password for the given username,
        by consulting the database.
        The password is compared against its encrypted version stored in the database.
        If successful, return the User ID; otherwise, return None

        :param username:    A string with the username
        :param password:    A string provided by the user to authenticate
        :return:            If the login credentials are valid, return an integer with the User ID;
                                otherwise, return None
        """
        # Query the database to get back a list of users with the given username (ideally, exactly 1)
        lookup_info = {"username": username}
        match = cls.db.match(labels="User", properties=lookup_info)
        db_record_list = cls.db.get_nodes(match=match)

        print("check_login_credentials(). List of dbase records with matching username:", db_record_list)

        if len(db_record_list) != 1:
            print(f"check_login_credentials(): no matches or more than one for username `{username}`")
            return None           # Unsuccessful login
        else:
            db_record = db_record_list[0]
            stored_password = db_record["password"]
            if cls.check_password(provided_password=password, hashed_password=stored_password):
                user_id = db_record["user_id"]
                print("check_login_credentials(): successful validation of user credentials. User ID: ", user_id)
                return user_id      # Successful login
            else:
                print(f"check_login_credentials(): failed validation of user credentials for user `{username}`")
                return None



    @classmethod
    def authenticate_user(cls, username :str, password :str) -> bool:
        """
        Return True if the passed user's credentials validate against those stored in the database,
        or False otherwise.
        The provided password is compared against its encrypted version stored in the database.

        :param username:    A string with the username
        :param password:    A string provided by the user to authenticate
        :return:            True if the user's credentials validate against the database,
                                or False otherwise
        """
        user_id = cls.check_login_credentials(username, password)

        return False if user_id is None else True
