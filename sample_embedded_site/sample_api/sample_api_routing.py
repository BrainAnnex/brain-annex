"""
SAMPLE API endpoint
"""

from flask import Blueprint, jsonify



# This "Blueprint" object gets registered in the Flask app object in main.py, using: url_prefix = "/sample/api"
# Specify where this module's STATIC folder is located (relative to this module's main folder)
sample_api_flask_blueprint = Blueprint('sample_api_flask', __name__, static_folder='static')



################################################################################################
#         Define the Flask routing (mapping URLs to Python functions)                          #
#         for all the web pages served by this module                                          #
#                                                                                              #
#         "@" signifies a decorator - a way to wrap a function and modify its behavior         #
################################################################################################




##################   A few simple examples of API endpoints   ##################

@sample_api_flask_blueprint.route('/test1')
def sample_api_test1() -> str:
    # EXAMPLE invocation: http://localhost:5000/sample/api/test1

    return "It <i>really</i> works!"  # This function also takes care of the Content-Type header



@sample_api_flask_blueprint.route('/test2')
def sample_api_test2():
    # EXAMPLE invocation: http://localhost:5000/sample/api/test2

    response = {"status": "ok", "data": "Some data"}
    return jsonify(response)  # This function also takes care of the Content-Type header
