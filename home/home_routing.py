"""
Router/generator for navigation pages:
    CSS static pages, and HTML pages that get included into other Flask files
"""

from flask import Blueprint, render_template



class Home:
    """
    Setup, and routing, for all the web pages served by this module
    """

    # Module-specific parameters (as class variables)
    blueprint_name = "home"         # Name unique to this module
    #url_prefix = ""                # NOT USED FOR THIS TOP-LEVEL MODULE.  Prefix for all URL's handled by this module
    template_folder = "templates"   # Relative to this module's location
    static_folder = "static"        # Relative to this module's location



    #############################################################
    #         REGISTRATION OF THIS MODULE WITH FLASK            #
    #############################################################

    @classmethod
    def setup(cls, flask_app_obj) -> None:
        """
        Based on the module-specific class variables, and given a Flask app object,
        instantiate a "Blueprint" object,
        and register:
            the names of folders used for templates and static content
            the URL prefix to use
            the functions that will be assigned to the various URL endpoints [NOT USED IN THIS MODULE]

        :param flask_app_obj:	The Flask app object
        :return:				None
        """
        flask_blueprint = Blueprint(cls.blueprint_name, __name__,
                                    template_folder=cls.template_folder,
                                    static_folder=cls.static_folder, static_url_path='/assets')

        # Define the Flask routing (mapping URLs to Python functions) for all the web pages served by this module
        cls.set_routing(flask_blueprint)

        # Register with the Flask app object the Blueprint object created above, and request the desired URL prefix
        flask_app_obj.register_blueprint(flask_blueprint)       # NOT USED:  url_prefix = cls.url_prefix




    #############################################################
    #                           ROUTING                         #
    #############################################################

    @classmethod
    def set_routing(cls, bp) -> None:
        """
        Define the Flask routing (mapping URLs to Python functions)
        for all the web pages served by this module,
        and provide the functions assigned to the various URL endpoints

        :param bp:  The Flask "Blueprint" object that was created for this module
        :return:    None
        """

        ##################  START OF ROUTING DEFINITIONS  ##################

        # "@" signifies a decorator - a way to wrap a function and modify its behavior
        @bp.route("/")    # Root  : SET BROWSER TO http://localhost:5000
        def index():
            # Serve a minimalist home page
            return "Welcome to Brain Annex: the web server is running.<br><br><a href='/login'>Login</a>"



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
            return render_template(template)