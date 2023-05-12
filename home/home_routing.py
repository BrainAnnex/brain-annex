"""
Router/generator for navigation pages:
    CSS static pages, and HTML pages that get included into other Flask files
"""

from flask import Blueprint, render_template, request, session      # Not used: redirect
from home.user_manager import UserManagerNeo4j, User
import flask_login



class Home:
    """
    Setup, and routing, for all the web pages served by this module.

    This is a STATIC class that doesn't get initialized
    """

    # Module-specific parameters (as class variables)
    blueprint_name = "home"         # Name unique to this module
    #url_prefix = ""                # NOT USED FOR THIS TOP-LEVEL MODULE.  Prefix for all URL's handled by this module
    template_folder = "templates"   # Relative to this module's location
    static_folder = "static"        # Relative to this module's location


    # Set up the user-authentication mechanism
    # From docs: "The login manager contains the code that lets this application and Flask-Login work together,
    #             such as how to load a user from an ID, where to send users when they need to log in, etc."
    login_manager = None                # This gets a value assigned by calls to setup()

    config_pars = {}                    # Dict with all the app configuration parameters



    #############################################################
    #         REGISTRATION OF THIS MODULE WITH FLASK            #
    #############################################################

    @classmethod
    def setup(cls, flask_app_obj, config_dict) -> None:
        """
        Based on this module-specific class variables, and given a Flask app object,
        instantiate a "Blueprint" object,
        and register:
            the names of folders used for templates and static content
            the URL prefix to use
            the functions that will be assigned to the various URL endpoints [NOT USED IN THIS MODULE]

        :param flask_app_obj:	The Flask app object
        :param config_dict:     Dict with all the app configuration parameters
        :return:				None
        """
        flask_blueprint = Blueprint(cls.blueprint_name, __name__,
                                    template_folder=cls.template_folder,
                                    static_folder=cls.static_folder, static_url_path='/assets')

        login_manager_obj = flask_login.LoginManager(app=flask_app_obj) # Object of type "LoginManager"
        login_manager_obj.login_view = "/login"     # Specify a page to redirect to whenever an attempt is made
                                                    # to access a page requiring login, without being logged in
                                                    # If not specified, a "401 Unauthorized" error is returned

        # Define the Flask routing (mapping URLs to Python functions) for all the web pages served by this module
        cls.set_routing(flask_blueprint, login_manager_obj)

        # Register with the Flask app object the Blueprint object created above, and request the desired URL prefix
        flask_app_obj.register_blueprint(flask_blueprint)       # NOT USED:  url_prefix = cls.url_prefix

        # Save the app configuration parameters in a class variable
        cls.config_pars = config_dict




    #############################################################
    #                           ROUTING                         #
    #############################################################

    @classmethod
    def set_routing(cls, bp, login_manager_obj) -> None:
        """
        Define the Flask routing (mapping URLs to Python functions)
        for all the web pages served by this module,
        and provide the functions assigned to the various URL endpoints

        :param bp:                  The Flask "Blueprint" object that was created for this module
        :param login_manager_obj:   Object of type "LoginManager" (from the "flask_login" package)
        :return:                    None
        """

        ##################  START OF ROUTING DEFINITIONS  ##################

        # "@" signifies a decorator - a way to wrap a function and modify its behavior
        @bp.route("/")    # Root  : SET BROWSER TO http://localhost:5000  or http://IP_ADDRESS:5000
        def index():
            # Serve a top-level page
            template = "index.htm"
            return render_template(template)



        #####################
        #   Login-related   #
        #####################

        #"@" signifies a decorator - a way to wrap a function and modify its behavior
        @bp.route('/login')
        def login() -> str:
            """
            EXAMPLE invocation: http://localhost:5000/login
            """
            template = "login.htm"
            """
            # DEBUGGING, TO DELETE
            not_yet_used = current_app.config['UPLOAD_FOLDER']
            print(not_yet_used)
            not_yet_used2 = current_app.config['APP_NEO4J_DBASE']
            print(not_yet_used2.credentials)
            """
            branding = cls.config_pars.get("BRANDING")
            return render_template(template, branding=branding)



        @bp.route("/do-login", methods=["POST"])
        def do_login():
            """
            Log in by username/password.
            This page get invoked by a login form that passes 2 POST variables: "username" and "passwd"
            """
            # Extract the POST values passed by the calling form
            username = request.form["username"]
            passwd = request.form["passwd"]
            print(f"do_login().  POST parameters -> username: `{username}` | passwd: `{passwd}`")

            # Verify the login credential against the database;
            # if successful, obtain the User ID (-1 in case of failure)
            user_id = UserManagerNeo4j.check_login_credentials(username, passwd)

            if user_id == -1:
                return "<b>Login failed</b>.  <a href='/login'>Try again</a>"


            # If we get thus far, the login authentication was successful


            # Look up or, if not found, create an object of type "User"
            user_obj = UserManagerNeo4j.prepare_user_obj(user_id, username)
            print("user_obj:", user_obj)
            UserManagerNeo4j.show_users()

            #print("~~~ Flask session ID PRIOR to login: ", session.get("_id"))

            status = flask_login.login_user(user_obj)

            print("status of login operation handled by Flask: ", status)
            print(f"~~~ Flask session ID upon login of user id {user_id}: ", session.get("_id"))

            if status:
                # flask.flash('Logged in successfully.')
                return F"<b>{user_obj.username}</b>, you are now logged in! <a href='/BA/pages/viewer'>Continue</a>"
                #return redirect(F"client/{user_id}")
            else:
                return "<b>Login failed</b>"



        @login_manager_obj.user_loader       # NOTE THE DIFFERENT DECORATOR HERE!
        def load_user(flask_user_id: str) -> User:
            """
            Callback function required by the "flask_login" package.

            From the docs:
            "This callback is used to reload the user object from the user ID stored in the session.
            It should take the unicode ID of a user, and return the corresponding user object.
            It should return None (not raise an exception) if the ID is not valid"

            :param flask_user_id:   ID of a user, expressed as a UNICODE string
            :return:                An object of type "User" if the ID is valid, or None if not
            """

            # TODO: return None if the flask_user_id is invalid
            user_id_as_int = ord(flask_user_id)     # Take a one-character Unicode string and return the code point value (an integer)
                                                    # Note: Unclear whether flask_login would ever use more than 1 character

            #user_id_as_int = flask_user_id         # In my test, this also worked if User.get_id is changed to return an integer

            print(f"Inside callback function load_user().  flask_user_id = {repr(flask_user_id)} , with integer representation : {user_id_as_int}")
            print("~~~ Flask session ID: ", session.get("_id"))

            return UserManagerNeo4j.obtain_user_obj(user_id_as_int)



        @bp.route("/protected")
        @flask_login.login_required
        def protected() -> str:
            """
            Sample protected page, only shown if logged in
            EXAMPLE invocation: http://localhost:5000/protected

            :return:    A string with the HTML for a simple web page
            """
            return "Hello `<b>" + flask_login.current_user.username + "</b>`. You are able to access this test protected page"



        @bp.route("/logout")
        @flask_login.login_required
        def logout() -> str:
            """
            User will be logged out, and any cookies for their session will be cleaned up.
            Also, provide a logout landing page.  TODO ? : replace the landing page with auto-forwarding to login page
            EXAMPLE invocation: http://localhost:5000/protected

            :return:    A string with the HTML for a bare-bones logout landing page
            """
            name = flask_login.current_user.username    # TODO: maybe turn (current_user.username) into a method...
            flask_login.logout_user()
            return "<b>" + name + "</b>, you're now logged out. &nbsp; <a href='/login'>Login</a>"
            # return redirect(somewhere)
