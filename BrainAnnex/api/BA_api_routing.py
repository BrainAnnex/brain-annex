from flask import Blueprint, jsonify, request, make_response  # The request package makes available a GLOBAL request object
from BrainAnnex.api.BA_api_request_handler import APIRequestHandler
from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema
from BrainAnnex.modules.node_explorer.node_explorer import NodeExplorer
from BrainAnnex.modules.categories.categories import Categories
import sys                  # Used to give better feedback on Exceptions
import shutil
from time import sleep      # Used for tests of delays in asynchronous fetching

"""
    API endpoint


    ----------------------------------------------------------------------------------
	MIT License

    Copyright (c) 2021 Julian A. West

    This file is part of the "Brain Annex" project (https://BrainAnnex.org)

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
	----------------------------------------------------------------------------------

"""


# This "Blueprint" object gets registered in the Flask app object in main.py, using: url_prefix = "/BA/api"
# Specify where this module's STATIC folder is located (relative to this module's main folder)
BA_api_flask_blueprint = Blueprint('BA_api', __name__, static_folder='static')



###################################################################################################################
#                                                                                                                 #
#   The "simple" subset of the API, with endpoints that return PLAIN text (rather than JSON or something else)    #
#                                                                                                                 #
###################################################################################################################

ERROR_PREFIX = "-"      # Prefix used in the "simple API" protocol to indicate an error in the response value;
#       the remainder of the response string will the be understood to be the error message

SUCCESS_PREFIX = "+"    # Prefix used in the "simple API" protocol to indicate a successful operation;
#       the remainder of the response string will the be understood to be the optional data payload
#       (such as a status message)

# NOTE: To test POST-based API access points, on the Linux shell or Windows PowerShell issue commands such as:
#            curl http://localhost:5000/BA/api/simple/add_item_to_category -d "schema_id=1&category_id=60"




###############################################
#               For DEBUGGING                 #
###############################################

def exception_helper(ex) -> str:       # TODO: 2 copies of this functions currently exist
    """
    To give better info on an Exception.
    The info returned by "ex" is skimpy; for example, in case of a key error, all that it returns is the key name!

    :param ex:  The Exemption object

    :return:    A string with a more detailed explanation of the given Exception (prefixed by the Exception type)
    """
    (exc_type, _, _) = sys.exc_info()
    return str(exc_type) + " : " + str(ex)



def show_post_data(post_data, method_name=None) -> None:
    """
    Debug utility method

    :param post_data:
    :param method_name: Name of invoking function
    :return:            None
    """
    if method_name:
        print(f"In {method_name}(). POST data: ")
    else:
        print(f"POST data: ")

    for k, v in post_data.items():
        print("    ", k , " -> " , v)
    print("-----------")




###################################################################################################################
#               Define the Flask routing (mapping URLs to Python functions)                                       #
#               for all the web pages served by this module                                                       #
#                                                                                                                 #
#               "@" signifies a decorator - a way to wrap a function and modify its behavior                      #
###################################################################################################################


###############################################
#                SCHEMA-related               #
###############################################

@BA_api_flask_blueprint.route('/get_properties/<schema_id>')
def get_properties(schema_id):
    """
    Get all Properties by the schema_id of a Class node,
    including indirect ones thru chains of outbound "INSTANCE_OF" relationships

    EXAMPLE invocation: http://localhost:5000/BA/api/get_properties/4

    :param schema_id:   ID of a Class node
    :return:            A JSON object with a list of the Properties of the specified Class
                        EXAMPLE:
                            [
                              "Notes",
                              "English",
                              "French"
                            ]
    """

    # Fetch all the Properties
    prop_list = NeoSchema.get_class_properties(int(schema_id), include_ancestors=True)
    response = {"status": "ok", "payload": prop_list}
    # TODO: handle error scenarios

    return jsonify(response)   # This function also takes care of the Content-Type header


