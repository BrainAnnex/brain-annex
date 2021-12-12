"""
Generator of Sample Pages in Example Embedded Site
"""

from flask import Blueprint, render_template, request   # The "request" package makes available a GLOBAL request object
from navigation.navigation import get_site_pages   # Navigation configuration for this site


# This "Blueprint" object gets registered in the Flask app object in main.py, using: url_prefix = "/sample/pages"
# Specify where this module's TEMPLATE and STATIC folders are located (relative to this module's main folder)
sample_pages_flask_blueprint = Blueprint('sample_pages_flask', __name__,
                                         template_folder='templates', static_folder='static')



################################################################################################
#         Define the Flask routing (mapping URLs to Python functions)                          #
#         for all the web pages served by this module                                          #
#                                                                                              #
#         "@" signifies a decorator - a way to wrap a function and modify its behavior         #
################################################################################################




##################   PAGES  (Demo examples and test area for Flask developers)   ##################

@sample_pages_flask_blueprint.route('/minimalist-flask')
def minimalist_flask() -> str:
    # Demonstration of a minimalist Flask page (with no template involved)
    # EXAMPLE invocation: http://localhost:5000/sample/pages/minimalist-flask

    return "Example of a minimalist <b>Flask-generated</b> page"



@sample_pages_flask_blueprint.route('/sample-page')
def sample_page() -> str:
    # EXAMPLE invocation: http://localhost:5000/sample/pages/sample-page

    template = "sample.htm"
    return render_template(template, current_page=request.path, site_pages=get_site_pages())



@sample_pages_flask_blueprint.route('/flask-testing')
def flask_testing() -> str:
    # Test area for Flask-based development
    # Not in actual use: so, OK TO CHANGE IT AS IT SUITS YOUR FOR YOUR TESTING/EXPERIMENTING

    # EXAMPLE invocation: http://localhost:5000/sample/pages/flask-testing


    # 1. Here, insert code to produce the data needed for the HTML page

    # Examples
    my_variable = "temperature"
    my_list = ["a", "b", "c"]


    url = "flask_testing.htm"   # 2. Locate and change this HTML template as it suits you
                                #           (in the "sample_embedded_site/sample_pages/templates" folder)
                                #    Optionally, tweak its CSS file flask_testing.css
                                #           (in the "sample_embedded_site/sample_pages/static" folder)

    # 3. Pass to the HTML template whatever variables are needed
    #    (current_page and site_pages are currently used for navigation)
    return render_template(url, current_page=request.path, site_pages=get_site_pages(),
                           biomarker = my_variable, my_list = my_list)
