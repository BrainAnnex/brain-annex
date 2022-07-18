"""
    API endpoint
    MIT License.  Copyright (c) 2021-2022 Julian A. West
"""

from flask import Blueprint, jsonify, request, current_app, make_response  # The request package makes available a GLOBAL request object
from flask_login import login_required
from BrainAnnex.api.BA_api_request_handler import APIRequestHandler
from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema
from BrainAnnex.modules.node_explorer.node_explorer import NodeExplorer     # TODO: to phase out
from BrainAnnex.modules.categories.categories import Categories
from BrainAnnex.modules.upload_helper.upload_helper import UploadHelper, ImageProcessing
import sys                  # Used to give better feedback on Exceptions
import shutil
#from time import sleep     # Used for tests of delays in asynchronous fetching



class ApiRouting:
    """
    Setup, routing and endpoints for all the web pages served by this module.
    Note that this class does not directly interact with the Neo4j database.

    SECTIONS:
        - UTILITY methods
        - For DEBUGGING
        - ROUTING:
            * SCHEMA-related (reading)
            * SCHEMA-related (creating)
            * CONTENT-ITEM MANAGEMENT
                VIEWING CONTENT ITEMS
                MODIFYING EXISTING CONTENT ITEMS
            * CATEGORY-RELATED (incl. adding new Content Items)
                POSITIONING WITHIN CATEGORIES
            * FILTERS
            * IMPORT-EXPORT  (upload/download)
            * EXPERIMENTAL
    """

    # Module-specific parameters (as class variables)
    blueprint_name = "BA_api"           # Name unique to this module
    url_prefix = "/BA/api"              # Prefix for all URL's handled by this module
    template_folder = "templates"       # Relative to this module's location
    static_folder = "static"            # Relative to this module's location

    MEDIA_FOLDER = None                 # Location where the media for Content Items is stored
    UPLOAD_FOLDER = None                # Temporary location for uploads

    debug = False                       # Flag indicating whether a debug mode is to be used by all methods of this class
                                        #       (currently, in very limited use)

    #######################################################################################################################
    #                                                                                                                     #
    #   ERROR_PREFIX and SUCCESS_PREFIX:                                                                                  #
    #   used for "simple" subset of the API, with endpoints that return PLAIN text (rather than JSON or something else)   #
    #                                                                                                                     #
    #######################################################################################################################

    ERROR_PREFIX = "-"      # Prefix used in the "simple API" protocol to indicate an error in the response value;
    #       the remainder of the response string will the be understood to be the error message

    SUCCESS_PREFIX = "+"    # Prefix used in the "simple API" protocol to indicate a successful operation;
    #       the remainder of the response string will the be understood to be the optional data payload
    #       (such as a status message)

    # NOTE: To test POST-based API access points, on the Linux shell or Windows PowerShell issue commands such as:
    #            curl http://localhost:5000/BA/api/simple/add_item_to_category -d "schema_id=1&category_id=60"




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




    ###############################################
    #               UTILITY methods               #
    ###############################################

    @classmethod
    def str_to_int(cls, s: str) -> int:
        """
        Helper function to give more friendly error messages in case non-integers are passed
        in situations where integers are expected (for example, for id's).
        Without this function, the user would see cryptic messages such as
        "invalid literal for int() with base 10: 'q123'"

        EXAMPLE:
            try:
                item_id = cls.str_to_int(item_id_str)
            except Exception as ex:
                # Do something

        :param s:   A string that should represent an integer
        :return:    The integer represented in the passed string, if applicable;
                        if not, an Exception is raised
        """
        try:
            i = int(s)
        except Exception:
            raise Exception(f"The passed parameter ({s}) is not an integer as expected")

        return i



    @classmethod
    def extract_post_pars(cls, post_data, required_par_list=None) -> dict:
        """
        Convert into a Python dictionary the given POST data
        (expressed as an ImmutableMultiDict) - ASSUMED TO HAVE UNIQUE KEYS -
        while enforcing the optional given list of parameters that must be present.
        In case of errors (or missing required parameters), an Exception is raised.

        EXAMPLE:
                post_data = request.form
                post_pars = cls.extract_post_pars(post_data, "name_of_calling_functions")

        TODO: maybe optionally pass a list of pars that must be int, and handle conversion and errors
              Example - int_pars = ['item_id']

        TODO: merge with UploadHelper.get_form_data()

        :param post_data:           An ImmutableMultiDict object, which is a sub-class of Dictionary
                                    that can contain multiple values for the same key.
                                    EXAMPLE: ImmutableMultiDict([('item_id', '123'), ('rel_name', 'BA_served_at')])

        :param required_par_list:   A list or tuple.  EXAMPLE: ['item_id', 'rel_name']
        :return:                    A dict populated with the POST data
        """
        data_dict = post_data.to_dict(flat=True)    # WARNING: if multiple identical keys occur,
                                                    #          the values associated to the later keys will be discarded

        if required_par_list:
            for par in required_par_list:
                assert par in data_dict, f"The expected parameter `{par}` is missing from the POST request"

        return data_dict




    ###############################################
    #               For DEBUGGING                 #
    ###############################################

    @classmethod
    def show_post_data(cls, post_data, method_name=None) -> None:
        """
        Debug utility method.  Pretty-printing for POST data (expressed as an ImmutableMultiDict)
        Long values are shown in abridged form

        EXAMPLE:
                post_data = request.form
                cls.show_post_data(post_data, "name_of_calling_functions")

        :param post_data:   An ImmutableMultiDict, as for example returned by request.form
        :param method_name: (Optional) Name of invoking function
        :return:            None
        """
        if method_name:
            print(f"In {method_name}(). POST data: ")
        else:
            print(f"POST data: ")

        max_length = 100
        for k, v in post_data.items():
            # Show an abridged (if appropriate) version of the value
            if len(v) > max_length:
                v_print = v[:max_length] + " ..."
            else:
                v_print = v

            print("    ", k , " -> " , v_print)
        print("-----------")




    #############################################################
    #                           ROUTING                         #
    #############################################################

    @classmethod
    def set_routing(cls, bp) -> None:
        """
        Define the Flask routing (mapping URLs to Python functions)
        for all the web pages served by this module,
        and provide the functions assigned to the various URL endpoints

        Organized in the following groups:
                * SCHEMA-related (reading)
                * SCHEMA-related (creating)
                * CONTENT-ITEM MANAGEMENT
                * CATEGORY-RELATED
                    * POSITIONING WITHIN CATEGORIES

                * FILTERS
                * IMPORT-EXPORT  (upload/download)
                * EXPERIMENTAL
                
        :param bp:  The Flask "Blueprint" object that was created for this module
        :return:    None
        """

        ##################  START OF ROUTING DEFINITIONS  ##################
        
        #---------------------------------------------#
        #              SCHEMA-related (reading)       #
        #---------------------------------------------#

        #"@" signifies a decorator - a way to wrap a function and modify its behavior
        @bp.route('/get_properties_by_class_name', methods=['POST'])
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
            cls.show_post_data(post_data, "get_properties_by_class_name")

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



        @bp.route('/get_properties/<schema_id>')
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



        @bp.route('/get_links/<schema_id>')
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



        @bp.route('/get_class_schema', methods=['POST'])
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
            cls.show_post_data(post_data, "get_class_schema")

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



        @bp.route('/get_record_classes')
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



        @bp.route('/get_properties_by_item_id/<item_id>')
        def get_properties_by_item_id(item_id):
            """
            Get all properties of a DATA node specified by item_id

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




        #------------------------------------------------------#
        #        SCHEMA-related (creating/editing/deleting)    #
        #------------------------------------------------------#

        @bp.route('/simple/create_new_schema_class', methods=['POST'])
        @login_required
        def create_new_schema_class() -> str:
            """
            Create a new Schema Class, possibly linked to another existing class,
            and also - typically but optionally - with the special "INSTANCE_OF" link
            to an existing Class (often, the "Records" Class)

            EXAMPLES of invocation:
                curl http://localhost:5000/BA/api/simple/create_new_schema_class -d
                    "new_class_name=my%20new%20class&properties_list=A,B,C,&instance_of=Records"

                curl http://localhost:5000/BA/api/simple/create_new_schema_class -d
                    "new_class_name=Greek&properties_list=Greek,&instance_of=Foreign%20Vocabulary"

                curl http://localhost:5000/BA/api/simple/create_new_schema_class -d
                    "new_class_name=Entrees&properties_list=name,price,&instance_of=Records&linked_to=Restaurants&rel_name=served_at&rel_dir=OUT"

            POST FIELDS:
                new_class_name      The name of the new Class (tolerant of leading/trailing blanks)
                properties_list     The name of all desired Properties, in order
                                    (all comma-separated).  Tolerant of leading/trailing blanks, and of missing property names
                instance_of         Typically, "Records"

                [ALL THE REMAINING FIELDS ARE OPTIONAL]
                linked_to           The name of an existing Class node, to link to
                rel_name            The name to give to the above relationship
                rel_dir             The relationship direction, from the point of view of the newly-added node
            """
            # Extract the POST values
            post_data = request.form     # Example: ImmutableMultiDict([('data', 'Quotes,quote,attribution,notes')])
            cls.show_post_data(post_data, "create_new_schema_class")

            try:
                class_specs = cls.extract_post_pars(post_data, required_par_list=["new_class_name"])
                APIRequestHandler.new_schema_class(class_specs)
                return_value = cls.SUCCESS_PREFIX               # Success
            except Exception as ex:
                err_status = f"Unable to create a new Schema Class. {ex}"
                return_value = cls.ERROR_PREFIX + err_status    # Failure

            print(f"create_new_schema_class() is returning: `{return_value}`")

            return return_value



        @bp.route('/simple/add_schema_relationship', methods=['POST'])
        @login_required
        def add_schema_relationship() -> str:
            """
            Add a relationship with the specified name between 2 existing Classes

            POST FIELDS:
                from_class_name
                to_class_name
                rel_name

            EXAMPLE of invocation:
                curl http://localhost:5000/BA/api/simple/add_schema_relationship -d
                        "from_class_name=some_class_1&to_class_name=some_class_2&rel_name=CONNECTED_TO"
            """
            # Extract the POST values
            post_data = request.form     # An ImmutableMultiDict object
            cls.show_post_data(post_data, "add_schema_relationship")

            try:
                class_specs = cls.extract_post_pars(post_data, required_par_list=["from_class_name", "to_class_name", "rel_name"])
                APIRequestHandler.add_schema_relationship_handler(class_specs)
                return_value = cls.SUCCESS_PREFIX               # Success
            except Exception as ex:
                err_status = f"Unable to add a new relationship. {ex}"
                return_value = cls.ERROR_PREFIX + err_status    # Failure

            print(f"add_schema_relationship() is returning: `{return_value}`")

            return return_value



        @bp.route('/simple/delete_schema_relationship', methods=['POST'])
        @login_required
        def delete_schema_relationship() -> str:
            """
            Delete the relationship with the specified name between 2 existing Classes
            POST FIELDS:
                from_class_name
                to_class_name
                rel_name

            EXAMPLE of invocation:
                curl http://localhost:5000/BA/api/simple/delete_schema_relationship -d
                        "from_class_name=some_class_1&to_class_name=some_class_2&rel_name=CONNECTED_TO"
            """
            # Extract the POST values
            post_data = request.form     # An ImmutableMultiDict object
            cls.show_post_data(post_data, "delete_schema_relationship")

            try:
                class_specs = cls.extract_post_pars(post_data, required_par_list=["from_class_name", "to_class_name", "rel_name"])
                APIRequestHandler.delete_schema_relationship_handler(class_specs)
                return_value = cls.SUCCESS_PREFIX               # Success
            except Exception as ex:
                err_status = f"Unable to delete the relationship. {ex}"
                return_value = cls.ERROR_PREFIX + err_status    # Failure

            if cls.debug:
                print(f"delete_schema_relationship() is returning: `{return_value}`")

            return return_value



        @bp.route('/simple/delete_class', methods=['POST'])
        @login_required
        def delete_class() -> str:
            """
            Delete the specified Class.
            The operation will fail if the Class doesn't exist,
            or if data nodes attached to that Class are present (those need to be deleted first)

            POST FIELDS:
                class_name

            EXAMPLE of invocation:
                curl http://localhost:5000/BA/api/simple/delete_class -d
                        "class_name=some_class_1"
            """
            # Extract the POST values
            post_data = request.form     # An ImmutableMultiDict object
            cls.show_post_data(post_data, "delete_class")

            try:
                pars_dict = cls.extract_post_pars(post_data, required_par_list=["class_name"])
                NeoSchema.delete_class(name=pars_dict["class_name"], safe_delete=True)
                return_value = cls.SUCCESS_PREFIX               # Success
            except Exception as ex:
                # TODO: in case of failure, investigate further the problem
                #       (e.g. no class by that name vs. class has data points still attached to it)
                #       and give a more specific error message
                err_status = f"Unable to delete the class. {ex}"
                return_value = cls.ERROR_PREFIX + err_status    # Failure

            #if cls.debug:
            print(f"delete_class() is returning: `{return_value}`")

            return return_value




        #---------------------------------------------#
        #            CONTENT-ITEM MANAGEMENT          #
        #---------------------------------------------#


        ################   VIEWING CONTENT ITEMS   ################

        @bp.route('/simple/get_media/<item_id_str>')
        @login_required
        def get_media(item_id_str) -> str:
            """
            Retrieve and return the contents of a text media item (for now, just "notes"),
            including the request status
        
            EXAMPLE invocation: http://localhost:5000/BA/api/simple/get_media/123
            """
            #sleep(1)    # For debugging

            try:
                item_id = int(item_id_str)
                payload = APIRequestHandler.get_text_media_content(item_id, "n")
                response = cls.SUCCESS_PREFIX + payload
            except Exception as ex:
                err_details = f"Unable to retrieve the requested note: {ex}"
                print(f"get_media() encountered the following error: {err_details}")
                response = cls.ERROR_PREFIX + err_details

                #print(f"get_media() is returning the following text [first 30 chars]: `{response[:30]}`")
        
            return response



        @bp.route('/simple/remote_access_note/<item_id_str>')
        def remote_access_note(item_id_str) -> str:     # NO LOGIN REQUIRED
            """
            Similar to get_media(), but:
                1) no login required
                2) specifically for notes
                3) it only serves items marked as "public"

            EXAMPLE invocation: http://localhost:5000/BA/api/simple/remote_access_note/123
            """

            try:
                item_id = int(item_id_str)
                payload = APIRequestHandler.get_text_media_content(item_id, "n", public_required=True)

                text_response = cls.SUCCESS_PREFIX + payload
                response = make_response(text_response)
                response.headers['Access-Control-Allow-Origin'] = '*'   # This will send the header line: "Access-Control-Allow-Origin: *"
                                                                        # without it, web clients on other domains won't be able to use the payload!
                                                                        # An alternative to '*' would be a site name, such as  'https://foo.example'

            except Exception as ex:
                err_details = f"Unable to retrieve the requested note: {ex}"
                print(f"remote_access_note() encountered the following error: {err_details}")
                response = cls.ERROR_PREFIX + err_details

            #print(f"remote_access_note() is returning the following text [first 30 chars]: `{response[:30]}`")

            return response



        @bp.route('/simple/serve_media/<item_id>')
        @bp.route('/simple/serve_media/<item_id>/<th>')
        @login_required
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



        @bp.route('/get_link_summary/<item_id_str>')
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
                item_id = cls.str_to_int(item_id_str)
                payload = APIRequestHandler.get_link_summary(item_id, omit_names = ['BA_in_category'])
                response = {"status": "ok", "payload": payload}             # Successful termination
            except Exception as ex:
                response = {"status": "error", "error_message": str(ex)}    # Error termination

            return jsonify(response)   # This function also takes care of the Content-Type header



        @bp.route('/get_records_by_link', methods=['POST'])
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
            cls.show_post_data(post_data)

            try:
                data_dict = cls.extract_post_pars(post_data, required_par_list=['item_id', 'rel_name', 'dir'])
                data_dict["item_id"] = cls.str_to_int(data_dict["item_id"])
                payload = APIRequestHandler.get_records_by_link(data_dict)
                response = {"status": "ok", "payload": payload}             # Successful termination
            except Exception as ex:
                response = {"status": "error", "error_message": str(ex)}    # Error termination

            return jsonify(response)   # This function also takes care of the Content-Type header




        ################   MODIFYING EXISTING CONTENT ITEMS   ################

        @bp.route('/simple/update', methods=['POST'])
        @login_required
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
            cls.show_post_data(post_data, "update")

            try:
                data_dict = cls.extract_post_pars(post_data, required_par_list=['item_id'])
                APIRequestHandler.update_content_item(data_dict)
                return_value = cls.SUCCESS_PREFIX              # If no errors
            except Exception as ex:
                return_value = cls.ERROR_PREFIX + str(ex)      # In case of errors
        
            print(f"update() is returning: `{return_value}`")
        
            return return_value
        
        
        
        @bp.route('/simple/delete/<item_id>/<schema_code>')
        @login_required
        def delete(item_id, schema_code) -> str:
            """
            Delete the specified Content Item.
            Note that schema_code is redundant.
            EXAMPLE invocation: http://localhost:5000/BA/api/simple/delete/46/n
            """
            err_status = APIRequestHandler.delete_content_item(item_id, schema_code)
        
            if err_status == "":    # If no errors
                return_value = cls.SUCCESS_PREFIX
            else:                   # If errors
                return_value = cls.ERROR_PREFIX + err_status
        
            print(f"delete() is returning: `{return_value}`")
        
            return return_value




        #-----------------------------------------------------------------#
        #         CATEGORY-RELATED  (incl. adding new Content Items)      #
        #-----------------------------------------------------------------#
        
        @bp.route('/simple/add_item_to_category', methods=['POST'])
        @login_required
        def add_item_to_category() -> str:
            """
            Create a new Content Item attached to a particular Category,
            at a particular location in the "collection" (page)

            EXAMPLE invocation:
            curl http://localhost:5000/BA/api/simple/add_item_to_category
                            -d "category_id=708&insert_after=711&schema_code=h&text=New Header"
        
            POST FIELDS:
                category_id         Integer identifying the Category to which attach the new Content Item
                schema_code         A string to identify the Schema that the new Content Item belongs to
                insert_after        Either an item_id (int), or one of the special values "TOP" or "BOTTOM"
                PLUS any applicable plugin-specific fields
            """
            # Extract the POST values
            post_data = request.form
            # Example: ImmutableMultiDict([('category_id', '123'), ('schema_code', 'h'), ('insert_after', '5'), ('text', 'My Header')])
            cls.show_post_data(post_data, "add_item_to_category")
        
            # Create a new Content Item with the POST data
            try:
                pars_dict = cls.extract_post_pars(post_data, required_par_list=['category_id', 'schema_code', 'insert_after'])
                new_id = APIRequestHandler.new_content_item_in_category(pars_dict)
                return_value = cls.SUCCESS_PREFIX + str(new_id)     # Include the newly-added ID as a payload
            except Exception as ex:
                return_value = cls.ERROR_PREFIX + APIRequestHandler.exception_helper(ex)
        
            print(f"add_item_to_category() is returning: `{return_value}`")
        
            return return_value
        
        
        
        @bp.route('/simple/add_subcategory', methods=['POST'])
        @login_required
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
                return_value = cls.SUCCESS_PREFIX + str(new_id)     # Include the newly-added ID as a payload
            except Exception as ex:
                return_value = cls.ERROR_PREFIX + APIRequestHandler.exception_helper(ex)
        
            print(f"add_subcategory() is returning: `{return_value}`")
        
            return return_value
        
        
        
        @bp.route('/simple/delete_category/<category_id>')
        @login_required
        def delete_category(category_id) -> str:
            """
            Delete the specified Category, provided that there are no Content Items linked to it
            EXAMPLE invocation: http://localhost:5000/BA/api/simple/delete_category/123
            """
            try:
                Categories.delete_category(int(category_id))
                return_value = cls.SUCCESS_PREFIX
            except Exception as ex:
                return_value = cls.ERROR_PREFIX + APIRequestHandler.exception_helper(ex)
        
            print(f"delete_category() is returning: `{return_value}`")
        
            return return_value
        
        
        
        @bp.route('/simple/add_subcategory_relationship')
        # TODO: phase out in favor of the more general /simple/add_relationship
        @login_required
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
                return_value = cls.SUCCESS_PREFIX
            except Exception as ex:
                return_value = cls.ERROR_PREFIX + APIRequestHandler.exception_helper(ex)
        
            print(f"add_subcategory_relationship() is returning: `{return_value}`")
        
            return return_value



        @bp.route('/simple/remove_relationship', methods=['POST'])
        @login_required
        def remove_relationship() -> str:
            """
            Remove the specified relationship (edge)

            POST FIELDS:
                from                    The item_id of the node from which the relationship originates
                to                      The item_id of the node into which the relationship takes
                rel_name                The name of the relationship to remove
                schema_code (optional)  If passed, the appropriate plugin gets invoked
            :return:
            """
            # Extract the POST values
            post_data = request.form
            # EXAMPLE: ImmutableMultiDict([('from', '123'), ('to', '88'), ('rel_name', 'BA_subcategory_of'), ('schema_code', 'cat')])
            cls.show_post_data(post_data)

            try:
                data_dict = cls.extract_post_pars(post_data, required_par_list=['from', 'to', 'rel_name'])
                from_id = cls.str_to_int(data_dict['from'])
                to_id = cls.str_to_int(data_dict['to'])
                rel_name = data_dict['rel_name']
                schema_code = data_dict.get('schema_code')         # Tolerant of missing values

                if schema_code == "cat":
                    Categories.remove_relationship(from_id=from_id, to_id=to_id,
                                                   rel_name=rel_name)       # Category-specific action

                NeoSchema.remove_data_relationship(from_id=from_id, to_id=to_id,
                                                   rel_name=rel_name, labels="BA")

                return_value = cls.SUCCESS_PREFIX              # If no errors
            except Exception as ex:
                return_value = cls.ERROR_PREFIX + APIRequestHandler.exception_helper(ex)   # In case of errors

            print(f"remove_relationship() is returning: `{return_value}`")

            return return_value


        @bp.route('/simple/add_relationship', methods=['POST'])
        @login_required
        def add_relationship() -> str:
            """
            Add the specified relationship (edge)

            POST FIELDS:
                from                    The item_id of the node from which the relationship originates
                to                      The item_id of the node into which the relationship takes
                rel_name                The name of the relationship to add
                schema_code (optional)  If passed, the appropriate plugin gets invoked
            :return:
            """
            # Extract the POST values
            post_data = request.form
            # EXAMPLE: ImmutableMultiDict([('from', '123'), ('to', '88'), ('rel_name', 'BA_subcategory_of'), ('schema_code', 'cat')])
            cls.show_post_data(post_data)

            try:
                data_dict = cls.extract_post_pars(post_data, required_par_list=['from', 'to', 'rel_name'])
                from_id = cls.str_to_int(data_dict['from'])
                to_id = cls.str_to_int(data_dict['to'])
                rel_name = data_dict['rel_name']
                schema_code = data_dict.get('schema_code')         # Tolerant of missing values

                if schema_code == "cat":
                    Categories.add_relationship(from_id=from_id, to_id=to_id,
                                                rel_name=rel_name)       # Category-specific action

                NeoSchema.add_data_relationship(from_id=from_id, to_id=to_id,
                                                rel_name=rel_name, id_type="item_id")

                return_value = cls.SUCCESS_PREFIX              # If no errors
            except Exception as ex:
                return_value = cls.ERROR_PREFIX + APIRequestHandler.exception_helper(ex)   # In case of errors

            print(f"add_relationship() is returning: `{return_value}`")

            return return_value



        #############    POSITIONING WITHIN CATEGORIES    #############
        
        @bp.route('/simple/swap/<item_id_1>/<item_id_2>/<cat_id>')
        @login_required
        def swap(item_id_1, item_id_2, cat_id) -> str:
            """
            Swap the positions of the specified Content Items within the given Category.
        
            EXAMPLE invocation: http://localhost:5000/BA/api/simple/swap/23/45/2
            """
            err_status:str = Categories.swap_content_items(item_id_1, item_id_2, cat_id)
        
            if err_status == "":    # If no errors
                return_value = cls.SUCCESS_PREFIX
            else:                   # If errors
                return_value = cls.ERROR_PREFIX + err_status
        
            print(f"swap() is returning: `{return_value}`")
        
            return return_value
        
        
        
        @bp.route('/simple/reposition/<category_id>/<item_id>/<move_after_n>')
        @login_required
        def reposition(category_id, item_id, move_after_n) -> str:
            """
            Reposition the given Content Item after the n-th item (counting starts with 1) in specified Category.
            TODO: switch to an after-item version?
        
            EXAMPLE invocation: http://localhost:5000/BA/api/simple/reposition/60/576/4
            """
            try:
                Categories.reposition_content(category_id=int(category_id), item_id=int(item_id), move_after_n=int(move_after_n))
                return_value = cls.SUCCESS_PREFIX               # Success
            except Exception as ex:
                err_status = f"UNABLE TO REPOSITION ELEMENT: {ex}"
                return_value = cls.ERROR_PREFIX + err_status    # Failure
        
            print(f"reposition() is returning: `{return_value}`")
        
            return return_value




        #---------------------------------------------#
        #                   FILTERS                   #
        #---------------------------------------------#
        
        @bp.route('/get-filtered-json', methods=['POST'])
        @login_required
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
        
        
        
        @bp.route('/get_filtered', methods=['POST'])
        @login_required
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
            cls.show_post_data(post_data, "get_filtered")
        
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

        @bp.route('/import_json_file', methods=['POST'])
        @login_required
        def import_json_file() -> str:
            """
            Upload and import of a data file in JSON format
            Invoke with the URL: http://localhost:5000/BA/api/import_json_file
            """
            # Extract the POST values
            post_data = request.form     # Example: ImmutableMultiDict([('use_schema', 'SCHEMA'), ('schema_class', 'my_class_name')])
            cls.show_post_data(post_data, "import_json_file")

            print("request.files: ", request.files)
            # EXAMPLE: ImmutableMultiDict([('file', <FileStorage: 'julian_test.json' ('application/json')>)])

            try:
                post_pars = cls.extract_post_pars(post_data, required_par_list=["use_schema"])
                result = APIRequestHandler.upload_import_json_file(post_pars)
                response = {"status": "ok", "payload": result}              # Successful termination
            except Exception as ex:
                response = {"status": "error", "error_message": str(ex)}    # Error termination

            print(f"import_json_file() is returning: `{response}`")

            return jsonify(response)   # This function also takes care of the Content-Type header



        @bp.route('/simple/stop_data_intake')
        #@login_required                # TODO: RESTORE
        def stop_data_intake() -> str:
            """
            Invoke with the URL: http://localhost:5000/BA/api/simple/stop_data_intake
            :return:
            """
            try:
                APIRequestHandler.do_stop_data_intake()
                return_value = cls.SUCCESS_PREFIX              # If no errors
            except Exception as ex:
                return_value = cls.ERROR_PREFIX + APIRequestHandler.exception_helper(ex)   # In case of errors

            print(f"stop_data_intake() is returning: `{return_value}`")

            return return_value


        @bp.route('/bulk_import', methods=['POST'])
        #@login_required                # TODO: RESTORE
        def bulk_import() -> str:
            """
            Bulk import (for now of JSON files)

            EXAMPLE of invocation: curl http://localhost:5000/BA/api/bulk_import -d "schema_class=my_schema_class"

            POST FIELDS:
                schema_class   TBA

            :return:
            """
            # Extract the POST values
            post_data = request.form
            # EXAMPLE: ImmutableMultiDict([('from', '123'), ('to', '88'), ('rel_name', 'BA_subcategory_of'), ('schema_code', 'cat')])
            cls.show_post_data(post_data)

            try:
                pars_dict = cls.extract_post_pars(post_data, required_par_list=['schema_class'])
                schema_class = pars_dict['schema_class']

                # Extract some config parameters
                intake_folder = current_app.config['INTAKE_FOLDER']            # Defined in main file
                outtake_folder = current_app.config['OUTTAKE_FOLDER']          # Defined in main file

                result = APIRequestHandler.do_bulk_import(intake_folder, outtake_folder, schema_class)

                response = {"status": "ok", "result": result}              # Successful termination
            except Exception as ex:
                response = {"status": "error", "error_message":  APIRequestHandler.exception_helper(ex)}    # Error termination

            print(f"bulk_import() is returning: `{response}`")

            return jsonify(response)   # This function also takes care of the Content-Type header






        @bp.route('/import_json_dump', methods=['GET', 'POST'])
        @login_required
        def import_json_dump() -> str:
            """
            EXAMPLE invocation: http://localhost:5000/BA/api/import_json_dump
        
            Upload a file that contains a Full Database Dump, as created by BrainAnnex.
            NOTE: the uploaded file remains in the temporary folder; it will need to be moved or deleted.j
            """
        
            if request.method != 'POST':
                return "This endpoint requires POST data (you invoked it with a GET method.) No action taken..."   # Handy for testing
        
            return_url = request.form["return_url"] # This originates from the HTML form :
            #    <input type="hidden" name="return_url" value="my_return_url">
            print("return_url: ", return_url)
        
            status = APIRequestHandler.upload_import_json(verbose=False, return_url=return_url)
            return status
        
        
        
        @bp.route('/upload_media', methods=['POST'])
        @login_required
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
        
            try:
                upload_dir = current_app.config['UPLOAD_FOLDER']
                (tmp_filename_for_upload, full_filename, original_name) = UploadHelper.store_uploaded_file(request, upload_dir=upload_dir, key_name="file", verbose=True)
                print(f"Upload successful so far for file: `{tmp_filename_for_upload}` .  Full name: `{full_filename}`")
            except Exception as ex:
                err_status = f"<b>ERROR in upload</b>: {ex}"
                print(err_status)
                response = make_response(err_status, 500)
                return response
        
        
            # Move the uploaded file from its temp location to the media folder
            # TODO: let upload_helper (optionally) handle it
        
            src_fullname = cls.UPLOAD_FOLDER + tmp_filename_for_upload
            dest_folder = cls.MEDIA_FOLDER
            dest_fullname = dest_folder + tmp_filename_for_upload
            print(f"Attempting to move `{src_fullname}` to `{dest_fullname}`")
            try:
                shutil.move(src_fullname, dest_fullname)
            except Exception as ex:
                err_status = f"Error in moving the file to the intended final destination ({dest_folder}) after upload. {ex}"
                return make_response(err_status, 500)
        
        
            category_id = int(post_data["category_id"])
        
            try:
                properties = ImageProcessing.process_uploaded_image(tmp_filename_for_upload, dest_fullname, media_folder=cls.MEDIA_FOLDER)
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
        
        
        
        @bp.route('/upload_file', methods=['POST'])
        @login_required
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
                upload_dir = current_app.config['UPLOAD_FOLDER']
                (tmp_filename_for_upload, full_filename, original_name) = UploadHelper.store_uploaded_file(request, upload_dir=upload_dir, key_name="file", verbose=True)
                print(f"Upload successful so far for file: `{tmp_filename_for_upload}` .  Full name: `{full_filename}`")
            except Exception as ex:
                err_status = f"<b>ERROR in upload</b>: {ex}"
                print(err_status)
        
        
            if err_status == "":    # If no errors
                response = ""
            else:                   # If errors
                response = make_response(err_status, 500)
        
            return response
        
        
        
        @bp.route('/parse_datafile', methods=['GET', 'POST'])
        @login_required
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
                upload_dir = current_app.config['UPLOAD_FOLDER']
                (tmp_filename_for_upload, full_filename, original_name) = UploadHelper.store_uploaded_file(request, upload_dir=upload_dir, key_name="imported_datafile", verbose=False)
            except Exception as ex:
                return f"<b>ERROR in upload</b>: {ex}"
        
            print("In import_datafile(): ", (tmp_filename_for_upload, full_filename))
        
            return_url = request.form["return_url"] # This originates from the HTML form :
            #    <input type="hidden" name="return_url" value="my_return_url">
            print("return_url: ", return_url)
        
            status_msg = APIRequestHandler.import_datafile(tmp_filename_for_upload, full_filename, test_only=True)
        
            status_msg += f" <a href='{return_url}' style='margin-left:50px'>Go back</a>"
        
            return status_msg
        
        
        
        @bp.route('/download_dbase_json/<download_type>')
        @login_required
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
                    result = APIRequestHandler.export_full_dbase()
                    export_filename = "exported_dbase.json"
                elif download_type == "schema":
                    result = NeoSchema.export_schema()
                    export_filename = "exported_schema.json"
                else:
                    return f"Unknown requested type of download: {download_type}"
            except Exception as ex:
                    response = APIRequestHandler.exception_helper(ex, safe_html=True)
                    error_page_body = f'''<b>Unable to perform download</b>. <br>
                                          This is typically due to the 'APOC' library not being installed on Neo4j,
                                          unless the error message below indicates something else. 
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
        
        @bp.route('/add_label/<new_label>')
        @login_required
        def add_label(new_label) -> str:
            """
            Add a new blank node with the specified label
            EXAMPLE invocation: http://localhost:5000/api/add_label/boat
            """
            status = APIRequestHandler.add_new_label(new_label)
        
            if status:
                return cls.SUCCESS_PREFIX
            else:
                return cls.ERROR_PREFIX


        ##################  END OF ROUTING DEFINITIONS  ##################
        