@BA_api_flask_blueprint.route('/get_properties_by_class_name', methods=['POST'])
def get_properties_by_class_name():
    """
    Get all Properties of the given Class node (as specified by its name passed as a POST variable),
    including indirect ones thru chains of outbound "INSTANCE_OF" relationships.
    Return a JSON object with a list of the Property names of that Class.

    EXAMPLE invocation:
        curl http://localhost:5000/BA/api/get_properties_by_class_name  -d "class_name=Restaurant"

    1 POST FIELD:
        class_name

    :return:            A JSON object with a list of the Property names of the specified Class
                        EXAMPLE:
                            [
                              "Notes",
                              "English",
                              "French"
                            ]
    """

    # Extract the POST values
    post_data = request.form     # Example: ImmutableMultiDict([('class_name', 'Restaurant')])
    show_post_data(post_data, "get_properties_by_class_name")

    data_dict = dict(post_data)
    if "class_name" not in data_dict:
        response = {"status": "error", "error_message": "The expected POST parameter `class_name` is not present"}
    else:
        class_name = data_dict["class_name"]
        schema_id = NeoSchema.get_class_id(class_name)
        if schema_id == -1:
            response = {"status": "error", "error_message": f"Unable to locate any Class named `{class_name}`"}
        else:
            try:
                # Fetch all the Properties
                prop_list = NeoSchema.get_class_properties(schema_id, include_ancestors=True)
                response = {"status": "ok", "payload": prop_list}
            except Exception as ex:
                response = {"status": "error", "error_message": str(ex)}

    print(f"get_properties_by_class_name() is returning: `{response}`")

    return jsonify(response)   # This function also takes care of the Content-Type header



@BA_api_flask_blueprint.route('/get_properties_by_item_id/<item_id>')
def get_properties_by_item_id(item_id):
    """
    Get all properties by item_id

    EXAMPLE invocation: http://localhost:5000/BA/api/get_properties_by_item_id/123

    :param item_id:
    :return:            A JSON object with a list of the Properties of the specified Class
                        EXAMPLE:
                            [
                              "Notes",
                              "English",
                              "French"
                            ]
    """
    prop_list = NeoSchema.all_properties("BA", "item_id", int(item_id))
    response = {"status": "ok", "payload": prop_list}
    # TODO: handle error scenarios

    return jsonify(response)   # This function also takes care of the Content-Type header



@BA_api_flask_blueprint.route('/simple/create_new_record', methods=['POST'])
def create_new_record():
    """
    TODO: this is a simple, interim version - to later switch to JSON

    EXAMPLES of invocation:
        curl http://localhost:5000/BA/api/simple/create_new_record -d "data=Quotes,quote,attribution,notes"

    1 POST FIELD:
        data    The name of the new Class, followed by the name of all desired Properties, in order
                (all comma-separated)
    """
    # Extract the POST values
    post_data = request.form     # Example: ImmutableMultiDict([('data', 'Quotes,quote,attribution,notes')])
    show_post_data(post_data, "create_new_record")

    try:
        APIRequestHandler.new_record_class(dict(post_data))
        return_value = SUCCESS_PREFIX               # Success
    except Exception as ex:
        err_status = f"UNABLE TO CREATE NEW CLASS WITH PROPERTIES: {ex}"
        return_value = ERROR_PREFIX + err_status    # Failure

    print(f"create_new_record() is returning: `{return_value}`")

    return return_value



@BA_api_flask_blueprint.route('/get_record_classes')
def get_record_classes() -> str:
    """
    Get all Classes that are, directly or indirectly, INSTANCE_OF the Class "Records",
    as long as they are leaf nodes (with no other Class that is an INSTANCE_OF them.)

    EXAMPLE: if the "Foreign Vocabulary" Class is an INSTANCE_OF the Class "Records",
             and if "French Vocabulary" and "German Vocabulary" are instances of "Foreign Vocabulary",
             then "French Vocabulary" and "German Vocabulary" (but NOT "Foreign Vocabulary")
             would be returned

    EXAMPLE invocation: http://localhost:5000/BA/api/get_record_classes
    """

    try:
        result = APIRequestHandler.get_leaf_records()
        response = {"status": "ok", "payload": result}              # Successful termination
    except Exception as ex:
        response = {"status": "error", "error_message": str(ex)}    # Error termination

    print(f"get_record_classes() is returning: `{response}`")

    return jsonify(response)        # This function also takes care of the Content-Type header



