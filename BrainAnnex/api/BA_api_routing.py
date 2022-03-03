from flask import Blueprint, jsonify, request, make_response  # The request package makes available a GLOBAL request object
from BrainAnnex.api.BA_api_request_handler import APIRequestHandler
from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema
from BrainAnnex.modules.node_explorer.node_explorer import NodeExplorer     # TODO: to phase out
from BrainAnnex.modules.categories.categories import Categories
import sys                  # Used to give better feedback on Exceptions
import shutil
from time import sleep      # Used for tests of delays in asynchronous fetching

"""
    MIT License.  Copyright (c) 2021-2022 Julian A. West
"""



class ApiRouting:
    """
    API endpoint
    """

    def __init__(self, media_folder, upload_folder):
        # Specify where this module's STATIC folder is located (relative to this module's main folder)
        self.BA_api_flask_blueprint = Blueprint('BA_api', __name__, static_folder='static')
        # This "Blueprint" object gets registered in the Flask app object in main.py, using: url_prefix = "/BA/api"


        ###################################################################################################################
        #                                                                                                                 #
        #   The "simple" subset of the API, with endpoints that return PLAIN text (rather than JSON or something else)    #
        #                                                                                                                 #
        ###################################################################################################################
        
        self.ERROR_PREFIX = "-"      # Prefix used in the "simple API" protocol to indicate an error in the response value;
        #       the remainder of the response string will the be understood to be the error message
        
        self.SUCCESS_PREFIX = "+"    # Prefix used in the "simple API" protocol to indicate a successful operation;
        #       the remainder of the response string will the be understood to be the optional data payload
        #       (such as a status message)
        
        # NOTE: To test POST-based API access points, on the Linux shell or Windows PowerShell issue commands such as:
        #            curl http://localhost:5000/BA/api/simple/add_item_to_category -d "schema_id=1&category_id=60"


        self.MEDIA_FOLDER = media_folder    # Location where the media for Content Items is stored
        self.UPLOAD_FOLDER = upload_folder  # Temporary location for uploads

        self.set_routing()   # Define the Flask routing (mapping URLs to Python functions)





    ###############################################
    #               UTILITY methods               #
    ###############################################

    def str_to_int(self, s: str) -> int:
        """
        Helper function to give more friendly error messages in case non-integers are passed
        in situations where they are expected (for example, for id's).
        Without this function, the user would see more cryptic messages such as
        "invalid literal for int() with base 10: 'q123'"

        :param s:
        :return:
        """
        try:
            i = int(s)
        except Exception as ex:
            raise Exception(f"The passed parameter ({s}) is not an integer as expected")

        return i



    def extract_post_pars(self, post_data, required_par_list=None) -> dict:
        """
        Convert the given POST data (an ImmutableMultiDict) into a dictionary,
        while enforcing the optional given list of parameters that must be present.
        In case of errors (or missing required parameters), an Exception is raised.

        TODO: maybe optionally pass a list of pars that must be int, and handle conversion and errors
              Example - int_pars = ['item_id']

        :param post_data:           EXAMPLE: ImmutableMultiDict([('item_id', '123'), ('rel_name', 'BA_served_at')])
        :param required_par_list:   A list or tuple.  EXAMPLE: ['item_id', 'rel_name']
        :return:                    A dict of POST data
        """
        data_dict = dict(post_data)

        if required_par_list:
            for par in required_par_list:
                assert par in data_dict, f"The expected parameter `{par}` in the POST request is missing"

        return data_dict




    ###############################################
    #               For DEBUGGING                 #
    ###############################################

    def show_post_data(self, post_data, method_name=None) -> None:
        """
        Debug utility method.  Pretty-printing for POST data

        :param post_data:   An ImmutableMultiDict, as for example returned by request.form
        :param method_name: (Optional) Name of invoking function
        :return:            None
        """
        if method_name:
            print(f"In {method_name}(). POST data: ")
        else:
            print(f"POST data: ")

        for k, v in post_data.items():
            print("    ", k , " -> " , v)   # TODO: if v is a string, put quotes around it
        print("-----------")




    ###############################################
    #                   ROUTING                   #
    ###############################################

    def set_routing(self) -> None:
        """
        Define the Flask routing (mapping of URLs to Python functions)
        for all the web pages served by this module.

        Organized in the following groups:
                * SCHEMA-related (reading)
                * SCHEMA-related (creating)
                * CONTENT-ITEM MANAGEMENT
                * CATEGORY-RELATED
                    * POSITIONING WITHIN CATEGORIES

                * FILTERS
                * IMPORT-EXPORT  (upload/download)
                * EXPERIMENTAL

        :return: None
        """
        
        #---------------------------------------------#
        #              SCHEMA-related (reading)       #
        #---------------------------------------------#

        #"@" signifies a decorator - a way to wrap a function and modify its behavior
        @self.BA_api_flask_blueprint.route('/get_properties/<schema_id>')
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



        @self.BA_api_flask_blueprint.route('/get_links/<schema_id>')
        def get_links(schema_id):
            """
            Get the names of all the relationship attached to the Class specified by its Schema ID

            EXAMPLE invocation: http://localhost:5000/BA/api/get_links/47

            :param schema_id:   ID of a Class node
            :return:            A JSON object with the names of inbound and outbound links
                                EXAMPLE:
                                    {
                                        "status": "ok",
                                        "payload": {
                                            "in": [
                                                "BA_served_at"
                                            ],
                                            "out": [
                                                "BA_located_in",
                                                "BA_cuisine_type"
                                            ]
                                        }
                                    }
            """

            # Fetch all the relationship names
            try:
                rel_names = NeoSchema.get_class_relationships(int(schema_id), omit_instance=True)
                payload = {"in": rel_names["in"], "out": rel_names["out"]}
                response = {"status": "ok", "payload": payload}    # Successful termination
            except Exception as ex:
                response = {"status": "error", "error_message": str(ex)}    # Error termination

            return jsonify(response)   # This function also takes care of the Content-Type header


        
        @self.BA_api_flask_blueprint.route('/get_properties_by_class_name', methods=['POST'])
        def get_properties_by_class_name():
            """
            Get all Properties of the given Class node (as specified by its name passed as a POST variable),
            including indirect ones thru chains of outbound "INSTANCE_OF" relationships.
            Return a JSON object with a list of the Property names of that Class.
        
            EXAMPLE invocation:
                curl http://localhost:5000/BA/api/get_properties_by_class_name  -d "class_name=French Vocabulary"
        
            1 POST FIELD:
                class_name
        
            :return:  A JSON with a list of the Property names of the specified Class,
                      including indirect ones thru chains of outbound "INSTANCE_OF" relationships
                         EXAMPLE:
                            {
                                "payload":  [
                                              "Notes",
                                              "English",
                                              "French"
                                            ],
                                "status":   "ok"
                            }
            """
        
            # Extract the POST values
            post_data = request.form     # Example: ImmutableMultiDict([('class_name', 'French Vocabulary')])
            self.show_post_data(post_data, "get_properties_by_class_name")
        
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




        @self.BA_api_flask_blueprint.route('/get_class_schema', methods=['POST'])
        def get_class_schema():
            """
            Get all Schema data - both Properties and Links - of the given Class node
            (as specified by its name passed as a POST variable),
            including indirect Properties thru chains of outbound "INSTANCE_OF" relationships.
            Return a JSON object with a list of the Property names of that Class.

            EXAMPLE invocation:
                curl http://localhost:5000/BA/api/get_class_schema  -d "class_name=Restaurants"

            1 POST FIELD:
                class_name

            :return:  A JSON with a list of the Property names of the specified Class,
                      including indirect ones thru chains of outbound "INSTANCE_OF" relationships
                         EXAMPLE:
                            {
                                "payload":  {
                                            "properties":   [
                                                              "name",
                                                              "website",
                                                              "address"
                                                            ],
                                            "in_links":     ["BA_served_at"],
                                            "out_links":    ["BA_located_in", "BA_cuisine_type"]
                                            },
                                "status":   "ok"
                            }
            """

            # Extract the POST values
            post_data = request.form     # Example: ImmutableMultiDict([('class_name', 'Restaurants')])
            self.show_post_data(post_data, "get_class_schema")

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
                        rel_names = NeoSchema.get_class_relationships(int(schema_id), omit_instance=True)
                        payload = {"properties": prop_list, "in_links": rel_names["in"], "out_links": rel_names["out"]}
                        response = {"status": "ok", "payload": payload}
                    except Exception as ex:
                        response = {"status": "error", "error_message": str(ex)}

            print(f"get_class_schema() is returning: `{response}`")

            return jsonify(response)   # This function also takes care of the Content-Type header




        @self.BA_api_flask_blueprint.route('/get_properties_by_item_id/<item_id>')
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
        

        
        @self.BA_api_flask_blueprint.route('/get_record_classes')
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




        #---------------------------------------------#
        #            SCHEMA-related (creating)        #
        #---------------------------------------------#

        @self.BA_api_flask_blueprint.route('/simple/create_new_record_class', methods=['POST'])
        def create_new_record_class():
            """
            TODO: this is a simple, interim version - to later switch to JSON

            EXAMPLES of invocation:
                curl http://localhost:5000/BA/api/simple/create_new_record_class -d "data=Quotes,quote,attribution,notes"

            1 POST FIELD:
                data    The name of the new Class, followed by the name of all desired Properties, in order
                        (all comma-separated).  Tolerant of leading/trailing blanks, and of missing property names
            """
            # Extract the POST values
            post_data = request.form     # Example: ImmutableMultiDict([('data', 'Quotes,quote,attribution,notes')])
            self.show_post_data(post_data, "create_new_record_class")

            try:
                class_specs = self.extract_post_pars(post_data, required_par_list=["data"])
                APIRequestHandler.new_record_class(class_specs)
                return_value = self.SUCCESS_PREFIX               # Success
            except Exception as ex:
                err_status = f"UNABLE TO CREATE NEW CLASS WITH PROPERTIES. {ex}"
                return_value = self.ERROR_PREFIX + err_status    # Failure

            print(f"create_new_record_class() is returning: `{return_value}`")

            return return_value



        #---------------------------------------------#
        #            CONTENT-ITEM MANAGEMENT          #
        #---------------------------------------------#


        ################   VIEWING CONTENT ITEMS   ################

        @self.BA_api_flask_blueprint.route('/simple/get_media/<item_id>')
        def get_media(item_id) -> str:
            """
            Retrieve and return the contents of a text media item (for now, just "notes"),
            including the request status
        
            EXAMPLE invocation: http://localhost:5000/BA/api/simple/get_media/123
            """
            #sleep(1)    # For debugging

            status, content = APIRequestHandler.get_content("n", int(item_id))
        
            if status is False:
                err_details = f"Unable to retrieve note id {item_id} : {content}"
                print(f"get_media() encountered the following error: {err_details}")
                return_value = self.ERROR_PREFIX + err_details
            else:
                return_value = self.SUCCESS_PREFIX + content
                #print(f"get_media() is returning the following text [first 30 chars]: `{return_value[:30]}`")
        
            return return_value



        @self.BA_api_flask_blueprint.route('/simple/serve_media/<item_id>')
        @self.BA_api_flask_blueprint.route('/simple/serve_media/<item_id>/<th>')
        def serve_media(item_id, th=None):
            """
            Retrieve and return the contents of a data media item (for now, just images or documents)
            If ANY value is specified for the argument "th", then the thumbnail version is returned

            TODO: (at least for large media) read the file in blocks.

            EXAMPLE invocation: http://localhost:5000/BA/api/simple/serve_media/1234
            """
            mime_mapping = {'jpg': 'image/jpeg',
                            'png': 'image/png',
                            'gif': 'image/gif',
                            'bmp': 'image/bmp',
                            'svg': 'image/svg+xml',

                            'txt': 'text/plain',
                            'pdf': 'application/pdf',
                            'docx': 'application/msword',
                            'doc': 'application/msword',
                            'xlsx': 'application/vnd.ms-excel',
                            'xls': 'application/vnd.ms-excel',

                            'zip': 'application/zip'
                            }   # TODO: add more MIME types, when more plugins are introduced, and move to APIRequestHandler

            default_mime = 'application/save'   # TODO: not sure if this is the best default. Test!

            try:
                (suffix, content) = APIRequestHandler.get_binary_content(int(item_id), th)
                response = make_response(content)
                # set the MIME type
                mime_type = mime_mapping.get(suffix.lower(), default_mime)
                response.headers['Content-Type'] = mime_type
                #print(f"serve_media() is returning an image, with file suffix `{suffix}`.  Serving with MIME type `{mime_type}`")
            except Exception as ex:
                err_details = f"Unable to retrieve image id `{item_id}` : {ex}"
                print(f"serve_media() encountered the following error: {err_details}")
                response = make_response(err_details, 500)

            return response



        @self.BA_api_flask_blueprint.route('/get_link_summary/<item_id_str>')
        def get_link_summary_api(item_id_str) -> str:
            """
            Return a JSON structure identifying the names and counts of all
            inbound and outbound links to/from the given data node.

            This is approximately the data-node counterpart of the schema API 'get_links'

            EXAMPLE invocation: http://localhost:5000/BA/api/get_link_summary/47

            :param item_id_str: ID of a data node
            :return:            A JSON object with the names and counts of inbound and outbound links
                                EXAMPLE:
                                    {
                                        "status": "ok",
                                        "payload": {
                                            "in": [
                                                ["BA_served_at", 1]
                                            ],
                                            "out": [
                                                ["BA_located_in", 1],
                                                ["BA_cuisine_type", 2]
                                            ]
                                        }
                                    }
            """
            try:
                item_id = self.str_to_int(item_id_str)
                payload = APIRequestHandler.get_link_summary(item_id, omit_names = ['BA_in_category'])
                response = {"status": "ok", "payload": payload}             # Successful termination
            except Exception as ex:
                response = {"status": "error", "error_message": str(ex)}    # Error termination

            return jsonify(response)   # This function also takes care of the Content-Type header



        @self.BA_api_flask_blueprint.route('/get_records_by_link', methods=['POST'])
        def get_records_by_link_api() -> str:
            """
            Locate and return the data of the nodes linked to the one specified by item_id,
            by the relationship named by rel_name, in the direction specified by dir
            EXAMPLE invocation:
                curl http://localhost:5000/BA/api/get_records_by_link -d "item_id=123&rel_name=BA_served_at&dir=IN"
            """
            # Extract the POST values
            post_data = request.form
            # EXAMPLE: ImmutableMultiDict([('item_id', '123'), ('rel_name', 'BA_served_at'), ('dir', 'IN')])
            self.show_post_data(post_data)

            try:
                data_dict = self.extract_post_pars(post_data, required_par_list=['item_id', 'rel_name', 'dir'])
                data_dict["item_id"] = self.str_to_int(data_dict["item_id"])
                payload = APIRequestHandler.get_records_by_link(data_dict)
                response = {"status": "ok", "payload": payload}             # Successful termination
            except Exception as ex:
                response = {"status": "error", "error_message": str(ex)}    # Error termination

            return jsonify(response)   # This function also takes care of the Content-Type header




        ################   MODIFYING EXISTING CONTENT ITEMS   ################

        @self.BA_api_flask_blueprint.route('/simple/update', methods=['POST'])
        def update() -> str:
            """
            Update an existing Content Item.
            NOTE: the "schema_code" field is currently required, but it's redundant.  Only
                  used as a safety mechanism against incorrect values of item_id

            EXAMPLES of invocation:
                curl http://localhost:5000/BA/api/simple/update -d "item_id=11&schema_code=h&text=my_header"
                curl http://localhost:5000/BA/api/simple/update -d "item_id=62&schema_code=r&English=Love&German=Liebe"
            """
            # Extract the POST values
            post_data = request.form    # Example: ImmutableMultiDict([('item_id', '11'), ('schema_code', 'r')])
            self.show_post_data(post_data, "update")

            try:
                data_dict = self.extract_post_pars(post_data, required_par_list=['item_id'])
                APIRequestHandler.update_content_item(data_dict)
                return_value = self.SUCCESS_PREFIX              # If no errors
            except Exception as ex:
                return_value = self.ERROR_PREFIX + str(ex)      # In case of errors
        
            print(f"update() is returning: `{return_value}`")
        
            return return_value
        
        
        
        @self.BA_api_flask_blueprint.route('/simple/delete/<item_id>/<schema_code>')
        def delete(item_id, schema_code) -> str:
            """
            Delete the specified Content Item.
            Note that schema_code is redundant.
            EXAMPLE invocation: http://localhost:5000/BA/api/simple/delete/46/n
            """
            err_status = APIRequestHandler.delete_content_item(item_id, schema_code)
        
            if err_status == "":    # If no errors
                return_value = self.SUCCESS_PREFIX
            else:                   # If errors
                return_value = self.ERROR_PREFIX + err_status
        
            print(f"delete() is returning: `{return_value}`")
        
            return return_value




        #---------------------------------------------#
        #               CATEGORY-RELATED              #
        #---------------------------------------------#
        
        @self.BA_api_flask_blueprint.route('/simple/add_item_to_category', methods=['POST'])
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
            self.show_post_data(post_data, "add_item_to_category")
        
            # Create a new Content Item with the POST data
            try:
                new_id = APIRequestHandler.new_content_item_in_category(dict(post_data))
                return_value = self.SUCCESS_PREFIX + str(new_id)     # Include the newly-added ID as a payload
            except Exception as ex:
                return_value = self.ERROR_PREFIX + APIRequestHandler.exception_helper(ex)
        
            print(f"add_item_to_category() is returning: `{return_value}`")
        
            return return_value
        
        
        
        @self.BA_api_flask_blueprint.route('/simple/add_subcategory', methods=['POST'])
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
                return_value = self.SUCCESS_PREFIX + str(new_id)     # Include the newly-added ID as a payload
            except Exception as ex:
                return_value = self.ERROR_PREFIX + APIRequestHandler.exception_helper(ex)
        
            print(f"add_subcategory() is returning: `{return_value}`")
        
            return return_value
        
        
        
        @self.BA_api_flask_blueprint.route('/simple/delete_category/<category_id>')
        def delete_category(category_id) -> str:
            """
            Delete the specified Category, provided that there are no Content Items linked to it
            EXAMPLE invocation: http://localhost:5000/BA/api/simple/delete_category/123
            """
            try:
                Categories.delete_category(int(category_id))
                return_value = self.SUCCESS_PREFIX
            except Exception as ex:
                return_value = self.ERROR_PREFIX + APIRequestHandler.exception_helper(ex)
        
            print(f"delete_category() is returning: `{return_value}`")
        
            return return_value
        
        
        
        @self.BA_api_flask_blueprint.route('/simple/add_subcategory_relationship')
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
                return_value = self.SUCCESS_PREFIX
            except Exception as ex:
                return_value = self.ERROR_PREFIX + APIRequestHandler.exception_helper(ex)
        
            print(f"add_subcategory_relationship() is returning: `{return_value}`")
        
            return return_value
        
        
        @self.BA_api_flask_blueprint.route('/simple/remove_subcategory_relationship')
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
                return_value = self.SUCCESS_PREFIX
            except Exception as ex:
                return_value = self.ERROR_PREFIX + APIRequestHandler.exception_helper(ex)
        
            print(f"remove_subcategory_relationship() is returning: `{return_value}`")
        
            return return_value
        
        
        
        
        #############    POSITIONING WITHIN CATEGORIES    #############
        
        @self.BA_api_flask_blueprint.route('/simple/swap/<item_id_1>/<item_id_2>/<cat_id>')
        def swap(item_id_1, item_id_2, cat_id) -> str:
            """
            Swap the positions of the specified Content Items within the given Category.
        
            EXAMPLE invocation: http://localhost:5000/BA/api/simple/swap/23/45/2
            """
            err_status:str = Categories.swap_content_items(item_id_1, item_id_2, cat_id)
        
            if err_status == "":    # If no errors
                return_value = self.SUCCESS_PREFIX
            else:                   # If errors
                return_value = self.ERROR_PREFIX + err_status
        
            print(f"swap() is returning: `{return_value}`")
        
            return return_value
        
        
        
        @self.BA_api_flask_blueprint.route('/simple/reposition/<category_id>/<item_id>/<move_after_n>')
        def reposition(category_id, item_id, move_after_n) -> str:
            """
            Reposition the given Content Item after the n-th item (counting starts with 1) in specified Category.
            TODO: switch to an after-item version?
        
            EXAMPLE invocation: http://localhost:5000/BA/api/simple/reposition/60/576/4
            """
            try:
                Categories.reposition_content(category_id=int(category_id), item_id=int(item_id), move_after_n=int(move_after_n))
                return_value = self.SUCCESS_PREFIX               # Success
            except Exception as ex:
                err_status = f"UNABLE TO REPOSITION ELEMENT: {ex}"
                return_value = self.ERROR_PREFIX + err_status    # Failure
        
            print(f"reposition() is returning: `{return_value}`")
        
            return return_value




        #---------------------------------------------#
        #                   FILTERS                   #
        #---------------------------------------------#
        
        @self.BA_api_flask_blueprint.route('/get-filtered-json', methods=['POST'])
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
        
        
        
        @self.BA_api_flask_blueprint.route('/get_filtered', methods=['POST'])
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
            self.show_post_data(post_data, "get_filtered")
        
            try:
                result = APIRequestHandler.get_nodes_by_filter(dict(post_data))
                response = {"status": "ok", "payload": result}              # Successful termination
            except Exception as ex:
                response = {"status": "error", "error_message": str(ex)}    # Error termination
        
            print(f"get_filtered() is returning: `{response}`")
        
            return jsonify(response)        # This function also takes care of the Content-Type header




        #---------------------------------------------#
        #       IMPORT-EXPORT  (upload/download)      #
        #---------------------------------------------#
        
        @self.BA_api_flask_blueprint.route('/import_json_file', methods=['GET', 'POST'])
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
        
        
        
        @self.BA_api_flask_blueprint.route('/upload_media', methods=['POST'])
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
        
            src_fullname = self.UPLOAD_FOLDER + tmp_filename_for_upload
            dest_folder = self.MEDIA_FOLDER
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
        
        
        
        @self.BA_api_flask_blueprint.route('/upload_file', methods=['POST'])
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
        
        
        
        @self.BA_api_flask_blueprint.route('/parse_datafile', methods=['GET', 'POST'])
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
        
        
        
        @self.BA_api_flask_blueprint.route('/download_dbase_json/<download_type>')
        def download_dbase_json(download_type="full"):
            """
            Download the full Neo4j database as a JSON file
        
            EXAMPLES invocation:
                http://localhost:5000/BA/api/download_dbase_json/full
                http://localhost:5000/BA/api/download_dbase_json/schema
        
            :param download_type:   Either "full" (default) or "schema"
            :return:                A Flask response object, with HTTP headers that will initiate a download
            """
            try:
                if download_type == "full":
                    ne = NodeExplorer()     # TODO: use a more direct way to get to the NeoAccess object;
                                            #       this part of the code belongs in  APIRequestHandler
                    result = ne.neo.export_dbase_json()
                    export_filename = "exported_dbase.json"
                elif download_type == "schema":
                    result = NeoSchema.export_schema()
                    export_filename = "exported_schema.json"
                else:
                    return f"Unknown requested type of download: {download_type}"
            except Exception as ex:
                    response = APIRequestHandler.exception_helper(ex, safe_html=True)
                    error_page_body = f'''<b>Unable to perform download</b>. <br>
                                          This is typically due to the 'APOC' library not being installed on Neo4j. 
                                          Contact your Neo4j database administrator.
                                          <br><br>{response}"
                                       '''
                    return error_page_body
                    # TODO: have a special page to display errors like this one
        
            # result is a dict with 4 keys
            print(f"Getting ready to export {result.get('nodes')} nodes, "
                  f"{result.get('relationships')} relationships, and {result.get('properties')} properties")
        
            data = result["data"]
            response = make_response(data)
            response.headers['Content-Type'] = 'application/save'
            response.headers['Content-Disposition'] = f'attachment; filename=\"{export_filename}\"'
            return response




        #---------------------------------------------#
        #                EXPERIMENTAL                 #
        #---------------------------------------------#
        
        @self.BA_api_flask_blueprint.route('/add_label/<new_label>')
        def add_label(new_label) -> str:
            """
            Add a new blank node with the specified label
            EXAMPLE invocation: http://localhost:5000/api/add_label/boat
            """
            status = APIRequestHandler.add_new_label(new_label)
        
            if status:
                return self.SUCCESS_PREFIX
            else:
                return self.ERROR_PREFIX
