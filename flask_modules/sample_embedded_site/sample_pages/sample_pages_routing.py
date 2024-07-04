"""
Generator of Sample Pages for the Example Embedded Site
"""

from flask import Blueprint, render_template, request   # The "request" package makes available a GLOBAL request object
from flask_modules.navigation.navigation import get_site_pages        # Navigation configuration for this site



class SamplePagesRouting:
    """
    Setup, routing and endpoints for all the web pages served by this module
    """

    # Module-specific parameters (as class variables)
    blueprint_name = "sample_pages_flask"   # Name unique to this module
    url_prefix = "/sample/pages"            # Prefix for all URL's handled by this module
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
        @bp.route('/minimalist-flask')
        def minimalist_flask() -> str:
            # Demonstration of a minimalist Flask page (with no template involved)
            # EXAMPLE invocation: http://localhost:5000/sample/pages/minimalist-flask

            return "Example of a minimalist <b>Flask-generated</b> page"



        @bp.route('/sample-page')
        def sample_page() -> str:
            # EXAMPLE invocation: http://localhost:5000/sample/pages/sample-page

            template = "sample.htm"
            return render_template(template, current_page=request.path, site_pages=get_site_pages())



        @bp.route('/flask-testing')
        def flask_testing() -> str:
            # Test area for Flask-based development
            # Not in actual use: so, OK TO CHANGE IT AS IT SUITS YOUR FOR YOUR TESTING/EXPERIMENTING

            # EXAMPLE invocation: http://localhost:5000/sample/pages/flask-testing


            # 1. Here, insert code to produce the data needed for the HTML page

            # Examples
            my_variable = "temperature"
            my_list = ["a", "b", "c"]


            template = "flask_testing.htm"   # 2. Locate and change this HTML template as it suits you
            #           (in the "sample_embedded_site/sample_pages/templates" folder)
            #    Optionally, tweak its CSS file flask_testing.css
            #           (in the "sample_embedded_site/sample_pages/static" folder)


            # 3. Pass to the HTML template whatever variables are needed
            #    (current_page and site_pages are currently used for navigation)
            return render_template(template,
                                   current_page=request.path, site_pages=get_site_pages(),
                                   biomarker = my_variable, my_list = my_list,
                                   template_page=template)

        ##################  END OF ROUTING DEFINITIONS  ##################