#######################################################
#                CONTENT-ITEM MANAGEMENT              #
#######################################################

@BA_api_flask_blueprint.route('/simple/get_media/<item_id>')
def get_media(item_id) -> str:
    """
    Retrieve and return the text content of a media item (for now, just "notes")

    EXAMPLE invocation: http://localhost:5000/BA/api/simple/get_media/123
    """
    #sleep(1)    # For debugging

    #content = "Media data TBA for note id " + item_id
    status, content = APIRequestHandler.get_content("n", int(item_id))

    if status is False:
        return_value = ERROR_PREFIX + "Unable to retrieve note id " + item_id + " : " + content
        print(f"get_media() is encountered error: {return_value}")
    else:
        return_value = SUCCESS_PREFIX + content
        print(f"get_media() is returning the following text [first 40 chars]: `{return_value[:40]}`")

    return return_value



@BA_api_flask_blueprint.route('/simple/update', methods=['POST'])
def update() -> str:
    """
    Update an existing Content Item
    EXAMPLE invocation: http://localhost:5000/BA/api/simple/update
    """
    # Extract the POST values
    post_data = request.form     # Example: ImmutableMultiDict([('item_id', '11'), ('schema_code', 'r')])

    err_status = APIRequestHandler.update_content_item(dict(post_data))

    if err_status == "":    # If no errors
        return_value = SUCCESS_PREFIX
    else:                   # If errors
        return_value = ERROR_PREFIX + err_status

    print(f"update() is returning: `{return_value}`")

    return return_value



@BA_api_flask_blueprint.route('/simple/delete/<item_id>/<schema_code>')
def delete(item_id, schema_code) -> str:
    """
    Delete the specified Content Item.
    Note that schema_code is redundant.
    EXAMPLE invocation: http://localhost:5000/BA/api/simple/delete/46/n
    """
    err_status = APIRequestHandler.delete_content_item(item_id, schema_code)

    if err_status == "":    # If no errors
        return_value = SUCCESS_PREFIX
    else:                   # If errors
        return_value = ERROR_PREFIX + err_status

    print(f"delete() is returning: `{return_value}`")

    return return_value




################################################
#               CATEGORY-RELATED               #
################################################

@BA_api_flask_blueprint.route('/simple/add_item_to_category', methods=['POST'])
def add_item_to_category() -> str:
    """
    Create a new Content Item attached to a particular Category
    EXAMPLE invocation:
    curl http://localhost:5000/BA/api/simple/add_item_to_category -d "category_id=708&insert_after=711&schema_code=h&text=New Header"

    POST FIELDS:
        category_id
        schema_code
        insert_after        Either an item_id, or one of the special values "TOP" or "BOTTOM"
        PLUS all applicable plugin-specific fields
    """
    # Extract the POST values
    post_data = request.form
    # Example: ImmutableMultiDict([('category_id', '123'), ('schema_code', 'h'), ('insert_after', '5'), ('text', 'My Header')])
    show_post_data(post_data, "add_item_to_category")

    # Create a new Content Item with the POST data
    try:
        new_id = APIRequestHandler.new_content_item_in_category(dict(post_data))
        return_value = SUCCESS_PREFIX + str(new_id)     # Include the newly-added ID as a payload
    except Exception as ex:
        return_value = ERROR_PREFIX + exception_helper(ex)

    print(f"add_item_to_category() is returning: `{return_value}`")

    return return_value



