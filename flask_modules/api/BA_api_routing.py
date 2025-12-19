"""
    Web API endpoint
    MIT License.  Copyright (c) 2021-2025 Julian A. West and the BrainAnnex.org project
"""

from flask import Blueprint, jsonify, request, current_app, make_response  # The request package makes available a GLOBAL request object
from flask_login import login_required
from app_libraries.data_manager import DataManager
from app_libraries.documentation_generator import DocumentationGenerator
from app_libraries.media_manager import MediaManager, ImageProcessing
from app_libraries.PLUGINS.documents import Documents
from app_libraries.PLUGINS import plugin_support
from app_libraries.upload_helper import UploadHelper
from brainannex import GraphSchema, Categories
import brainannex.exceptions as exceptions                # To give better info on Exceptions
import shutil
import os
import json
#from time import sleep     # For tests of delays in asynchronous fetching.  E.g. sleep(3) for 3 secs



class ApiRouting:
    """
    Setup, routing and endpoints for all the web pages served by this module.
    Note that this class does not directly interact with the database.
    This class doesn't need to get initialized.

    EXAMPLE of static files served by this module:
            /BA/api/static/server_communication.js

    EXAMPLE of web endpoint provided by this module:
            /BA/api/get_text_media/123

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
    blueprint_name = "BA_api"       # Name unique to this module
    url_prefix = "/BA/api"          # Prefix for all URL's handled by this module
    template_folder = "templates"   # Relative to this module's location
    static_folder = "static"        # Relative to this module's location
    #static_url_path = "/assets"    # Not used by this module
    config_pars = {}                # Dict with all the app configuration parameters


    MEDIA_FOLDER = None             # Location where the media for Content Items is stored
    UPLOAD_FOLDER = None            # Temporary location for uploads

    debug = False                   # Flag indicating whether a debug mode is to be used by all methods of this class
                                    #       (currently, in very limited use)



    # NOTE: To test POST-based web APIs, on the Linux shell or Windows PowerShell issue commands such as:
    #            curl http://localhost:5000/BA/api/add_item_to_category -d "class_name=Image&category_uri=60"

    # TODO: provide support for API_KEY (or API_TOKEN) authentication




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
                                    template_folder=cls.template_folder,
                                    static_folder=cls.static_folder)

        # Define the Flask routing (mapping URLs to Python functions) for all the web pages served by this module
        cls.set_routing(flask_blueprint)

        # Register with the Flask app object the Blueprint object created above, and request the desired URL prefix
        flask_app_obj.register_blueprint(flask_blueprint, url_prefix = cls.url_prefix)

        # Save the app configuration parameters in a class variable
        cls.config_pars = flask_app_obj.config




    #######################################################
    #                   UTILITY methods                   #
    #######################################################


    @classmethod
    def explain_flask_request(cls, request_obj :request) -> None:
        """
        Print out a bunch of information to elucidate the contents
        of the given flask.request object

        :param request_obj: A flask.request object
        :return:            None
        """
        request_dict = request_obj.__dict__     # A dictionary of all names and attributes of the flask.request object
        keys_list = list(request_dict)
            # EXAMPLE: ['method', 'scheme', 'server', 'root_path', 'path', 'query_string', 'headers',
            #           'remote_addr', 'environ', 'shallow', 'cookies', 'url_rule', 'view_args',
            #           'stream', '_parsed_content_type', 'content_length', 'form', 'files']

        print(f"Upload flask.request object contains {len(request_dict)} items:\n    {keys_list}\n")

        for i, k in enumerate(keys_list):
            print(f"    ({i}) * {k}: {request_dict[k]}")

        # Note: somehow, cannot simply loop over request_dict, or it crashes with error "dictionary changed size during iteration"

        print("\nrequest.files: ", request_obj.files)     # Somehow, that's NOT included in the previous listing!
        # EXAMPLE: ImmutableMultiDict([('imported_datafile', <FileStorage: 'my_data.json' ('application/json')>)])
        #               where 'imported_datafile' originates from <input type="file" name="imported_datafile">
        #               and the name after FileStorage is the name of the file being uploaded

        print("request.args: ", request_obj.args)
        print("request.form: ", request_obj.form)
        # EXAMPLE: ImmutableMultiDict([('categoryID', '123'), ('pos', 888)])
        #               if the HTML form included <input type="hidden" name="categoryID" value="123">
        #                                     and <input type="hidden" name="pos" value="88">

        print("request.values: ", request_obj.values)
        print("request.json: ", request_obj.json)
        print("request.data: ", request_obj.data)



    @classmethod
    def extract_get_pars(cls, get_data, required_par_list=None) -> dict:
        """
        Convert the given GET data (an ImmutableMultiDict object) into a Python dictionary,
        optionally enforcing the presence of the specified required GET parameters

        EXAMPLE:
            get_data = request.args
            data_dict = cls.extract_get_pars(get_data, required_par_list=["name_of_some_required_field"])

        :param get_data:            An ImmutableMultiDict object, which is a sub-class of Dictionary
                                        that may contain multiple values for the same key.
                                        EXAMPLE: ImmutableMultiDict([('uri', '123'), ('rel_name', 'BA_served_at')])
        :param required_par_list:   [OPTIONAL] A list or tuple of name of GET parameters whose presence is to be enforced.
                                        EXAMPLE: ['uri', 'rel_name']

        :return:                    A dict populated with the GET data
        """
        data_dict = get_data.to_dict(flat=True)     # WARNING: if multiple identical keys occur,
                                                    #          the values associated to the later keys will be discarded
        if required_par_list:
            for par in required_par_list:
                assert par in data_dict, \
                    f"The expected parameter `{par}` is missing from the query string at end of the URL. The GET request: {data_dict}"

        return data_dict



    @classmethod
    def extract_post_pars(cls, post_data, required_par_list=None, json_decode=False) -> dict:
        """
        Convert into a Python dictionary the given POST data
        (expressed as an ImmutableMultiDict) - ASSUMED TO HAVE UNIQUE KEYS -
        while enforcing the optional given list of parameters that must be present.
        In case of errors (or missing required parameters), an Exception is raised.

        EXAMPLE:
                post_data = request.form
                data_dict = cls.extract_post_pars(post_data, ["name_of_some_required_field"])

        :param post_data:           An ImmutableMultiDict object, which is a sub-class of Dictionary
                                        that may contain multiple values for the same key.
                                        EXAMPLE: ImmutableMultiDict([('uri', '123'), ('rel_name', 'BA_served_at')])

        :param required_par_list:   [OPTIONAL] A list or tuple of name of POST parameters whose presence is to be enforced.
                                        If the json_decode argument is True, then these parameters may reside
                                        EXAMPLE: ['uri', 'rel_name']
        :param json_decode:         If True, all values are expected to be JSON-encoded strings
        :return:                    A dict populated with the POST data
        """
        #TODO: return a dict with 2 keys: one whose value is the required fields,
        #      PLUS an extra key, "OTHER_FIELDS" that contains a dict with the remaining fields
        '''
        other_fields = {}
        required_fields = {}
        return_dict = {"REQUIRED: required_fields, "OTHER": other_fields}
        for k, v in data_binding.items():
            if k in required_par_list:    # Exclude some special keys
                return_dict[k] = v
            else:
                other_fields[k] = v
        '''

        #TODO: instead of accepting "post_data" as argument,
        #      extract it here, with a:  post_data = request.form  (and optional call to show_post_data)

        #TODO:  maybe optionally pass a list of pars that must be int, and handle conversion and errors;
        #       but maybe the parameter validation doesn't belong to this API module, which ought to remain thin
        #       Example - int_pars = ['uri']

        #TODO: merge with get_form_data()

        data_dict = post_data.to_dict(flat=True)    # WARNING: if multiple identical keys occur,
                                                    #          the values associated to the later keys will be discarded

        if required_par_list:
            # Verify that all the required POST parameters are indeed present
            if len(data_dict) == 0:
                raise Exception(f"The POST request does not contain any data; "
                                f"the following parameters were expected: {required_par_list}")
            for par in required_par_list:
                assert par in data_dict, f"The expected parameter `{par}` is missing from the POST request"

        if json_decode:
            # Decode all the values in the data dictionary
            for key, val in data_dict.items():
                data_dict[key] = json.loads(val)

        return data_dict


    @classmethod
    def get_form_data(cls, request_obj, flat=True) -> dict:
        """
        It accepts a flask.request object, and it extracts and returns
        a dictionary with the data passed by the calling form thru inputs, such as:
                <input type="hidden" name="categoryID" value="123">
                <input name="remarks" value="some text">
        or its counterpart in JS submissions, such as
                                            const post_data = new FormData();
                                            post_data.append('categoryID', "123");

        TODO: merge with extract_post_pars()

        :param request_obj: A flask.request object
        :param flat:        A flag only relevant when there are non-unique keys;
                            if True (default), the values associated to the later keys will be discarded...
                            if False, values are returned as lists
                            EXAMPLE - if the data originates from:
                                <input type="hidden" name="my_data" value="88">
                                <input type="hidden" name="my_data" value="99">
                            then flat=True returns {'my_data': '88'}
                            while flat=False returns {'my_data': ['88', '99']}

        :return:            A dictionary with the POST data
        """
        hidden_data = request_obj.form
        # EXAMPLE: ImmutableMultiDict([('categoryID', '123'), ('pos', 888)])
        #               if the HTML form included <input type="hidden" name="categoryID" value="123">
        #                                     and <input type="hidden" name="pos" value="88">
        #               Note that the keys may not be unique

        data_dict = hidden_data.to_dict(flat=flat)  # WARNING: if multiple identical keys occur,
        #          the values associated to the later keys will be discarded

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
        :param method_name: (Optional) Name of the invoking function
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


        #####################################################################################################

        '''                          ~   SCHEMA-RELATED (reading)  ~                                      '''

        def ________SCHEMA_READ________(DIVIDER):
            pass        # Used to get a better structure view in IDEs
        #####################################################################################################


        #"@" signifies a decorator - a way to wrap a function and modify its behavior
        @bp.route('/get_class_properties')
        @login_required
        def get_class_properties():
            """
            Get all Properties of the given Class node (as specified by its name),
            optionally including indirect ones that arise thru chains of outbound "INSTANCE_OF" relationships.
            Return a JSON object with a list of the Property names of that Class.

            If `class_name` is missing, and `label` is used instead,
            the Property list is *estimated* by the label instead (and all other parameters are disregarded)


            GET VARIABLE:
                json    A JSON-encoded dict

            KEYS in the JSON-encoded dict:
                    class_name
                    label
                    include_ancestors
                    sort_by_path_len
                    exclude_system
                Either `class_name` or `label` must be present

            EXAMPLE invocations:
                http://localhost:5000/BA/api/get_class_properties?json=%7B%22class_name%22%3A%20%22Quote%22%7D
                    (passing the URL-safe version of the JSON-serialized dict {"class_name": "Quote"})

                http://localhost:5000/BA/api/get_class_properties?json=%7B%22class_name%22%3A%20%22Quote%22%2C%20%22include_ancestors%22%3A%20true%7D
                    (corresponding to {"class_name": "Quote", "include_ancestors": True})

                http://localhost:5000/BA/api/get_class_properties?json=%7B%22class_name%22%3A%20%22Quote%22%2C%20%22include_ancestors%22%3A%20true%2C%20%22exclude_system%22%3A%20true%7D
                    (corresponding to {"class_name": "Quote", "include_ancestors": True, "exclude_system": True})

            Note: To generate URL-safe versions of the JSON-serialized data from d variable in Python, use
                    import json
                    import urllib.parse
                    urllib.parse.quote(json.dumps(d))

            For details, see GraphSchema.get_class_properties()

            :return:  A JSON with a list of the Property names of the specified Class,
                      optionally including indirect ones that arise thru
                      chains of outbound "INSTANCE_OF" relationships
                         EXAMPLE:
                            {
                                "payload":  [
                                              "Note",
                                              "English",
                                              "French"
                                            ],
                                "status":   "ok"
                            }
            """
            # Extract the GET values
            get_data = request.args    # Example: ImmutableMultiDict([('json', 'SOME_JSON_ENCODED_DATA')])

            try:
                # This operation might fail - if there are problems in the JSON encoding
                data_dict = cls.extract_get_pars(get_data)      # required_par_list=["json"]
            except Exception as ex:
                err_details = exceptions.exception_helper(ex)
                response_data = {"status": "error", "error_message": err_details}        # Error termination
                print(response_data["error_message"])
                return jsonify(response_data)    # This function also takes care of the Content-Type header


            json_str = data_dict["json"]
            #print("get_class_properties() - JSON string: ", json_str)

            # TODO: turn a lot of the code below into a JSON-helper method;
            #       in particular, add a "json_decode" arg to extract_get_pars()
            #       See approach in '/update_content_item_JSON'

            try:
                # This operation might fail - if there are problems in the JSON encoding
                json_data = json.loads(json_str)    # Turn the string into a Python object
                #print("Decoded JSON request: ", json_data)
            except Exception as ex:
                response_data = {"status": "error", "error_message": f"Failed parsing of JSON string in request. Incorrectly formatted.  {ex}"}
                print(response_data["error_message"])
                return jsonify(response_data)    # This function also takes care of the Content-Type header

            if ("class_name" not in json_data) and ("label" not in json_data):
                response_data = {"status": "error", "error_message": "Missing required value for either `class_name` or `label` in the JSON data"}
                print(response_data["error_message"])
                return jsonify(response_data)    # This function also takes care of the Content-Type header

            class_name = json_data.get("class_name")
            label = json_data.get("label")
            #print("class_name: ", class_name)
            if "class_name" in json_data:
                del json_data["class_name"]
            if "label" in json_data:
                del json_data["label"]

            try:
                # Fetch all the Properties
                if class_name:
                    prop_list = GraphSchema.get_class_properties(**json_data, class_node=class_name)
                else:
                    prop_set = GraphSchema.db.sample_properties(label=label, sample_size=30)    # Estimate the list of properties by label
                    # Take out Schema-related properties, if present
                    prop_set.discard("_CLASS")      # Remove if present
                    prop_set.discard("uri")         # Remove if present
                    prop_list = list(prop_set)

                response_data = {"status": "ok", "payload": prop_list}
            except Exception as ex:
                response_data = {"status": "error", "error_message": str(ex)}

            #print("get_class_properties() - response_data: ", response_data)

            return jsonify(response_data)   # This function also takes care of the Content-Type header



        @bp.route('/get_links/<class_name>')
        @login_required
        def get_links(class_name):
            """
            Get the names of all the relationship attached to the specified Class.
            (No error if the Class doesn't exist)

            EXAMPLE invocation: http://localhost:5000/BA/api/get_links/Entrees

            :param class_name:  The name of a Schema Class node
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
                rel_names = GraphSchema.get_class_relationships(class_name=class_name, omit_instance=True)
                payload = {"in": rel_names["in"], "out": rel_names["out"]}
                response = {"status": "ok", "payload": payload}    # Successful termination
            except Exception as ex:
                err_details = f"/get_links :  {exceptions.exception_helper(ex)}"
                response = {"status": "error", "error_message": err_details}    # Error termination

            return jsonify(response)   # This function also takes care of the Content-Type header



        @bp.route('/get_class_schema', methods=['POST'])
        @login_required
        def get_class_schema():
            """
            Get all Schema data - both Properties and Links - of the given Class node
            (as specified by its name passed as a POST variable),
            including indirect Properties thru chains of outbound "INSTANCE_OF" relationships.
            Properties marked as "system" ones gets excluded.

            Return a JSON object with a list of the Property names of that Class.

            1 POST FIELD:
                class_name

            EXAMPLE invocation:
                curl http://localhost:5000/BA/api/get_class_schema  -d "class_name=Restaurants"

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
            #cls.show_post_data(post_data, "get_class_schema")

            data_dict = dict(post_data)
            if "class_name" not in data_dict:
                response = {"status": "error",
                            "error_message": "/get_class_schema: the expected POST parameter `class_name` is not present"}
                return jsonify(response)   # This function also takes care of the Content-Type header

            class_name = data_dict["class_name"]

            try:
                # Fetch all the Properties
                prop_list = GraphSchema.get_class_properties(class_name, include_ancestors=True, exclude_system=True)
                rel_names = GraphSchema.get_class_relationships(class_name=class_name, omit_instance=True)
                payload = {"properties": prop_list, "in_links": rel_names["in"], "out_links": rel_names["out"]}
                response = {"status": "ok", "payload": payload}
            except Exception as ex:
                err_details = f"/get_class_schema :  {exceptions.exception_helper(ex)}"
                response = {"status": "error", "error_message": err_details}


            return jsonify(response)   # This function also takes care of the Content-Type header



        @bp.route('/all_labels')
        @login_required
        def all_labels():
            """
            Get all the node labels present in the database

            EXAMPLE:   ['label_1', 'label_2']

            EXAMPLE invocation: http://localhost:5000/BA/api/all_labels
            """

            try:
                all_labels = DataManager.get_node_labels()      # EXAMPLE: ["my_label_1", "my_label_2"]
                response = {"status": "ok", "payload": all_labels}          # Successful termination
            except Exception as ex:
                response = {"status": "error", "error_message": str(ex)}    # Error termination

            #print(f"all_labels() is returning: `{response}`")

            return jsonify(response)        # This function also takes care of the Content-Type header



        @bp.route('/get_record_classes')
        @login_required
        def get_record_classes():
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
                result = DataManager.get_leaf_records()
                response = {"status": "ok", "payload": result}              # Successful termination
            except Exception as ex:
                response = {"status": "error", "error_message": str(ex)}    # Error termination
        
            #print(f"get_record_classes() is returning: `{response}`")
        
            return jsonify(response)        # This function also takes care of the Content-Type header



        @bp.route('/get_properties_by_uri/<uri>')
        @login_required
        def get_properties_by_uri(uri):
            """
            Get all properties of a DATA node specified by its URI

            EXAMPLE invocation: http://localhost:5000/BA/api/get_properties_by_uri/123

            :param uri: A string uniquely identifying a data node
            :return:    A JSON object with a list of the Properties of the specified Class
                            EXAMPLE:
                                    [
                                      "Note",
                                      "English",
                                      "French"
                                    ]
            """
            prop_list = GraphSchema.all_properties("BA", "uri", uri)
            response = {"status": "ok", "payload": prop_list}
            # TODO: handle error scenarios

            return jsonify(response)   # This function also takes care of the Content-Type header




        #####################################################################################################

        '''                   ~   SCHEMA-RELATED (creating/editing/deleting)  ~                           '''

        def ________SCHEMA_WRITE________(DIVIDER):
            pass        # Used to get a better structure view in IDEs
        #####################################################################################################

        @bp.route('/create_new_schema_class', methods=['POST'])
        @login_required
        def create_new_schema_class():
            """
            Create a new Schema Class, possibly linked to another existing class,
            and also - typically but optionally - with the special "INSTANCE_OF" link
            to an existing Class (often, the "Records" Class)

            EXAMPLES of invocation:
                curl http://localhost:5000/BA/api/create_new_schema_class -d
                    "new_class_name=my%20new%20class&properties_list=A,B,C,&instance_of=Records"

                curl http://localhost:5000/BA/api/create_new_schema_class -d
                    "new_class_name=Greek&properties_list=Greek,&instance_of=Foreign%20Vocabulary"

                curl http://localhost:5000/BA/api/create_new_schema_class -d
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
            post_data = request.form     # Example: ImmutableMultiDict([('data', 'Quote,quote,attribution,notes')])
            #cls.show_post_data(post_data, "create_new_schema_class")

            try:
                class_specs = cls.extract_post_pars(post_data, required_par_list=["new_class_name"])
                DataManager.new_schema_class(class_specs)
                response_data = {"status": "ok"}                                    # Success
            except Exception as ex:
                err_details = f"/create_new_schema_class : Unable to create a new Schema Class.  {exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}    # Failure

            #print(f"create_new_schema_class() is returning: `{err_details}`")

            return jsonify(response_data)   # This function also takes care of the Content-Type header



        @bp.route('/delete_class', methods=['POST'])
        @login_required
        def delete_class():
            """
            Delete a Class specified by its name.
            All its Properties will also get deleted alongside.
            The operation will fail if the Class doesn't exist,
            or if data nodes attached to that Class are present (those would need to be deleted first)

            POST FIELDS:
                class_name

            EXAMPLE of invocation:
                curl http://localhost:5000/BA/api/delete_class -d
                        "class_name=some_class_1"
            """
            # Extract the POST values
            post_data = request.form     # An ImmutableMultiDict object
            #cls.show_post_data(post_data, "delete_class")

            try:
                pars_dict = cls.extract_post_pars(post_data, required_par_list=["class_name"])
                GraphSchema.delete_class(name=pars_dict["class_name"], safe_delete=True)
                response_data = {"status": "ok"}                                    # Success
            except Exception as ex:
                err_details = f"Unable to delete the class.  {exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}    # Failure

            #print(f"delete_class() is returning: `{response_data}`")

            return jsonify(response_data)   # This function also takes care of the Content-Type header



        @bp.route('/schema_add_property_to_class', methods=['POST'])
        @login_required
        def schema_add_property_to_class():
            """
            Add a new Property to an existing Class, identified by its name

            POST FIELDS:
                prop_name
                class_name

            EXAMPLE of invocation:
                curl http://localhost:5000/BA/api/schema_add_property_to_class -d
                        "prop_name=gender&class_name=patient"
            """
            # Extract the POST values
            post_data = request.form     # An ImmutableMultiDict object
            #cls.show_post_data(post_data, "schema_add_property_to_class")

            try:
                class_specs = cls.extract_post_pars(post_data)
                DataManager.schema_add_property_to_class_handler(class_specs)
                response_data = {"status": "ok"}                                    # Success
            except Exception as ex:
                err_details = f"Unable to add the new property.  {exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}   # Failure

            #print(f"schema_add_property_to_class() is returning: `{return_value}`")

            return jsonify(response_data)   # This function also takes care of the Content-Type header



        @bp.route('/add_schema_relationship', methods=['POST'])
        @login_required
        def add_schema_relationship():
            """
            Add a relationship with the specified name between 2 existing Classes

            POST FIELDS:
                from_class_name
                to_class_name
                rel_name

            EXAMPLE of invocation:
                curl http://localhost:5000/BA/api/add_schema_relationship -d
                        "from_class_name=some_class_1&to_class_name=some_class_2&rel_name=CONNECTED_TO"
            """
            # Extract the POST values
            post_data = request.form     # An ImmutableMultiDict object
            #cls.show_post_data(post_data, "add_schema_relationship")

            try:
                class_specs = cls.extract_post_pars(post_data, required_par_list=["from_class_name", "to_class_name", "rel_name"])
                DataManager.add_schema_relationship_handler(class_specs)
                response_data = {"status": "ok"}                                     # Success
            except Exception as ex:
                err_details = f"Unable to add a new relationship.  {exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}    # Failure

            #print(f"add_schema_relationship() is returning: `{response_data}`")

            return jsonify(response_data)   # This function also takes care of the Content-Type header



        @bp.route('/delete_schema_relationship', methods=['POST'])
        @login_required
        def delete_schema_relationship():
            """
            Delete the relationship with the specified name between 2 existing Classes
            POST FIELDS:
                from_class_name
                to_class_name
                rel_name

            EXAMPLE of invocation:
                curl http://localhost:5000/BA/api/delete_schema_relationship -d
                        "from_class_name=some_class_1&to_class_name=some_class_2&rel_name=CONNECTED_TO"
            """
            # Extract the POST values
            post_data = request.form     # An ImmutableMultiDict object
            #cls.show_post_data(post_data, "delete_schema_relationship")

            try:
                class_specs = cls.extract_post_pars(post_data, required_par_list=["from_class_name", "to_class_name", "rel_name"])
                DataManager.delete_schema_relationship_handler(class_specs)
                response_data = {"status": "ok"}                                    # Success
            except Exception as ex:
                err_details = f"Unable to delete the relationship.  {exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}   # Failure

            #print(f"delete_schema_relationship() is returning: `{response_data}`")

            return jsonify(response_data)   # This function also takes care of the Content-Type header




        #####################################################################################################

        '''                              ~   VIEWING CONTENT ITEMS   ~                                    '''

        def ________VIEWING_CONTENT_ITEMS________(DIVIDER):
            pass        # Used to get a better structure view in IDEs
        #####################################################################################################

        @bp.route('/get_text_media/<uri>')
        @login_required
        def get_text_media(uri):
            """
            Retrieve and return the contents of a TEXT media item (for now, just "notes")

            EXAMPLE invocation: http://localhost:5000/BA/api/get_text_media/123

            :param uri: The URI of a data node representing a text media Item (such as a "Note")
            :return:    A Flask Response response object containing a JSON string
                            with the contents of the specified text media Item
                            EXAMPLE of successful response data:
                                {
                                    "status": "ok",
                                    "payload": "I'm the contents of the text media file"
                                }
                            In case the text media isn't found, a normal response status (200) is still sent,
                            but the JSON in the payload with provide "status": "error",
                            and an "error_message" key with details
            """
            try:
                payload = DataManager.get_text_media_content(uri, class_name="Note")
                #print(f"get_text_media() is returning the following text [first 30 chars]: `{payload[:30]}`")
                response_data = {"status": "ok", "payload": payload}                     # Successful termination
            except Exception as ex:
                err_details = f"Unable to retrieve the requested Media Item.  {exceptions.exception_helper(ex)}"
                #print(f"get_text_media() encountered the following error: {err_details}")
                response_data = {"status": "error", "error_message": err_details}        # Error termination

            return jsonify(response_data)   # This function also takes care of the Content-Type header



        @bp.route('/remote_access_note/<uri>')
        def remote_access_note(uri):     # NO LOGIN REQUIRED
            """
            Similar to get_text_media(), but:
                1) no login required
                2) specifically for Notes  (TODO: possibly generalize to any media)
                3) it only serves items that are marked as "public" in the database

            EXAMPLE invocation: http://localhost:5000/BA/api/remote_access_note/123
            """
            try:
                payload = DataManager.get_text_media_content(uri=uri, class_name="Note", public_required=True)
                #print(f"remote_access_note() is returning the following text [first 30 chars]: `{payload[:30]}`")
                response_data = {"status": "ok", "payload": payload}    # Successful
                response = jsonify(response_data)
                response.headers['Access-Control-Allow-Origin'] = '*'   # This will send the header line: "Access-Control-Allow-Origin: *"
                                                                        # without it, web clients on other domains won't be able to use the payload!
                                                                        # An alternative to '*' would be a site name, such as  'https://foo.example'

            except Exception as ex:
                err_details = f"Unable to retrieve the requested note.  {exceptions.exception_helper(ex)}"
                #print(f"remote_access_note() encountered the following error: {err_details}")
                response_data = {"status": "error", "error_message": err_details}        # Error termination
                response = jsonify(response_data)

            return response



        @bp.route('/serve_media/<class_name>/<uri>')
        @bp.route('/serve_media/<class_name>/<uri>/<th>')
        @login_required
        def serve_media(class_name, uri, th=None):
            """
            Retrieve and return the contents of a data media item.
            If ANY value is specified for the argument "th", then the thumbnail version is returned (only
                applicable to images)

            EXAMPLES of invocation:
                http://localhost:5000/BA/api/serve_media/Image/1234
                http://localhost:5000/BA/api/serve_media/Image/1234/th
                http://localhost:5000/BA/api/serve_media/Document/888

            :param class_name:
            :param uri: The URI of a data node representing a media Item (such as an "Image" or "Document")
            :param th:  Only applicable to Images.  If not None, then the thumbnail version is returned
            :return:    A Flask Response object containing the data for the requested media,
                            with a header setting the MIME type appropriate for the media format
                        In case the media isn't found, a 404 response status is sent,
                            together with an error message
            """
            try:
                (suffix, content) = MediaManager.get_binary_content(uri, class_name=class_name, th=th)
                response = make_response(content)
                # Set the MIME type
                mime_type = MediaManager.get_mime_type(suffix)
                response.headers['Content-Type'] = mime_type
                #print(f"serve_media() is returning the contents of data file, with file suffix `{suffix}`.  "
                #      f"Serving with MIME type `{mime_type}`")
            except Exception as ex:
                err_details = f'Unable to retrieve Media Item of Class "{class_name}" with uri "{uri}". {exceptions.exception_helper(ex)}'
                #print(f"serve_media() encountered the following error: {err_details}")
                response = make_response(err_details, 404)

            return response



        @bp.route('/get_link_summary/<uri_str>')
        @login_required
        def get_link_summary_api(uri_str):
            """
            Return a JSON structure identifying the names and counts of all
            inbound and outbound links to/from the given data node.

            This is approximately the data-node counterpart of the schema API 'get_links'

            EXAMPLE invocation: http://localhost:5000/BA/api/get_link_summary/47

            :param uri_str: ID of a data node
            :return:            A JSON string with the names and counts of inbound and outbound links
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
                uri = uri_str
                payload = DataManager.get_link_summary(uri, omit_names = ['BA_in_category'])
                response = {"status": "ok", "payload": payload}             # Successful termination
            except Exception as ex:
                response = {"status": "error", "error_message": str(ex)}    # Error termination

            return jsonify(response)   # This function also takes care of the Content-Type header


        @bp.route('/get-link-summary-by-id/<internal_id>')
        @login_required
        def get_link_summary_by_id(internal_id):
            """
            Return a JSON structure identifying the names and counts of all
            the inbound and outbound links to and from the given node.

            EXAMPLE invocation: http://localhost:5000/BA/api/get-link-summary-by-id/123

            :param internal_id: Internal database ID of the node of interest
            :return:            A JSON string with the names and counts of inbound and outbound links
                                EXAMPLE:
                                    {
                                        "status": "ok",
                                        "payload": [["HAS_ON_PAYROLL", "IN", 2],
                                                    ["EMPLOYED_BY", "OUT", 2],
                                                    ["MARRIED_TO", "OUT", 1]
                                                   ]
                                    }
            """
            try:
                link_data = GraphSchema.db.get_link_summary(internal_id=internal_id)
                # Transform the format      TODO: maybe move to DataManager
                payload = []
                for l in link_data["in"]:   # Process the inbound links
                    payload.append([l[0], "IN", l[1]])  # EXAMPLE: payload.append(["EMPLOYS", "IN", 2])

                for l in link_data["out"]:  # Process the outbound links
                    payload.append([l[0], "OUT", l[1]])

                response = {"status": "ok", "payload": payload}             # Successful termination
            except Exception as ex:
                response = {"status": "error", "error_message": str(ex)}    # Error termination

            return jsonify(response)   # This function also takes care of the Content-Type header



        @bp.route('/get_records_by_link', methods=['POST'])
        @login_required
        def get_records_by_link_api():
            """
            Locate and return the data (properties) of all the nodes (up to a max of 100)
            linked to the one specified by either its uri or internal database ID.
            From that node, follow the relationships named by `rel_name`, in the direction specified by `dir`.

            If the internal database ID is provided,
            then the internal database ID's of the matched nodes is also returned in each record.

            EXAMPLES of invocation:
                1) Using uri:
                    curl http://localhost:5000/BA/api/get_records_by_link -d "uri=123&rel_name=BA_served_at&dir=IN"
                2) Using internal_id:
                    curl http://localhost:5000/BA/api/get_records_by_link -d "internal_id=8&rel_name=BA_served_at&dir=IN"

            POST PARAMETERS:
                uri or internal_id      One of them is required (the latter takes priority)
                rel_name                The name of the relationship to follow across one hop
                dir                     Must be either "IN" or "OUT"
            """
            # TODO: provide flexibility for the max number returned (currenly hardwired)
            # Extract the POST values
            post_data = request.form
            # EXAMPLE: ImmutableMultiDict([('uri', '123'), ('rel_name', 'BA_served_at'), ('dir', 'IN')])
            #cls.show_post_data(post_data)

            try:
                data_dict = cls.extract_post_pars(post_data, required_par_list=['rel_name', 'dir'])
                payload = DataManager.get_records_by_link(data_dict)
                response = {"status": "ok", "payload": payload}             # Successful termination
            except Exception as ex:
                response = {"status": "error", "error_message": str(ex)}    # Error termination

            return jsonify(response)   # This function also takes care of the Content-Type header





        #####################################################################################################

        '''                              ~   MODIFYING EXISTING CONTENT ITEMS   ~                         '''

        def ________MODIFYING_CONTENT_ITEMS________(DIVIDER):
            pass        # Used to get a better structure view in IDEs
        #####################################################################################################


        @bp.route('/create_data_node_JSON', methods=['POST'])
        @login_required
        def create_data_node_JSON():
            """
            Create a new Data Node

            RESTRICTION: currently, not to be used for any Content Item that
                         requires plugin-specific actions

            POST VARIABLES:
                json    (REQUIRED) A JSON-encoded dict

            EXPECTED Content-Type for the request:  "application/json"

            KEYS in the JSON-encoded dict:
                class_name          The name of the Class of the new Data Node
                *PLUS* any applicable plugin-specific fields

            RETURNED PAYLOAD (on success):
                A JSON-encoded dict of the Internal Database ID and the URI assigned to the newly-created Data Node

            EXAMPLE:
                Send to  localhost:5000/BA/api/create_data_node_JSON ,
                with Content-Type for the request:  "application/json",
                a POST request with the following body:
                {"class_name": "Quote", "quote": "Inspiration exists, but it has to find us working", "attribution": "Pablo Picasso"}

                The response body will be something like:
                    {
                      "payload": {
                        "internal_id": 1234,
                        "uri": "q-88"
                      },
                      "status": "ok"
                    }

            """
            #TODO: explore more Schema enforcements
            #TODO: make the generation of the URI optional
            #TODO: lift restriction against plugin-specific actions

            # Extract and parse the POST value
            pars_dict = request.get_json()  # This parses the JSON-encoded string in the POST message,
                                            # provided that mimetype indicates "application/json"
                                            # EXAMPLE: {"class_name": "Quote",
                                            #           "quote": "Inspiration exists, but it has to find us working",
                                            #           "attribution": "Pablo Picasso"}

            print("In create_data_node_JSON() -  pars_dict: ", pars_dict)


            # TODO: create a helper function for the unpacking/validation below
            class_name = pars_dict.get('class_name')


            # Create a new Content Item with the POST data
            try:
                del pars_dict["class_name"]


                payload = DataManager.create_data_node(class_name=class_name,
                                                       item_data=pars_dict)
                # It returns the internal database ID and the URI of the newly-created Data Node
                # EXAMPLE: {"internal_id": 123, "uri": "rs-8"}

                response_data = {"status": "ok", "payload": payload}
            except Exception as ex:
                err_details = f"/create_data_node_JSON : Unable to add the requested Content Item to the specified Category.  " \
                              f"{exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}

            #print(f"create_data_node_JSON() is returning: `{err_details}`")

            return jsonify(response_data)   # This function also takes care of the Content-Type header



        @bp.route('/update_content_item', methods=['POST'])
        @login_required
        def update_content_item():
            """
            Update an existing Data Node, possibly representing a Content Item.

            Required POST variables:
                'uri', 'class_name'
            Optional  POST variables: whichever fields are being edited

            NOTES:  the "class_name" field in the POST data is redundant.
                    A JSON version of this endpoint is also available

            EXAMPLES of invocation:
                curl http://localhost:5000/BA/api/update_content_item -d "uri=11&class_name=Headers&text=my_header"
                curl http://localhost:5000/BA/api/update_content_item -d "uri=62&class_name=German Vocabulary&English=Love&German=Liebe"
            """
            #TODO: probably phase out in favor of '/update_content_item_JSON'
            #TODO: maybe use a PUT or PATCH method, instead of a POST
            #TODO: explore more Schema enforcements

            # Extract the POST values
            post_data = request.form    # Example: ImmutableMultiDict([('uri', '11'), ('class_name', 'Header'), ('text', 'my_header')])
            #cls.show_post_data(post_data, "update_content_item")

            try:
                data_dict = cls.extract_post_pars(post_data, required_par_list=['uri', 'class_name'])
                uri=data_dict["uri"]
                class_name=data_dict["class_name"]
                del data_dict["uri"]
                del data_dict["class_name"]
                DataManager.update_content_item(uri=uri, class_name=class_name,
                                                update_data=data_dict)
                response_data = {"status": "ok"}                                    # If no errors
            except Exception as ex:
                err_details = f"Unable to update the specified Content Item.  {exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}   # Error termination
                #TODO: consider a "500 Internal Server Error" in this case
                #      or maybe a "422 Unprocessable Entity"

            #print(f"update_content_item() is returning: `{response_data}`")

            return jsonify(response_data)   # This function also takes care of the Content-Type header



        @bp.route('/update_content_item_JSON', methods=['POST'])
        @login_required
        def update_content_item_JSON():
            """
            Update an existing Data Node, possibly representing a Content Item.
            This is variation of '/update_content_item' that expects to receive JSON data

            1 POST VARIABLE EXPECTED:
                json    (REQUIRED) A JSON-encoded dict

            KEYS in the JSON-encoded dict:
                REQUIRED    `uri` and `class_name`
                                OR  `internal_id`
                OPTIONAL    whichever fields are being edited

            EXAMPLES of invocation:
                curl http://localhost:5000/BA/api/update_content_item_JSON
                        -d 'json={"uri":"6965","class_name":"Recordset","class":"YouTube Channel","n_group":7,"order_by":"name"}'

                curl http://localhost:5000/BA/api/update_content_item_JSON
                        -d 'json={"internal_id":123,"note":"My note","name":"Brain Annex channel"}'
            """
            #TODO: maybe use a PUT or PATCH method, instead of a POST
            #TODO: explore more Schema enforcements

            # Extract and parse the POST value
            try:
                data_dict = request.get_json()      # This parses the JSON-encoded string in the POST message into a python dictionary,
                                                    # provided that mimetype indicates "application/json";
                                                    # other mime types will result in a None value
                assert data_dict is not None, "the client request does not have the MIME type 'application/json'"
            except Exception as ex:
                err_details = f"update_content_item_JSON(): Unable to update the Record (Content Item / Database Node).  " \
                              f"Request body could not be parsed as valid JSON.  {exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}   # Error termination
                return jsonify(response_data), 400      # 400 is "Bad Request client error"

            # EXAMPLES of data_dict:
            #       {'uri': '6967', 'class_name': 'Recordset', 'class': 'University Classes', 'n_group': 12, 'order_by': 'code'}
            #       {'internal_id': 123, 'note': 'My note', 'name': 'Brain Annex channel'}
            # See: https://flask.palletsprojects.com/en/1.1.x/api/
            print("In update_content_item_JSON() -  data_dict: ", data_dict)

            # TODO: create a helper function for the unpacking/validation below
            # The following values will be None if missing
            uri = data_dict.get('uri')
            class_name = data_dict.get('class_name')
            label = data_dict.get('label')
            internal_id = data_dict.get('internal_id')

            # Enforce required parameters (TODO: turn this into a general utility function)
            if (not uri or not class_name) and (not internal_id):
                err_details = f"update_content_item_JSON(): some required parameters are missing; " \
                              f"`uri` and `class_name` (or, alternatively `internal_id`) are required"
                response_data = {"status": "error", "error_message": err_details}
                return jsonify(response_data), 422      # "Unprocessable Entity", for parsed but invalid content


            # Take out special fields that aren't meant to be set in the Data Node being edited
            if uri:
                del data_dict["uri"]
            if class_name:
                del data_dict["class_name"]
            if label:
                del data_dict["label"]
            if internal_id:
                del data_dict["internal_id"]

            if uri:
                # Scenario where `uri` and (`class_name` and/or `label`) are used
                try:
                    DataManager.update_content_item(uri=uri, class_name=class_name, label=label,
                                                    update_data=data_dict)
                    response_data = {"status": "ok"}                                    # If no errors
                except Exception as ex:
                    err_details = f"Unable to update the specified Content Item.  {exceptions.exception_helper(ex)}"
                    response_data = {"status": "error", "error_message": err_details}   # Error termination
                                            #TODO: consider a "500 Internal Server Error" in this case
                                            #      or maybe a "422 Unprocessable Entity"
            else:
                # Scenario where `internal_id` is used  (TODO: maybe this branch should be prioritized)
                try:
                    number_properties_set = GraphSchema.db.set_fields(match=internal_id,
                                                                      set_dict=data_dict, drop_blanks=True)
                    assert number_properties_set > 0, f"No node found with internal_id {internal_id}"
                    response_data = {"status": "ok"}                                    # If no errors
                except Exception as ex:
                    err_details = f"Unable to update the specified record.  {exceptions.exception_helper(ex)}"
                    response_data = {"status": "error", "error_message": err_details}   # Error termination
                                            #TODO: consider a "500 Internal Server Error" in this case
                                            #      or maybe a "422 Unprocessable Entity"


            print(f"update_content_item() is returning: `{response_data}`")

            return jsonify(response_data)   # This function also takes care of the Content-Type header



        @bp.route('/delete/<uri>/<class_name>')
        @login_required
        def delete(uri, class_name):
            """
            Delete the specified Content Item.

            EXAMPLE invocation: http://localhost:5000/BA/api/delete/46/Document
            """
            try:
                DataManager.delete_content_item(uri=uri, class_name=class_name)
                response_data = {"status": "ok"}              # If no errors
            except Exception as ex:
                err_details = f"Unable to delete the requested Content Item.  {exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}        # Error termination

            #print(f"delete() is returning: `{response_data}`")

            return jsonify(response_data)   # This function also takes care of the Content-Type header



        @bp.route('/add_relationship', methods=['POST'])
        @login_required
        def add_relationship():
            """
            Add the specified relationship (edge) between existing Data Nodes.
            This is a generic API to add *any* relationship; no other changes made.

            POST FIELDS:
                from                    The URI of the Data Nodes from which the relationship originates
                to                      The URI of the Data Nodes into which the relationship takes
                rel_name                The name of the relationship to add
                schema_code (optional)  If passed, the appropriate plugin gets invoked

            EXAMPLE of invocation:
                curl http://localhost:5000/BA/api/add_relationship -d
                        "from=some_uri_1&to=some_uri_2&rel_name=SOME_NAME"
            """
            # TODO: maybe merge with the schema endpoint /add_schema_relationship

            # Extract the POST values
            post_data = request.form
            # EXAMPLE: ImmutableMultiDict([('from', '123'), ('to', '88'), ('rel_name', 'BA_subcategory_of'), ('schema_code', 'cat')])
            #cls.show_post_data(post_data, "add_relationship")

            try:
                data_dict = cls.extract_post_pars(post_data, required_par_list=['from', 'to', 'rel_name'])
                DataManager.add_data_relationship_handler(data_dict)
                response_data = {"status": "ok"}                                    # If no errors
            except Exception as ex:
                err_details = f"Unable to add the requested data relationship.  {exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}   # In case of errors

            #print(f"add_relationship() is returning: `{response_data}`")

            return jsonify(response_data)   # This function also takes care of the Content-Type header



        @bp.route('/remove_relationship', methods=['POST'])
        @login_required
        def remove_relationship():
            """
            Remove the specified relationship (edge) between Data Nodes

            POST FIELDS:
                from                    The uri of the node from which the relationship originates
                to                      The uri of the node into which the relationship takes
                rel_name                The name of the relationship to remove
                schema_code (optional)  If passed, the appropriate plugin gets invoked

            EXAMPLE of invocation:
                curl http://localhost:5000/BA/api/remove_relationship -d
                        "from=some_uri_1&to=some_uri_2&rel_name=SOME_NAME"
            """
            # TODO: maybe merge with the schema endpoint /remove_schema_relationship

            # Extract the POST values
            post_data = request.form
            # EXAMPLE: ImmutableMultiDict([('from', '123'), ('to', '88'), ('rel_name', 'BA_subcategory_of'), ('schema_code', 'cat')])
            #cls.show_post_data(post_data, "remove_relationship")

            try:
                data_dict = cls.extract_post_pars(post_data, required_par_list=['from', 'to', 'rel_name'])
                DataManager.remove_data_relationship_handler(data_dict)
                response_data = {"status": "ok"}                                     # If no errors
            except Exception as ex:
                err_details = f"Unable to remove the requested data relationship.  {exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}    # In case of errors

            #print(f"remove_relationship() is returning: `{response_data}`")

            return jsonify(response_data)   # This function also takes care of the Content-Type header




        #####################################################################################################

        '''                                 ~  CATEGORY-RELATED   ~                                       '''

        def ________CATEGORY_RELATED________(DIVIDER):
            pass        # Used to get a better structure view in IDEs
        #####################################################################################################


        @bp.route('/delete_category/<uri>')
        @login_required
        def delete_category(uri):
            """
            Delete the specified Category, provided that there are no Content Items linked to it.

            EXAMPLE invocation: http://localhost:5000/BA/api/delete_category/123

            :param uri: The URI of a data node representing a Category

            RETURNED PAYLOAD (on success):
                None
            """
            try:
                Categories.delete_category(uri)
                response_data = {"status": "ok"}                                    # Successful termination
            except Exception as ex:
                err_details = f"Unable to delete the specified Category.  {exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}   # Error termination


            return jsonify(response_data)       # This function also takes care of the Content-Type header



        @bp.route('/add_subcategory', methods=['POST'])
        @login_required
        def add_subcategory():
            """
            Add a new Subcategory to a given Category
            (if the Subcategory to link up to already exists, use '/add_subcategory_relationship' instead)
            If a new Subcategory is successfully added, the server_payload will contain the newly-assigned URI

            EXAMPLE invocation:
                curl http://localhost:5000/BA/api/add_subcategory -d
                            "category_uri=some_category_uri&subcategory_name=SOME_NAME&subcategory_remarks=SOME_REMARKS"
        
            POST FIELDS:
                category_uri            URI to identify the Category to which to add the new Subcategory
                subcategory_name        The name to give to the new Subcategory
                subcategory_remarks     (OPTIONAL)  A comment field for the new Subcategory

            RETURNED PAYLOAD (on success):
                The URI of the newly-created Category Data Node
            """
            # Extract the POST values
            post_data = request.form     # Example: ImmutableMultiDict([('category_uri', 'cat-12'),
                                         #                              ('subcategory_name', 'Astronomy'),
                                         #                              ('subcategory_remarks', '')])
            #print(post_data)

            try:
                data_dict = cls.extract_post_pars(post_data, required_par_list=['category_uri', 'subcategory_name'])
                payload = Categories.add_subcategory(data_dict)     # The URI of the newly-created Category Data Node
                                                                    # TODO: maybe move to DataManager module
                response_data = {"status": "ok", "payload": payload}
            except Exception as ex:
                err_details = f"/add_subcategory : Unable to add the requested Subcategory.  {exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}        # Error termination
        
            #print(f"add_subcategory() is returning: `{response_data}`")

            return jsonify(response_data)   # This function also takes care of the Content-Type header
        

        
        @bp.route('/add_subcategory_relationship')
        @login_required
        def add_subcategory_relationship():
            """
            Create a subcategory relationship between 2 existing Categories.
            (To add a new subcategory to an existing Category, use /add_subcategory instead)

            Notice that this is a more specialized form of the more general /add_relationship

            EXAMPLE invocation: http://localhost:5000/BA/api/add_subcategory_relationship?sub=12&cat=1

            QUERY-STRINGS FIELDS:
                sub         URI to identify an existing Category node that is to be made a sub-category of another one
                cat         URI to identify an existing Category node that is to be made the parent of the other Category
            """
            # TODO: not in current use

            # Extract the GET values
            get_data = request.args     # Example: ImmutableMultiDict([('sub', '12'), ('cat', '555')])

            try:
                data_dict = cls.extract_get_pars(get_data, required_par_list=['sub', 'cat'])
                Categories.add_subcategory_relationship(data_dict)
                response_data = {"status": "ok"}
            except Exception as ex:
                err_details = f"Unable to add the requested relationship to the specified subcategory.  {exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}        # Error termination
        
            #print(f"add_subcategory_relationship() is returning: `{response_data}`")

            return jsonify(response_data)   # This function also takes care of the Content-Type header



        @bp.route('/pin_category/<uri>/<op>')
        @login_required
        def pin_category(uri, op):
            """
            Set or unset the "pinned" property of the specified Category

            EXAMPLE invocations: http://localhost:5000/BA/api/pin_category/123/set
                                 http://localhost:5000/BA/api/pin_category/123/unset

            :param uri: The URI of a data node representing a Category
            :param op:  Either "set" or "unset"

            RETURNED PAYLOAD (on success):
                Nothing
            """
            try:
                Categories.pin_category(uri=uri, op=op)
                response_data = {"status": "ok"}                                    # Successful termination
            except Exception as ex:
                err_details = f"Unable to change the 'pinned' status of the specified Category.  {exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}   # Error termination

            return jsonify(response_data)   # This function also takes care of the Content-Type header



        @bp.route('/see_also', methods=['POST'])
        @login_required
        def see_also():
            """
            Add or remove a "SEE ALSO" relationship between two given Categories

            EXAMPLE invocation:
                curl http://localhost:5000/BA/api/see_also -d
                            "from_category_uri=some_category_uri&to_category_uri=some_other_category_uri&action=add"

            POST FIELDS:
                from_category_uri       URI to identify the Category from which the "BA_see_also" link originates
                to_category_uri         URI to identify the Category towards which the "BA_see_also" link points
                action                  Either "add" or "remove"    TODO: possibly switch to using a "DELETE" HTTP method for the latter

            RETURNED PAYLOAD (on success):
                Nothing
            """
            # Extract the POST values
            post_data = request.form    # Example: ImmutableMultiDict([('from_category_uri', 'cat-12'),
                                        #                              ('to_category_uri', 'cat-4732'),
                                        #                              ('action', 'remove')])
            #print(post_data)

            try:
                data_dict = cls.extract_post_pars(post_data,
                                                  required_par_list=['from_category_uri', 'to_category_uri', 'action'])

                if data_dict["action"] == "add":
                    Categories.create_see_also(from_category=data_dict["from_category_uri"], to_category=data_dict["to_category_uri"])
                elif data_dict["action"] == "remove":
                    Categories.remove_see_also(from_category=data_dict["from_category_uri"], to_category=data_dict["to_category_uri"])
                else:
                    raise Exception(f"The parameter `action` in the POST request has an unknown value ({data_dict['action']}); "
                                    f"allowed values are 'add' and 'remove'")

                response_data = {"status": "ok"}
            except Exception as ex:
                err_details = f"/see_also : Unable to modify the requested 'SEE ALSO' link.  {exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}        # Error termination


            return jsonify(response_data)   # This function also takes care of the Content-Type header





        #####################################################################################################

        '''                      ~  CATEGORY PAGES  (CONTENT ITEMS in CATEGORIES)    ~                    '''

        def ________CATEGORY_PAGES________(DIVIDER):
            pass        # Used to get a better structure view in IDEs
        #####################################################################################################


        @bp.route('/add_item_to_category', methods=['POST'])
        @login_required
        def add_item_to_category():
            """
            Create a new Content Item attached to a particular Category,
            at a particular location in the "collection" (page)

            EXAMPLE invocation:
            curl http://localhost:5000/BA/api/add_item_to_category
                            -d "category_id=708&insert_after_uri=711&schema_code=h&text=New Header&class_name=Headers"

            POST FIELDS:
                category_id         URI identifying the Category to which attach the new Content Item
                class_name          The name of the Class of the new Content Item
                insert_after_uri    Either an URI of an existing Content Item attached to this Category,
                                    or one of the special values "TOP" or "BOTTOM"
                insert_after_class  The name of the Class of the preceding Content Item, if applicable
                *PLUS* any applicable plugin-specific fields

            RETURNED PAYLOAD (on success):
                The URI of the newly-created Data Node
            """
            # TODO: possibly phase out in favor of '/add_item_to_category_JSON' (below)
            # TODO: switch from "category_id" to "category_uri"
            # TODO: also return the newly-assigned "pos" value
            # Extract the POST values
            post_data = request.form
            # Example: ImmutableMultiDict([('category_id', '123'), ('class_name', 'Header'),
            #                              ('insert_after_uri', 'i-5'), ('insert_after_class', 'Image'), ('text', 'My Header')])
            #cls.show_post_data(post_data, "add_item_to_category")

            # Create a new Content Item with the POST data
            try:
                pars_dict = cls.extract_post_pars(post_data, required_par_list=['category_id', 'insert_after_uri', 'class_name'])
                #print("/add_item_to_category - pars_dict: ", pars_dict)
                # EXAMPLE: {'class_name': 'Header', 'category_id': '1', 'insert_after_uri': 'BOTTOM', 'text': 'My Header'}
                payload = DataManager.new_content_item_in_category(pars_dict)        # The URI of the newly-created Data Node
                response_data = {"status": "ok", "payload": payload}
            except Exception as ex:
                err_details = f"/add_item_to_category : Unable to add the requested Content Item to the specified Category.  " \
                              f"{exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}

            #print(f"add_item_to_category() is returning: `{err_details}`")

            return jsonify(response_data)   # This function also takes care of the Content-Type header



        @bp.route('/plugin/<handler>', methods=['POST'])
        @login_required
        def plugin(handler):
            """
            EXPERIMENTAL endpoint not yet in use.  Meant to support plugin-provided operations.

            POST VARIABLES:
                json    (REQUIRED) A JSON-encoded dict

            EXAMPLE invocation:     http://localhost:5000/BA/api/plugin/documents using a POST,
                                    and passing a body of [1,2,3] with mimetype "application/json"

            :param handler: The name of a plugin-handler class.  EXAMPLE: "documents"
            """
            print(f"Invoking /plugin/ endpoint for handler:  `{handler}`")
            # Extract and parse the POST value
            parameters = request.get_json()     # This parses the JSON-encoded string in the POST message,
                                                # provided that mimetype indicates "application/json"

            print("    parameters passed to the plugin: ", parameters)              # EXAMPLE:  [1, 2, 3]

            try:
                result = plugin_support.api_handler(handler, parameters)
                response_data = {"status": "ok", "payload": result}                  # Successful termination

            except Exception as ex:
                err_details =  f"Error from `{handler}` plugin.  {exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}   # Error termination

            return jsonify(response_data)   # This function also takes care of the Content-Type header



        @bp.route('/add_item_to_category_JSON', methods=['POST'])
        @login_required
        def add_item_to_category_JSON():
            """
            Create a new Content Item attached to a particular Category,
            at a particular location in the "collection" (page)

            This is variation of '/add_item_to_category' that expects to receive JSON data

            POST VARIABLES:
                json    (REQUIRED) A JSON-encoded dict

            KEYS in the JSON-encoded dict:
                category_uri        URI identifying the Category to which attach the new Content Item
                class_name          The name of the Class of the new Content Item
                insert_after_uri    Either an URI of an existing Content Item attached to this Category,
                                        or one of the special values "TOP" or "BOTTOM"
                insert_after_class  [OPTIONAL] The name of the Class of the preceding Content Item, if applicable
                *PLUS* any applicable plugin-specific fields

            RETURNED PAYLOAD (on success):
                The URI of the newly-created Data Node
            """
            #TODO:
            '''
            A possible general API design:
                required_fields = ["category_uri", "class_name", "insert_after_uri"]
                other_fields = ["insert_after_class"]
                allow_extra_fields = True
                handler = DataManager.add_new_content_item_to_category
                
            Then it automatically does field extraction and presence check,
            and finally makes a call to:  
                handler(category_uri=..., class_name=..., insert_after_uri=..., insert_after_class=...,
                        extra_fields=<the remaining dict>)   
            '''

            # Extract and parse the POST value
            pars_dict = request.get_json()      # This parses the JSON-encoded string in the POST message,
            # provided that mimetype indicates "application/json"
            # EXAMPLE: {'category_uri': '6967', 'class_name': 'Header', 'insert_after_uri': 'BOTTOM', 'text': 'My Header'}
            # See: https://flask.palletsprojects.com/en/1.1.x/api/
            #print("In add_item_to_category_JSON() -  pars_dict: ", pars_dict)

            # TODO: create a helper function for the unpacking/validation below
            category_uri = pars_dict.get('category_uri')
            class_name = pars_dict.get('class_name')
            insert_after_uri = pars_dict.get('insert_after_uri')
            insert_after_class = pars_dict.get('insert_after_class')    # NOT required if `insert_after_uri` is "TOP" or "BOTTOM"

            # TODO: this check for a required set of variables ought to be the ONLY responsibility of this layer!
            if not category_uri or not class_name or not insert_after_uri:
                err_details = f"add_item_to_category_JSON(): some required parameters are missing; " \
                              f"'category_uri', 'class_name' and 'insert_after_uri' are required"
                response_data = {"status": "error", "error_message": err_details}
                return jsonify(response_data), 400      # 400 is "Bad Request client error"


            # Create a new Content Item with the POST data
            try:
                del pars_dict["category_uri"]
                del pars_dict["class_name"]
                del pars_dict["insert_after_uri"]
                if "insert_after_class" in pars_dict:
                    del pars_dict["insert_after_class"]

                #print("Creating new Content Item with following properties: ", pars_dict)
                payload = DataManager.add_new_content_item_to_category(category_uri=category_uri, class_name=class_name,
                                                                       insert_after_uri=insert_after_uri, insert_after_class=insert_after_class,
                                                                       item_data=pars_dict)     # It returns the URI of the newly-created Data Node
                response_data = {"status": "ok", "payload": payload}
            except Exception as ex:
                err_details = f"/add_item_to_category_JSON : Unable to add the requested Content Item to the specified Category.  " \
                              f"{exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}

            #print(f"add_item_to_category_JSON() is returning: `{err_details}`")

            return jsonify(response_data)   # This function also takes care of the Content-Type header



        @bp.route('/link_content_at_end/<category_uri>/<item_uri>')
        @login_required
        def link_content_at_end(category_uri, item_uri):
            """
            Link an existing Content Item at the end of an existing Category

            EXAMPLE invocation: http://localhost:5000/BA/api/link_content_at_end/cat-123/i-222

            :param category_uri:    The URI of a data node representing a Category
            :param item_uri:        The URI of a data node representing a Content Item
            :return:                A Flask Response response object
                                    RETURNED PAYLOAD (on success):
                                        None
            """
            # TODO: maybe switch to a query string, to avoid errors in order of arguments
            try:
                Categories.link_content_at_end(category_uri=category_uri, item_uri=item_uri)
                response_data = {"status": "ok"}                                    # Successful termination
            except Exception as ex:
                err_details = f"Unable to attach Content Item (URI '{item_uri}') to the end of Category (URI '{category_uri}') .  " \
                              f"{exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}   # Error termination

            return jsonify(response_data)   # This function also takes care of the Content-Type header



        @bp.route('/get_categories_linked_to/<item_uri>')
        @login_required
        def get_categories_linked_to(item_uri):
            """
            Locate and return information about all the Categories
            that the given Content Item is linked to

            EXAMPLE invocation: http://localhost:5000/BA/api/get_categories_linked_to/n-123

            :param item_uri:        The URI of a data node representing a Content Item
            :return:                A Flask Response response object
                                    RETURNED PAYLOAD (on success):
                                        A (possibly empty) list of pairs [Category name, remarks]
                                        Any missing value will appear as null
                                        EXAMPLE:
                                                      "payload": [
                                                                    {
                                                                      "name": "Some Category name",
                                                                      "remarks": null,
                                                                      "uri": "cat-123"
                                                                    },
                                                                    {
                                                                      "name": ".A Test",
                                                                      "remarks": "my test",
                                                                      "uri": "cat-999"
                                                                    }
                                                                 ]
            """
            try:
                result = Categories.get_categories_linked_to_content_item(item_uri=item_uri)
                response_data = {"status": "ok", "payload": result}                         # Successful termination
            except Exception as ex:
                err_details = f"Problem in retrieving Categories to which the Content Item with URI '{item_uri}' is attached .  " \
                              f"{exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}           # Error termination

            return jsonify(response_data)       # This function also takes care of the Content-Type header



        @bp.route('/detach_from_category/<category_uri>/<item_uri>')
        @login_required
        def detach_from_category(category_uri, item_uri):
            """
            Sever the link from the specified Content Item and the given Category.
            If it's the only Category that the Content Item is currently linked to,
            an error is returned

            EXAMPLE invocation: http://localhost:5000/BA/api/detach_from_category/cat-123/i-222

            :param category_uri:    The URI of a data node representing a Category
            :param item_uri:        The URI of a data node representing a Content Item
            """
            # TODO: maybe switch to a query string, to avoid errors in order of arguments
            try:
                Categories.detach_from_category(category_uri=category_uri, item_uri=item_uri)
                response_data = {"status": "ok"}                                    # Successful termination
            except Exception as ex:
                err_details = f"Unable to detach Content Item (URI '{item_uri}') from Category (URI '{category_uri}') .  " \
                              f"{exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}   # Error termination

            return jsonify(response_data)   # This function also takes care of the Content-Type header



        @bp.route('/switch_category', methods=['POST'])
        @login_required
        def switch_category():
            """
            Switch one or more Content Items from being attached to a given Category,
            to another one

            POST VARIABLES:
                items   JSON-encoded list of URI's to relocate across Categories
                from    JSON-encoded string URI of the old Category
                to      JSON-encoded string URI of the new Category

            NO RETURNED PAYLOAD

            EXAMPLE invocation:
                curl http://localhost:5000/BA/api/switch_category  -d "items=[\"i-3332\", \"h-235\"]&from=\"3677\"&to=\"3676\""

            TODO: consider switching to passing just 1 POST variable named "json",
                  as done in 'get_class_properties'
            """
            # Extract the POST values
            post_data = request.form     # An ImmutableMultiDict

            try:
                data_dict = cls.extract_post_pars(post_data, required_par_list=['items', 'from', 'to'],
                                                  json_decode=True)
                #print("In '/switch_category' endpoint.  data_dict: ", data_dict)
                DataManager.switch_category(data_dict)
                response_data = {"status": "ok"}
            except Exception as ex:
                err_details = f"/switch_category : Unable to relocate Content Item(s) to new Category.  {exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}        # Error termination
                # TODO: manage scenario where SOME - but not all - items got successfully moved;
                #       maybe implement a standard "error_data" field

            return jsonify(response_data)   # This function also takes care of the Content-Type header





        #############    POSITIONING WITHIN CATEGORIES    #############
        
        @bp.route('/swap/<uri_1>/<uri_2>/<cat_id>')
        @login_required
        def swap(uri_1, uri_2, cat_id):
            """
            Swap the positions of the specified Content Items within the given Category.
        
            EXAMPLE invocation: http://localhost:5000/BA/api/swap/23/45/2
            """
            try:
                Categories.swap_content_items(uri_1, uri_2, cat_id)
                response_data = {"status": "ok"}                                    # Successful termination
            except Exception as ex:
                err_details = f"Unable to swap the requested Content Items.  {exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}   # Error termination

            #print(f"swap() is returning: `{response_data}`")

            return jsonify(response_data)   # This function also takes care of the Content-Type header
        
        
        
        @bp.route('/reposition/<category_uri>/<uri>/<move_after_n>')
        @login_required
        def reposition(category_uri, uri, move_after_n):
            """
            Reposition the given Content Item after the n-th item (counting starts with 1) in specified Category.
            Note: moving after the 0-th item means to move to the very top
        
            EXAMPLE invocation: http://localhost:5000/BA/api/reposition/60/576/4
            """
            #TODO: TODO: switch to an after-item version?

            try:
                Categories.reposition_content(category_uri=category_uri, uri=uri, move_after_n=int(move_after_n))
                response_data = {"status": "ok"}                                    # Successful termination
            except Exception as ex:
                err_details = f"Unable to reposition the Content Item.  {exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}   # Error termination
        
            #print(f"reposition() is returning: `{response_data}`")

            return jsonify(response_data)   # This function also takes care of the Content-Type header



        @bp.route('/add_label/<new_label>')
        @login_required
        def add_label(new_label):
            """
            Add a new blank node with the specified label.
            Return the internal database ID of the new node.
            Meant for testing.

            EXAMPLE invocation: http://localhost:5000/BA/api/add_label/Customer

            :param new_label:   String with the name of a Graph-Database label
            :return:            A Flask Response response object containing
                                    the internal database ID of the new node
            """
            try:
                internal_id = DataManager.add_new_label(new_label)
                response_data = {"status": "ok", "payload": internal_id}            # Successful termination
            except Exception as ex:
                err_details = f"Unable to create a new database node with the given label: `{new_label}`. " \
                              f"{exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}   # Error termination

            return jsonify(response_data)   # This function also takes care of the Content-Type header





        #####################################################################################################

        '''                                          ~   UTILS   ~                                        '''

        def ________UTILS________(DIVIDER):
            pass        # Used to get a better structure view in IDEs
        #####################################################################################################

        @bp.route('/fetch-remote-title')
        @login_required
        def fetch_remote_title():
            """
            Retrieve the Title of a remote webpage, given its URL.

            EXAMPLE invocation:
                http://localhost:5000/BA/api/fetch-remote-title?url=https://brainannex.org

            :return:    A Flask Response response object containing a JSON string
                            with the contents of the title of the page specified by the "url" query string,
                            or an error message in case the fetching webpage fails or its title cannot be extracted.
                            Note: any HTML entities in the title are turned into characters; e.g. "&ndash;" becomes "-"
            """
            remote_url = request.args.get('url')    # Extract the value of the "url" value from the query string
            #print(f"Attempting to retrieve remove web page {remote_url}")

            try:
                title = DataManager.extract_website_title(remote_url)
                response_data = {"status": "ok", "payload": title}                  # Successful termination

            except Exception as ex:
                err_details =  f"Error in fetching the remote page.  {exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}   # Error termination

            return jsonify(response_data)   # This function also takes care of the Content-Type header




        #####################################################################################################

        '''                                        ~   FILTERS   ~                                        '''

        def ________FILTERS________(DIVIDER):
            pass        # Used to get a better structure view in IDEs
        #####################################################################################################

        @bp.route('/field-names-by-class/<class_name>')
        @login_required
        def field_names_by_class(class_name):
            """
            Get all the field (property) names
            registered with that class name or, if no such class exists,
            retrieve field names typically associated with nodes with that label

            EXAMPLES of invocation: http://localhost:5000/BA/api/field-names-by-class/cars

            :param class_name:  The name of a Schema Class node, or of a database node label
            :return:            A JSON object with a list of field (property) names
                                EXAMPLE:
                                    {
                                        "status": "ok",
                                        "payload": ["my_field_1", "my_field_2"]
                                    }
            """
            #TODO: for now, we're just searching by label, rather than by Class
            try:
                # Fetch all the Properties of the given Class
                all_props = GraphSchema.db.sample_properties(label=class_name, sample_size=10)    # Set of strings
                payload = list(all_props)       # Convert set to list
                response = {"status": "ok", "payload": payload}    # Successful termination
            except Exception as ex:
                err_details = f"/field-names-by-class :  {exceptions.exception_helper(ex)}"
                response = {"status": "error", "error_message": err_details}    # Error termination

            return jsonify(response)   # This function also takes care of the Content-Type header


        
        @bp.route('/get_filtered')
        @login_required
        def get_filtered():
            """
            Perform a database search for particular nodes, and return their properties,
            as well as a total count.

            For example, for the use of a record search form or the recordset plugin

            EXAMPLE of invocation:
                http://localhost:5000//BA/api/get_filtered?json={"label":"German Vocabulary","key_name":["English","German"],"key_value":"sucht"}

            GET VARIABLE:
                json    A JSON-encoded dict, containing the following entries:

                    label       The name of a database node label
                    class       Not yet used (will get turned into `label` if label is missing)
                    key_name    A string, or list of strings, with the name of a node attribute;
                                    if provided, key_value must be passed, too
                    key_value   The required value for the above key; if provided, key_name must be passed, too.
                                    Note: no requirement for the key to be primary
                    order_by    Field name, or comma-separated list;
                                    each name may optionally be followed by "DESC"
                    skip        The number of initial entries (in the context of specified order) to skip
                    limit       The max number of entries to return

            RETURNED JSON PAYLOAD:
                recordset:   A list of dicts with the filtered data; each dict contains the data for a node,
                                including a field called "internal_id" that has the internal database ID,
                                and a field called "node_labels" with a list of the node's label names
                total_count: The total number of nodes in the database with the given label - NOT considering the remainder of the filter
                                if no label was provided, None
            """
            # Extract the GET values
            get_data = request.args     # Example: Example: ImmutableMultiDict([('json', 'SOME_JSON_ENCODED_DATA')])
            #print("get_data: ", get_data)

            try:
                # This operation might fail - if "json" keys is missing
                data_dict = cls.extract_get_pars(get_data, required_par_list=["json"])
                #print("data_dict: ", data_dict)
                # EXAMPLE: {'json': '{"label":"German Vocabulary","key_name":["English","German"],"key_value":"sucht"}'}
            except Exception as ex:
                err_details = exceptions.exception_helper(ex)
                response_data = {"status": "error", "error_message": err_details}        # Error termination
                #print(response_data["error_message"])
                return jsonify(response_data)    # This function also takes care of the Content-Type header


            json_str = data_dict["json"]
            # EXAMPLE: the STRING {"label":"German Vocabulary","key_name":["English","German"],"key_value":"sucht"}
            #print("get_filtered() - JSON string: ", json_str)

            # TODO: turn a lot of the code below into a JSON-helper method;
            #       in particular, add a "json_decode" arg to extract_get_pars()
            #       See approach in '/update_content_item_JSON'

            try:
                # This operation might fail - if there are problems in the JSON encoding
                json_data = json.loads(json_str)    # Turn the string into a Python object
                #print("Decoded JSON request: ", json_data)
                # EXAMPLE:  {'label': 'German Vocabulary', 'key_name': ['English', 'German'], 'key_value': 'sucht'}
            except Exception as ex:
                response_data = {"status": "error", "error_message": f"Failed parsing of JSON string in request. Incorrectly formatted.  {ex}"}
                #print(response_data["error_message"])
                return jsonify(response_data)    # This function also takes care of the Content-Type header


            #  TODO: for now, we're actually doing a database search by node label,
            #         rather than by Schema Class
            class_name = json_data.get("class")
            #label_name = json_data.get("label")

            if "label" not in json_data:
                json_data["label"] = class_name     # Use "class" in lieu of "label"

            if "class" in json_data:
                del json_data["class"]      # For now, "class" is not being passed


            try:
                recordset, total_count = DataManager.get_filtered(json_data)
                # `recordset` is a list of dicts, with all the fields of the search results
                # `total_count` is what the length of `recordset` would have been, in the absence of limit/skip value
                #print("    recordset: ", recordset)
                #print("    total_count: ", total_count)

                # Build a list from the original database-query result; for each "record" (list element which is a dict),
                #   take only its key/value pairs where the value has an acceptable type.
                #   This is done to remove "bytes" values (for example, encoded passwords) and other quantities
                #   that aren't serializable with JSON
                sanitized_recordset = [{k: v for k, v in record.items()
                                            if (type(v) == str or type(v) == int or type(v) == bool or type(v) == list) }
                                       for record in recordset]

                response = {"status": "ok",
                            "payload": {"recordset": sanitized_recordset, "total_count": total_count}}   # Successful termination
                #print(f"get_filtered() is returning successfully: `{response}`")
                return jsonify(response)        # This function also takes care of the Content-Type header
                                                #   Note: jsonify() may fail if any parts of the response are not JSON serializable

            except Exception as ex:
                response = {"status": "error", "error_message": f"/get_filtered web API endpoint: {ex}" }    # Error termination
                #print(f"get_filtered() is returning with error: `{response}`")
                return jsonify(response)        # This function also takes care of the Content-Type header
                                                # Maybe, do this instead:
                                                # response = make_response(response["error_message"], 422)  # "422 Unprocessable Entity"
                                                # return response






        #####################################################################################################

        '''                          ~   IMPORT/EXPORT (incl. Upload/Download)   ~                        '''

        def ________IMPORT_EXPORT________(DIVIDER):
            pass        # Used to get a better structure view in IDEs
        #####################################################################################################

        @bp.route('/import_json_file', methods=['POST'])
        @login_required
        def import_json_file():
            """
            Upload and import of a data file in JSON format
            Invoke with the URL: http://localhost:5000/BA/api/import_json_file
            """
            # Extract the POST values
            post_data = request.form     # Example: ImmutableMultiDict([('use_schema', 'SCHEMA'), ('schema_class', 'my_class_name')])
            cls.show_post_data(post_data, "import_json_file")

            #print("request.files: ", request.files)
            # EXAMPLE: ImmutableMultiDict([('file', <FileStorage: 'julian_test.json' ('application/json')>)])

            #explain_flask_request(request)

            try:
                post_pars = cls.extract_post_pars(post_data, required_par_list=["use_schema"])
                result = DataManager.upload_import_json_file(files=request.files, upload_dir=cls.config_pars['UPLOAD_FOLDER'],
                                                             post_pars=post_pars, verbose=False)
                response = {"status": "ok", "payload": result}              # Successful termination
            except Exception as ex:
                response = {"status": "error", "error_message": str(ex)}    # Error termination

            print(f"import_json_file() is returning: `{response}`")

            return jsonify(response)   # This function also takes care of the Content-Type header



        @bp.route('/stop_data_intake')
        @login_required
        def stop_data_intake():
            """
            Invoke with the URL: http://localhost:5000/BA/api/stop_data_intake
            """
            try:
                DataManager.do_stop_data_intake()
                response_data = {"status": "ok"}              # If no errors
            except Exception as ex:
                err_details = f"Unable to stop the data-intake process.  {exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}        # Error termination

            #print(f"stop_data_intake() is returning: `{err_details}`")

            return jsonify(response_data)   # This function also takes care of the Content-Type header



        @bp.route('/bulk_import', methods=['POST'])
        @login_required
        def bulk_import():
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

                result = DataManager.do_bulk_import(intake_folder, outtake_folder, schema_class)

                response = {"status": "ok", "result": result}              # Successful termination
            except Exception as ex:
                response = {"status": "error", "error_message":  exceptions.exception_helper(ex)}    # Error termination

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

            #explain_flask_request(request)

            return_url = request.form["return_url"] # This originates from the HTML form :
            #    <input type="hidden" name="return_url" value="my_return_url">
            #print("return_url: ", return_url)
        
            status = DataManager.upload_import_json(files=request.files, upload_dir=cls.config_pars['UPLOAD_FOLDER'],
                                                    return_url=return_url, verbose=False)
            return status
        
        
        
        @bp.route('/upload_media', methods=['POST'])
        @login_required
        def upload_media():
            """
            Upload new media Content, to the (specified or default) media folder, and attach it to the Category
            specified in the POST variable "category_id"

            USAGE EXAMPLE:
                <form enctype="multipart/form-data" method="POST" action="/BA/api/upload_media">
                    <input type="file" name="file"><br>   <!-- IMPORTANT: the API handler expects the name value to be "file" -->
                    <input type="submit" value="Upload your file">
                    <input type='hidden' name='category_id' value='123'>
                    <input type='hidden' name='insert_after_uri' value='rs-2'>
                    <input type='hidden' name='insert_after_class' value='Recordset'>
                    <input type='hidden' name='upload_folder' value='documents/Ebooks & Articles'>    <!-- OPTIONAL -->
                </form>

            The 'insert_after_uri' attribute also can take the special values 'INSERT_AT_BOTTOM' or 'INSERT_AT_TOP'
        
            (Note: the "Dropzone" front-end module invokes this handler in a similar way,
                   and in particular uses name="file")
        
            If the upload is successful, a normal status (200) is returned (no response data);
                in case of error, a server error status is return (500), with a text error message
            """
            # TODO: move a lot of this function to MediaManager
            # TODO: media is currently added to a folder determined by its media type (image vs. document)

            # Extract the POST values
            post_data = request.form    # Example: ImmutableMultiDict([('category_id', '3677'),
                                        #                              ('insert_after_uri', 'rs-2'),
                                        #                              ('upload_folder', 'documents/Ebooks & Articles')])
        
            print("Uploading media content thru upload_media()")
            #print("Raw POST data: ", post_data)
            print("POST variables: ", dict(post_data))  # EXAMPLE: {'category_id': '3677', 'insert_after_uri': 'rs-2',
                                                        #           'upload_folder': 'documents/Ebooks & Articles'}
                                                        # Note that 'upload_folder' is optional
        
            try:
                upload_dir = current_app.config['UPLOAD_FOLDER']    # The name of the *temporary* directory used for the uploads.
                                                                    #   EXAMPLES: "/tmp/" (Linux)  or  "D:/tmp/" (Windows)
                (tmp_filename_for_upload, full_filename, original_name, mime_type) = \
                            UploadHelper.store_uploaded_file(files=request.files, upload_dir=upload_dir, key_name="file")
                print(f"    Upload successful so far for file: `{tmp_filename_for_upload}` .  Full name: `{full_filename}`")
            except Exception as ex:
                err_status = f"<b>ERROR in upload</b>: {ex}"
                print("upload_media(): ", err_status)
                response = make_response(err_status, 500)
                return response


            # Map the MIME type of the uploaded file into a schema_code
            # TODO: maybe store the MIME type in the database, or in the plugin helper?
            #       For now, the Schema Class is inferred from the MIME type of the file
            if mime_type.split('/')[0] == "image":  # For example, 'image/jpeg', 'image/png', etc.
                class_name = "Image"
            else:
                class_name = "Document"            # Any unrecognized MIME type is treated as a Document


            # Move the uploaded file from its temp location to the appropriate media folder (depending on class_name)
            # TODO: let upload_helper (optionally) handle it
        
            src_fullname = cls.UPLOAD_FOLDER + tmp_filename_for_upload

            if not post_data.get("upload_folder"):    # If not explicitly passed (EXAMPLE: "documents/Ebooks & Articles")
                dest_folder = MediaManager.default_file_path(class_name=class_name)
            else:
                dest_folder = cls.config_pars["MEDIA_FOLDER"] + post_data["upload_folder"] + "/"

            dest_fullname = dest_folder + tmp_filename_for_upload

            #print(f"upload_media(): Attempting to move file `{src_fullname}` to `{dest_fullname}`")
            try:
                shutil.move(src_fullname, dest_fullname)    # Note: this will fail if the path to the destination file isn't already present
            except Exception:
                # This failure might be due to the folder dest_folder not being present
                print(f"upload_media(): Failed to move the uploaded file '{src_fullname}' to its intended destination '{dest_fullname}'.  "
                      f"Attempting to automatically correct, if that was due to a missing destination folder")

                # Attempt to remedy the problem by creating the appropriate media folder - in case it was missing
                MediaManager.create_folder(name=dest_folder)

                # Try again after creating the media folder (if that was indeed missing)
                try:
                    shutil.move(src_fullname, dest_fullname)
                except Exception as ex:
                    err_status = f"Error in moving the file to the intended final destination ({dest_folder}) after upload. {ex}"
                    return make_response(err_status, 500)

        
            category_uri = post_data["category_id"]


            (basename, suffix) = os.path.splitext(tmp_filename_for_upload)  # EXAMPLE: "test.jpg" becomes
                                                                            #          ("test", ".jpg")
            if suffix:
                suffix = suffix[1:]         # Drop the first character (the ".")  EXAMPLE: "jpg"

            properties = {"basename": basename, "suffix": suffix}

            # TODO: turn into a call to a plugin-provided method, prior to database add
            if class_name == "Image":
                # This is specifically for Images
                try:
                    extra_properties = ImageProcessing.process_uploaded_image(media_folder=dest_folder,
                                                                              basename=basename, suffix=suffix)
                    # `extra_properties` is a  dictionary of extra properties to store in database,
                    # and may contain the following keys: "caption", "width", "height"

                except Exception:
                    extra_properties = {}       # Nothing else to save in the database
                    '''
                    err_status = "Unable to save, or make a thumb from, the uploaded image. " \
                                 + exceptions.exception_helper(ex)
                    return make_response(err_status, 500)
                    '''
            else:
                # This is specifically for Documents
                extra_properties = {"caption": basename}        # Add another attribute

            #print("upload_media(): extra_properties: ", extra_properties)
            properties.update(extra_properties)     # Merge the extra dictionary into the main one
            #print("upload_media(): properties: ", properties)


            # Update the database
            # TODO: switch over to using DataManager.new_content_item_in_category_final_step()
            try:
                insertion_location = post_data.get('insert_after_uri')
                insertion_class = post_data.get('insert_after_class')
                if (insertion_location == "INSERT_AT_BOTTOM") or (not insertion_location) or (not insertion_class):
                    # Note: in case the insertion position isn't fully specified, the Item will inserted at the bottom of the Category Page
                    print(f"    Inserting new Media Item at *bottom* of the Category page")
                    new_uri = Categories.add_content_at_end(category_uri=category_uri,
                                                            item_class_name=class_name, item_properties=properties)
                else:
                    print(f"    Inserting new Media Item after Category page element with URI `{insertion_location}`")
                    new_uri = Categories.add_content_after_element(category_uri=category_uri,
                                                                   item_class_name=class_name, item_properties=properties,
                                                                   insert_after_uri=insertion_location, insert_after_class=insertion_class)

                # Let the appropriate plugin handle anything they need to wrap up the operation
                if class_name == "Document":    # TODO: move to plugin_support.py
                    Documents.new_content_item_successful(uri=new_uri, pars=properties, mime_type=mime_type,
                                                          upload_folder=post_data.get("upload_folder"))

                response = ""

            except Exception as ex:
                err_status = "Unable to store the file in the database. " + exceptions.exception_helper(ex)
                print("upload_media(): ", err_status)
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
                (tmp_filename_for_upload, full_filename, original_name, mime_type) = \
                        UploadHelper.store_uploaded_file(files=request.files, upload_dir=upload_dir, key_name="file")
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
            The regular expression for the parsing is currently hardwired in APIRequestHandler.import_datafile()
            Typically, the uploads are initiated by forms containing:
                <input type="file" name="imported_datafile">
                <input type="hidden" name="return_url" value="my_return_url">
                <input type="submit" value="Import data file">

            Note:       name="imported_datafile"
                            and
                        name="return_url"

                        must be exactly as stated
        
            EXAMPLE invocation: http://localhost:5000/BA/api/parse_datafile
        
            :return:    String with status message
            """
        
            if request.method != 'POST':
                return "This endpoint requires POST data (you invoked it with a GET method.) No action taken..."   # Handy for testing
        
            try:
                # Manage the upload
                upload_dir = current_app.config['UPLOAD_FOLDER']    # Defined in main file
                (tmp_filename_for_upload, full_filename, original_name, mime_type) = \
                        UploadHelper.store_uploaded_file(files=request.files, upload_dir=upload_dir, key_name="imported_datafile")
            except Exception as ex:
                return f"<b>ERROR in upload</b>: {ex}"
        
            #print("In import_datafile(): ", (tmp_filename_for_upload, full_filename, original_name))
        
            return_url = request.form["return_url"] # This originates from the HTML form - namely the line:
                                                    #    <input type="hidden" name="return_url" value="my_return_url">
            #print("return_url: ", return_url)

            #status_msg = "Testing"
            status_msg = DataManager.import_datafile(tmp_filename_for_upload, full_filename, test_only=True)

            # Provide a return link
            status_msg += f" <a href='{return_url}' style='margin-left:50px'>GO BACK</a><br><br>"
        
            return status_msg



        @bp.route('/document_python', methods=['GET', 'POST'])
        @login_required
        def document_python() -> str:
            """
            EXPERIMENTAL!  Upload and parse a python file (with some expectations about its formatting),
            and then generate HTML code to create a documentation page.
            The regular expression for the parsing is currently hardwired in DocumentationGenerator.import_python_file()
            Typically, the uploads are initiated by forms containing:
                <input type="file" name="imported_datafile">
                <input type="hidden" name="return_url" value="my_return_url">
                <input type="submit" value="Import data file">

            Note:       name="imported_datafile"
                            and
                        name="return_url"

                        must be exactly as stated

            EXAMPLE invocation: http://localhost:5000/BA/api/parse_datafile

            :return:    String with status message
            """

            if request.method != 'POST':
                return "This endpoint requires POST data (you invoked it with a GET method.) No action taken..."   # Handy for testing

            try:
                # Manage the upload
                upload_dir = current_app.config['UPLOAD_FOLDER']    # Defined in main file
                (tmp_filename_for_upload, full_filename, original_name, mime_type) = \
                        UploadHelper.store_uploaded_file(files=request.files, upload_dir=upload_dir, key_name="imported_datafile")
            except Exception as ex:
                return f"<b>ERROR in upload</b>: {ex}"

            print("In import_datafile(): ", (tmp_filename_for_upload, full_filename, original_name))

            return_url = request.form["return_url"] # This originates from the HTML form - namely the line:
            #    <input type="hidden" name="return_url" value="my_return_url">
            #print("return_url: ", return_url)

            status_msg = f"<a href='{return_url}' style='margin-left:10px; font-weight:bold'>GO BACK</a><br><br>"
            status_msg += DocumentationGenerator.import_python_file(tmp_filename_for_upload, full_filename)

            # Provide a return link
            status_msg += f" <a href='{return_url}' style='margin-left:10px; font-weight:bold'>GO BACK</a><br><br>"

            return status_msg



        @bp.route('/download_dbase_json/<download_type>')
        @login_required
        def download_dbase_json(download_type="full"):
            """
            Download the Neo4j database (either all or part) as a JSON file
        
            EXAMPLES invocation:
                http://localhost:5000/BA/api/download_dbase_json/full
                http://localhost:5000/BA/api/download_dbase_json/schema

            EXAMPLE of exported file:

            [
                {"type":"node","id":"3","labels":["User"],"properties":{"name":"Adam","age":32,"male":true}},\n
                {"type":"node","id":"4","labels":["User"],"properties":{"name":"Eve","age":18}},\n
                {"type":"relationship","id":"1","label":"KNOWS","properties":{"since":2003},"start":{"id":"3","labels":["User"]},"end":{"id":"4","labels":["User"]}}\n
            ]

            If database is large, it may lead to errors:  java.lang.OutOfMemoryError: Java heap space.
            See manual: https://neo4j.com/docs/operations-manual/4.4/performance/memory-configuration/
        
            :param download_type:   Either "full" (default) or "schema"
            :return:                A Flask response object, with HTTP headers that will initiate a download
            """
            try:
                if download_type == "full":
                    result = DataManager.export_full_dbase()
                    export_filename = "exported_dbase.json"
                elif download_type == "schema":
                    result = GraphSchema.export_schema()
                    export_filename = "exported_schema.json"
                else:
                    return f"Unknown requested type of download: {download_type}"
            except Exception as ex:
                    response = exceptions.exception_helper(ex)
                    error_page_body = f'''<b>Unable to perform download</b>. <br>
                                          This is typically due to the 'APOC' library not being installed on Neo4j,
                                          unless the error message below indicates something else. 
                                          If it says OutOfMemoryError, the Neo4j configuration file needs to be changed. 
                                          Contact your Neo4j database administrator.
                                          <br><br>{response}"
                                       '''
                    return error_page_body
                    # TODO: have a special page to display errors like this one
        
            # result is a dict with 4 keys
            print(f"Getting ready to export {result.get('nodes')} nodes, "
                  f"{result.get('relationships')} relationships, and {result.get('properties')} properties")

            # Note that we're only returning the value of the "data" key
            # TODO: move this part to DataManager.export_full_dbase()
            data = result["data"]

            response = make_response(data)
            response.headers['Content-Type'] = 'application/save'
            response.headers['Content-Disposition'] = f'attachment; filename=\"{export_filename}\"'
            return response


        ##################  END OF ROUTING DEFINITIONS  ##################
        