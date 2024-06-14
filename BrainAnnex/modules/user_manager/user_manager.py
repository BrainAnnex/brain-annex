import bcrypt
from typing import Union
from neoaccess import NeoAccess
from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema


class UserManager:
    """
    Class for User Management

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
    def create_schema(cls):
        NeoSchema.create_class_with_properties(name="User",
                    properties=["user_id", "username", "password", "email", "admin"], strict=True)

        NeoSchema.set_property_attribute(class_name="User", prop_name="user_id", attribute_name="dtype", attribute_value="int")
        NeoSchema.set_property_attribute(class_name="User", prop_name="admin", attribute_name="dtype", attribute_value="bool")

        NeoSchema.set_property_attribute(class_name="User", prop_name="user_id",  attribute_name="required", attribute_value=True)
        NeoSchema.set_property_attribute(class_name="User", prop_name="username", attribute_name="required", attribute_value=True)
        NeoSchema.set_property_attribute(class_name="User", prop_name="password", attribute_name="required", attribute_value=True)



    @classmethod
    def create_user(cls, username :str, password :str, email :str, admin=False):
        """

        :param username:
        :param password:
        :param email:
        :param admin:
        :return:
        """
        # CREATE (n:`User` {user_id: 1, username: "the_desired_username", password: "the_desired_password"})

        assert (type(username) == str) and (username != ""), \
            f"create_user(): bad or missing username ({username})"

        assert (type(email) == str) and (email != ""), \
            f"create_user(): bad or missing email address ({email})"

        assert (type(password) == str) and (len(password) > 7), \
            f"create_user(): password must be at least 8 characters"

        hashed_password = cls.create_hashed_password(password)

        user_id = NeoSchema.advance_autoincrement(namespace="user")

        #NeoSchema.create_data_node(class_node="User",
                        #properties={"user_id": user_id, "username": username, "password": password, "email": email, "admin": admin})

        internal_id, created = NeoSchema.add_data_node_merge(class_name="User",
                                                             properties={"username": username})
        assert created, f"create_user(): the username `{username}` already exists"

        number_set = NeoSchema.update_data_node(data_node=internal_id,
                            set_dict={"user_id": user_id, "password": hashed_password, "email": email, "admin": admin})

        assert number_set == 4, \
            f"create_user(): user `{username}` created, but some or all of its properties could not be set"



    @classmethod
    def create_hashed_password(cls, password :str) -> bytes:
        """

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
    def authenticate_user(cls, username :str, password :str) -> bool:
        """

        :param username:
        :param password:
        :return:            True if the user's credentials validate against the database,
                                or False otherwise
        """
        pass



    @classmethod
    def get_username(cls, user_id :int) -> Union[str, None]:
        """

        :param user_id:
        :return:
        """
        # The requested "User" object was NOT found in the local lookup table; now attempt to retrieve it from the database

        # Query the database
        #print(f"obtain_user_obj(): querying the dbase for node labeled `User Login`, "
        #f"with attribute `user_id` having a value of `{user_id}`")
        result_dict = cls.db.get_record_by_primary_key(labels="User Login",
                                                       primary_key_name="user_id", primary_key_value=user_id)
        if (result_dict is None) or ("username" not in result_dict):
            #print("obtain_user_obj(): node not found in the database, or missing an attribute `username`")
            return None     # Not found

        username = result_dict["username"]

        return username



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