@BA_api_flask_blueprint.route('/simple/add_subcategory', methods=['POST'])
def add_subcategory() -> str:
    """
    Add a new Subcategory to a given Category
    (if the Subcategory already exists, use add_subcategory_relationship instead)
    EXAMPLE invocation: http://localhost:5000/BA/api/simple/add_subcategory

    POST FIELDS:
        category_id                     To identify the Category to which to add a Subcategory
        subcategory_name                The name to give to the new Subcategory
        subcategory_remarks (optional)
    """
    # Extract the POST values
    post_data = request.form     # Example: ImmutableMultiDict([('category_id', '12'), ('subcategory_name', 'Astronomy')])

    # Create a new Subcategory to a given Category, using the POST data
    try:
        new_id = Categories.add_subcategory(dict(post_data))
        return_value = SUCCESS_PREFIX + str(new_id)     # Include the newly-added ID as a payload
    except Exception as ex:
        return_value = ERROR_PREFIX + exception_helper(ex)

    print(f"add_subcategory() is returning: `{return_value}`")

    return return_value



@BA_api_flask_blueprint.route('/simple/delete_category/<category_id>')
def delete_category(category_id) -> str:
    """
    Delete the specified Category, provided that there are no Content Items linked to it
    EXAMPLE invocation: http://localhost:5000/BA/api/simple/delete_category/123
    """
    try:
        Categories.delete_category(int(category_id))
        return_value = SUCCESS_PREFIX
    except Exception as ex:
        return_value = ERROR_PREFIX + exception_helper(ex)

    print(f"delete_category() is returning: `{return_value}`")

    return return_value



@BA_api_flask_blueprint.route('/simple/add_subcategory_relationship')
def add_subcategory_relationship() -> str:
    """
    Create a subcategory relationship between 2 existing Categories.
    (To add a new subcategory, use add_subcategory instead)
    EXAMPLE invocation: http://localhost:5000/BA/api/simple/add_subcategory_relationship?sub=12&cat=1
    """
    try:
        subcategory_id: int = request.args.get("sub", type = int)
        category_id: int = request.args.get("cat", type = int)
        if subcategory_id is None:
            raise Exception("Missing value for parameter `sub`")
        if category_id is None:
            raise Exception("Missing value for parameter `cat`")

        Categories.add_subcategory_relationship(subcategory_id=subcategory_id, category_id=category_id)
        return_value = SUCCESS_PREFIX
    except Exception as ex:
        return_value = ERROR_PREFIX + exception_helper(ex)

    print(f"add_subcategory_relationship() is returning: `{return_value}`")

    return return_value


@BA_api_flask_blueprint.route('/simple/remove_subcategory_relationship')
def remove_subcategory_relationship() -> str:
    """
    Remove a subcategory relationship between 2 existing Categories.
    EXAMPLE invocation: http://localhost:5000/BA/api/simple/remove_subcategory_relationship?sub=12&cat=1
    """
    try:
        subcategory_id: int = request.args.get("sub", type = int)
        category_id: int = request.args.get("cat", type = int)
        if subcategory_id is None:
            raise Exception("Missing value for parameter `sub`")
        if category_id is None:
            raise Exception("Missing value for parameter `cat`")

        Categories.remove_subcategory_relationship(subcategory_id=subcategory_id, category_id=category_id)
        return_value = SUCCESS_PREFIX
    except Exception as ex:
        return_value = ERROR_PREFIX + exception_helper(ex)

    print(f"remove_subcategory_relationship() is returning: `{return_value}`")

    return return_value




#############    POSITIONING WITHIN CATEGORIES    #############

@BA_api_flask_blueprint.route('/simple/swap/<item_id_1>/<item_id_2>/<cat_id>')
def swap(item_id_1, item_id_2, cat_id) -> str:
    """
    Swap the positions of the specified Content Items within the given Category.

    EXAMPLE invocation: http://localhost:5000/BA/api/simple/swap/23/45/2
    """
    err_status:str = Categories.swap_content_items(item_id_1, item_id_2, cat_id)

    if err_status == "":    # If no errors
        return_value = SUCCESS_PREFIX
    else:                   # If errors
        return_value = ERROR_PREFIX + err_status

    print(f"swap() is returning: `{return_value}`")

    return return_value



