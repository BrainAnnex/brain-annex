"""
Router/generator for navigation pages
"""

from flask import Blueprint


# This "Blueprint" object is registered in the Flask app object, using: url_prefix = "/"
# Specify where this module's TEMPLATE and STATIC folders are located (relative to this module's main folder)
navigation_flask_blueprint = Blueprint('navigation', __name__,
                                       template_folder='templates', static_folder='static')