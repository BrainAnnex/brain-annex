"""
Router/generator for navigation pages:
    CSS static pages, and HTML pages that get included into other Flask files
"""

from flask import Blueprint



class Navigation:
    """
    Setup, and routing, for all the web pages served by this module
    """

    # Module-specific parameters (as class variables)
    blueprint_name = "navigation"     # Name unique to this module
    url_prefix = "/navigation"        # Prefix for all URL's handled by this module
    template_folder = "templates"     # Relative to this module's location
    static_folder = "static"          # Relative to this module's location



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
                                    template_folder=cls.template_folder, static_folder=cls.static_folder)

        # Define the Flask routing (mapping URLs to Python functions) for all the web pages served by this module
        #cls.set_routing(flask_blueprint)       # NOT USED IN THIS MODULE

        # Register with the Flask app object the Blueprint object created above, and request the desired URL prefix
        flask_app_obj.register_blueprint(flask_blueprint, url_prefix = cls.url_prefix)