@BA_api_flask_blueprint.route('/simple/reposition/<category_id>/<item_id>/<move_after_n>')
def reposition(category_id, item_id, move_after_n) -> str:
    """
    Reposition the given Content Item after the n-th item (counting starts with 1) in specified Category.
    TODO: switch to an after-item version?

    EXAMPLE invocation: http://localhost:5000/BA/api/simple/reposition/60/576/4
    """
    try:
        Categories.reposition_content(category_id=int(category_id), item_id=int(item_id), move_after_n=int(move_after_n))
        return_value = SUCCESS_PREFIX               # Success
    except Exception as ex:
        err_status = f"UNABLE TO REPOSITION ELEMENT: {ex}"
        return_value = ERROR_PREFIX + err_status    # Failure

    print(f"reposition() is returning: `{return_value}`")

    return return_value




###############################################################
#                            FILTERS                          #
###############################################################

@BA_api_flask_blueprint.route('/get-filtered-json', methods=['POST'])
def get_filtered_JSON() -> str:     # *** NOT IN CURRENT USE; see get_filtered() ***
    """
    Note: a form-data version is also available

    EXAMPLE invocation -    send a POST request to http://localhost:5000/BA/api/get-filtered-json
                            with body:
                            {"label":"BA", "key_name":"item_id", "key_value":123}

        On Win7 command prompt (but NOT the PowerShell!!), do:
            curl http://localhost:5000/BA/api/get-filtered-json -d "{\"label\":\"BA\", \"key_name\":\"item_id\", \"key_value\":123}"

    JSON KEYS (all optional):
        label       To name of a single Neo4j label
        key_name    A string with the name of a node attribute; if provided, key_value must be present, too
        key_value   The required value for the above key; if provided, key_name must be present, too
                                Note: no requirement for the key to be primary
    """
    # Extract the POST values
    #post_data = request.form
    #json_data = dict(post_data).get("json")     # EXAMPLE: '{"label": "BA", "key_name": "item_id", "key_value": 123}'

    json_data = request.get_json(force=True)    # force=True is needed if using the Win7 command prompt, even if including
                                                # the option    -H 'Content-Type: application/json'

    print(json_data)

    # Fetch the data from the filters
    #prop_list = NeoSchema.get_class_properties(int(schema_id), include_ancestors=True)
    prop_list = [1, 2, 3]
    response = {"status": "ok", "payload": prop_list}
    return jsonify(response)   # This function also takes care of the Content-Type header



@BA_api_flask_blueprint.route('/get_filtered', methods=['POST'])
def get_filtered() -> str:
    """
    Note: a JSON version is also available

    EXAMPLES of invocation:
        curl http://localhost:5000/BA/api/get_filtered -d "labels=BA&key_name=item_id&key_value=123"
        curl http://localhost:5000/BA/api/get_filtered -d "labels=CLASS&key_name=code&key_value=h"

    POST FIELDS (all optional):
        labels      To name of a single Neo4j label (TODO: for now, just 1 label)
        key_name    A string with the name of a node attribute; if provided, key_value must be present, too
        key_value   The required value for the above key; if provided, key_name must be present, too
                                Note: no requirement for the key to be primary
        limit       The max number of entries to return
    """
    # Extract the POST values
    post_data = request.form     # Example: ImmutableMultiDict([('label', 'BA'), ('key_name', 'item_id'), ('key_value', '123')])
    show_post_data(post_data, "get_filtered")

    try:
        result = APIRequestHandler.get_nodes_by_filter(dict(post_data))
        response = {"status": "ok", "payload": result}              # Successful termination
    except Exception as ex:
        response = {"status": "error", "error_message": str(ex)}    # Error termination

    print(f"get_filtered() is returning: `{response}`")

    return jsonify(response)        # This function also takes care of the Content-Type header




############################################################
#                       IMPORT-EXPORT                      #
############################################################

@BA_api_flask_blueprint.route('/import_json_file', methods=['GET', 'POST'])
def import_json_file() -> str:
    """
    EXAMPLE invocation: http://localhost:5000/BA/api/import_json_file

    Upload a file.  NOTE: the uploaded file remains in the temporary folder; it will need to be moved or deleted.j
    """

    if request.method != 'POST':
        return "This endpoint requires POST data (you invoked it with a GET method.) No action taken..."   # Handy for testing

    return_url = request.form["return_url"] # This originates from the HTML form :
    #    <input type="hidden" name="return_url" value="my_return_url">
    print("return_url: ", return_url)

    status = APIRequestHandler.upload_import_json(verbose=False, return_url=return_url)
    return status



