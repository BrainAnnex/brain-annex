"""
SAMPLE API endpoint
"""

from flask import Blueprint, jsonify



class SampleApiRouting:
    """
    Setup, routing and endpoints for all the web pages served by this module
    """

    # Module-specific parameters (as class variables)
    blueprint_name = "sample_api_flask"     # Name unique to this module
    url_prefix = "/sample/api"              # Prefix for all URL's handled by this module
    template_folder = "templates"           # Relative to this module's location
    static_folder = "static"                # Relative to this module's location
    config_pars = {}                        # Dict with all the app configuration parameters



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
            the functions that will be assigned to the various URL endpoints

        :param flask_app_obj:	The Flask app object
        :return:				None
        """
        flask_blueprint = Blueprint(cls.blueprint_name, __name__,
                                    template_folder=cls.template_folder, static_folder=cls.static_folder)

        # Define the Flask routing (mapping URLs to Python functions) for all the web pages served by this module
        cls.set_routing(flask_blueprint)

        # Register with the Flask app object the Blueprint object created above, and request the desired URL prefix
        flask_app_obj.register_blueprint(flask_blueprint, url_prefix = cls.url_prefix)

        # Save the app configuration parameters in a class variable
        cls.config_pars = flask_app_obj.config




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

        #"@" signifies a decorator - a way to wrap a function and modify its behavior
        @bp.route('/test1')
        def sample_api_test1() -> str:
            # EXAMPLE invocation: http://localhost:5000/sample/api/test1

            return "It <i>really</i> works!"  # This function also takes care of the Content-Type header



        @bp.route('/test2')
        def sample_api_test2():
            # EXAMPLE invocation: http://localhost:5000/sample/api/test2

            response = {"status": "ok", "data": "Some data"}
            return jsonify(response)  # This function also takes care of the Content-Type header

        ##################  END OF ROUTING DEFINITIONS  ##################