@BA_api_flask_blueprint.route('/upload_media', methods=['POST'])
def upload_media():
    """
    Upload new media Content, to the (currently hardwired) media folder, and attach it to the Category
    specified in the POST variable "category_id"
    TODO: media is currently added to the END of the Category page

    USAGE EXAMPLE:
        <form enctype="multipart/form-data" method="POST" action="/BA/api/upload_media">
            <input type="file" name="file"><br>   <!-- IMPORTANT: the name parameter is assumed to be "file" -->
            <input type="submit" value="Upload file">
            <input type='hidden' name='category_id' value='123'>
            <input type='hidden' name='pos' value='10'> <!-- TODO: NOT YET IN USE! Media added at END OF PAGE -->
        </form>

    (Note: the "Dropzone" module invokes this handler in a similar way)

    If the upload is successful, a normal status (200) is returned (no response data);
        in case of error, a server error status is return (500), with an text error message
    """
    #MEDIA_FOLDER = "D:/Docs/- MY CODE/Brain Annex/BA-code/BrainAnnex/pages/static/media/"    # TODO: for now, hardwired here
    #MEDIA_FOLDER = "H:/Pics/Brain Annex/media/"    # TODO: for now, hardwired here
    MEDIA_FOLDER = "D:/Docs/- MY CODE/Brain Annex/BA-Win7/BrainAnnex/pages/static/media/"   # TODO: condense into 1 location
    # "../pages/static/media/" also works

    # Extract the POST values
    post_data = request.form     # Example: ImmutableMultiDict([('schema_code', 'r'), ('field_1', 'hello')])

    print("Uploading content thru upload_media()")
    print("POST variables: ", dict(post_data))

    err_status = ""

    try:
        (tmp_filename_for_upload, full_filename) = APIRequestHandler.upload_helper(request, html_name="file", verbose=True)
        print(f"Upload successful so far for file: `{tmp_filename_for_upload}` .  Full name: `{full_filename}`")
    except Exception as ex:
        err_status = f"<b>ERROR in upload</b>: {ex}"
        print(err_status)
        response = make_response(err_status, 500)
        return response


    # Move the uploaded file from its temp location to the media folder
    # TODO: let upload_helper (optionally) handle it

    src_fullname = "D:/tmp/" + tmp_filename_for_upload
    dest_folder = MEDIA_FOLDER
    dest_fullname = dest_folder + tmp_filename_for_upload
    print(f"Attempting to move `{src_fullname}` to `{dest_fullname}`")
    try:
        shutil.move(src_fullname, dest_fullname)
    except Exception as ex:
        err_status = f"Error in moving the file to the intended final destination ({dest_folder}) after upload. {ex}"
        return make_response(err_status, 500)


    category_id = int(post_data["category_id"])

    try:
        properties = APIRequestHandler.process_uploaded_image(tmp_filename_for_upload, dest_fullname)
    except Exception as ex:
        (exc_type, _, _) = sys.exc_info()
        err_status = "Unable save, or make a thumb from, the uploaded image. " + str(exc_type) + " : " + str(ex)
        return make_response(err_status, 500)


    # Update the database (for now, the image is added AT THE END of the Category page)
    try:
        Categories.add_content_media(category_id, properties=properties)
        response = ""
    except Exception as ex:
        (exc_type, _, _) = sys.exc_info()
        err_status = "Unable to store the file in the database. " + str(exc_type) + " : " + str(ex)
        response = make_response(err_status, 500)

    return response



@BA_api_flask_blueprint.route('/upload_file', methods=['POST'])
def upload_file():
    """
    Handle the request to upload a file to the temporary directory (defined in main.py).
    USAGE EXAMPLE:
        <form enctype="multipart/form-data" method="POST" action="/BA/api/upload_file">
            <input type="file" name="file"><br>   <!-- name is expected to be "file" -->
            <input type="submit" value="Upload file">
        </form>

    (Note: the "Dropzone" module invokes this handler in a similar way)

    If the upload is successful, a normal status (200) is returned (no response data);
        in case of error, a server error status is return (500), with an text error message
    """
    # Extract the POST values
    post_data = request.form     # Example: ImmutableMultiDict([('schema_code', 'r'), ('field_1', 'hello')])

    print("Uploading content thru upload_file()")
    print("POST variables: ", dict(post_data))

    err_status = ""

    try:
        (tmp_filename_for_upload, full_filename) = APIRequestHandler.upload_helper(request, html_name="file", verbose=True)
        print(f"Upload successful so far for file: `{tmp_filename_for_upload}` .  Full name: `{full_filename}`")
    except Exception as ex:
        err_status = f"<b>ERROR in upload</b>: {ex}"
        print(err_status)


    if err_status == "":    # If no errors
        response = ""
    else:                   # If errors
        response = make_response(err_status, 500)

    return response



@BA_api_flask_blueprint.route('/parse_datafile', methods=['GET', 'POST'])
def parse_datafile() -> str:
    """
    EXPERIMENTAL!  Upload and parse a datafile.
    The regular expression for the parsing is currently hardwired in import_datafile()
    Typically, the uploads are initiated by forms containing:
        <input type="file" name="imported_datafile">
        <input type="hidden" name="return_url" value="my_return_url">

    EXAMPLE invocation: http://localhost:5000/BA/api/parse_datafile

    :return:    String with status message
    """

    if request.method != 'POST':
        return "This endpoint requires POST data (you invoked it with a GET method.) No action taken..."   # Handy for testing

    try:
        (tmp_filename_for_upload, full_filename) = APIRequestHandler.upload_helper(request, html_name="imported_datafile", verbose=False)
    except Exception as ex:
        return f"<b>ERROR in upload</b>: {ex}"

    print("In import_datafile(): ", (tmp_filename_for_upload, full_filename))

    return_url = request.form["return_url"] # This originates from the HTML form :
    #    <input type="hidden" name="return_url" value="my_return_url">
    print("return_url: ", return_url)

    status_msg = APIRequestHandler.import_datafile(tmp_filename_for_upload, full_filename, test_only=True)

    status_msg += f" <a href='{return_url}' style='margin-left:50px'>Go back</a>"

    return status_msg



@BA_api_flask_blueprint.route('/download_dbase_json/<download_type>')
def download_dbase_json(download_type="full"):
    """
    Download the full Neo4j database as a JSON file

    EXAMPLES invocation:
        http://localhost:5000/BA/api/download_dbase_json/full
        http://localhost:5000/BA/api/download_dbase_json/schema

    :param download_type:   Either "full" (default) or "schema"
    :return:                A Flask response object, with HTTP headers that will initiate a download
    """
    if download_type == "full":
        ne = NodeExplorer()     # TODO: use a more direct way to get to the NeoAccess object
        result = ne.neo.export_dbase_json()
        export_filename = "exported_dbase.json"
    elif download_type == "schema":
        result = NeoSchema.export_schema()
        export_filename = "exported_schema.json"
    else:
        return f"Unknown requested type of download: {download_type}"
    # TODO: error handling

    # result is a dict with 4 keys
    print(f"Getting ready to export {result.get('nodes')} nodes, "
          f"{result.get('relationships')} relationships, and {result.get('properties')} properties")

    data = result["data"]
    response = make_response(data)
    response.headers['Content-Type'] = 'application/save'
    response.headers['Content-Disposition'] = f'attachment; filename=\"{export_filename}\"'
    return response




########################################################################
#                           EXPERIMENTAL                               #
########################################################################

@BA_api_flask_blueprint.route('/add_label/<new_label>')
def add_label(new_label) -> str:
    """
    Add a new blank node with the specified label
    EXAMPLE invocation: http://localhost:5000/api/add_label/boat
    """
    status = APIRequestHandler.add_new_label(new_label)

    if status:
        return SUCCESS_PREFIX
    else:
        return ERROR_PREFIX