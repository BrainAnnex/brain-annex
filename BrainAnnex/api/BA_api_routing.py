"""
    Web API endpoint
    MIT License.  Copyright (c) 2021-2024 Julian A. West
"""

from flask import Blueprint, jsonify, request, current_app, make_response  # The request package makes available a GLOBAL request object
from flask_login import login_required
from BrainAnnex.modules.data_manager.data_manager import DataManager
from BrainAnnex.modules.data_manager.documentation_generator import DocumentationGenerator
from BrainAnnex.modules.media_manager.media_manager import MediaManager, ImageProcessing
from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema
from BrainAnnex.modules.categories.categories import Categories
from BrainAnnex.modules.PLUGINS.documents import Documents
from BrainAnnex.modules.upload_helper.upload_helper import UploadHelper
import BrainAnnex.modules.utilities.exceptions as exceptions                # To give better info on Exceptions
import shutil
import os
#from time import sleep     # For tests of delays in asynchronous fetching.  E.g. sleep(3) for 3 secs



class ApiRouting:
    """
    Setup, routing and endpoints for all the web pages served by this module.
    Note that this class does not directly interact with the database.

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



    # NOTE: To test POST-based web APIs, on the Linux shell or Windows PowerShell issue commands such as:
    #            curl http://localhost:5000/BA/api/add_item_to_category -d "schema_id=1&category_id=60"




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
    def extract_get_pars(cls, get_data, required_par_list=None) -> dict:
        """

        :param get_data:
        :param required_par_list:
        :return:
        """
        data_dict = get_data.to_dict(flat=True)     # WARNING: if multiple identical keys occur,
                                                    #          the values associated to the later keys will be discarded
        if required_par_list:
            for par in required_par_list:
                assert par in data_dict, f"The expected parameter `{par}` is missing from the GET request (i.e. from the query string)"

        return data_dict



    @classmethod
    def extract_post_pars(cls, post_data, required_par_list=None) -> dict:
        """
        Convert into a Python dictionary the given POST data
        (expressed as an ImmutableMultiDict) - ASSUMED TO HAVE UNIQUE KEYS -
        while enforcing the optional given list of parameters that must be present.
        In case of errors (or missing required parameters), an Exception is raised.

        EXAMPLE:
                post_data = request.form
                post_pars = cls.extract_post_pars(post_data, ["name_of_some_required_field"])

        :param post_data:           An ImmutableMultiDict object, which is a sub-class of Dictionary
                                    that can contain multiple values for the same key.
                                    EXAMPLE: ImmutableMultiDict([('uri', '123'), ('rel_name', 'BA_served_at')])

        :param required_par_list:   A list or tuple.  EXAMPLE: ['uri', 'rel_name']
        :return:                    A dict populated with the POST data
        """
        #TODO: instead of accepting "post_data" as argument,
        #      extract it here, with a:  post_data = request.form  (and optional call to show_post_data)

        #TODO:  maybe optionally pass a list of pars that must be int, and handle conversion and errors;
        #       but maybe the parameter validation doesn't belong to this API module, which ought to remain thin
        #       Example - int_pars = ['uri']

        #TODO: merge with UploadHelper.get_form_data()

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
        
        #---------------------------------------------#
        #              SCHEMA-related (reading)       #
        #---------------------------------------------#

        #"@" signifies a decorator - a way to wrap a function and modify its behavior
        @bp.route('/get_properties_by_class_name', methods=['POST'])
        #@login_required
        def get_properties_by_class_name():
            """
            Get all Properties of the given Class node (as specified by its name passed as a POST variable),
            including indirect ones that arise thru chains of outbound "INSTANCE_OF" relationships.
            Return a JSON object with a list of the Property names of that Class.

            EXAMPLE invocation:
                curl http://localhost:5000/BA/api/get_properties_by_class_name  -d "class_name=French Vocabulary"

            1 POST FIELD:
                class_name
                TODO: add an optional extra field, "include_ancestors"

            :return:  A JSON with a list of the Property names of the specified Class,
                      including indirect ones that arise thru
                      chains of outbound "INSTANCE_OF" relationships (TODO: make optional)
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
                #schema_id = NeoSchema.get_class_id(class_name)
                #if schema_id == -1:
                    #response = {"status": "error", "error_message": f"Unable to locate any Class named `{class_name}`"}
                #else:
                try:
                    # Fetch all the Properties
                    prop_list = NeoSchema.get_class_properties(class_node=class_name, include_ancestors=True)
                    response = {"status": "ok", "payload": prop_list}
                except Exception as ex:
                    response = {"status": "error", "error_message": str(ex)}

            #print(f"get_properties_by_class_name() is returning: `{response}`")

            return jsonify(response)   # This function also takes care of the Content-Type header



        @bp.route('/get_links/<schema_id>')
        @login_required
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
        @login_required
        def get_class_schema():
            """
            Get all Schema data - both Properties and Links - of the given Class node
            (as specified by its name passed as a POST variable),
            including indirect Properties thru chains of outbound "INSTANCE_OF" relationships.
            Properties marked as "system" ones gets excluded.

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
            #cls.show_post_data(post_data, "get_class_schema")

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
                        prop_list = NeoSchema.get_class_properties(class_name, include_ancestors=True, exclude_system=True)
                        rel_names = NeoSchema.get_class_relationships(int(schema_id), omit_instance=True)
                        payload = {"properties": prop_list, "in_links": rel_names["in"], "out_links": rel_names["out"]}
                        response = {"status": "ok", "payload": payload}
                    except Exception as ex:
                        response = {"status": "error", "error_message": str(ex)}

            #print(f"get_class_schema() is returning: `{response}`")

            return jsonify(response)   # This function also takes care of the Content-Type header



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
        
            print(f"get_record_classes() is returning: `{response}`")
        
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
                                      "Notes",
                                      "English",
                                      "French"
                                    ]
            """
            prop_list = NeoSchema.all_properties("BA", "uri", uri)
            response = {"status": "ok", "payload": prop_list}
            # TODO: handle error scenarios

            return jsonify(response)   # This function also takes care of the Content-Type header




        #####################################################################################################

        '''                   ~   SCHEMA_RELATED (creating/editing/deleting)  ~                           '''

        def ________SCHEMA_RELATED________(DIVIDER):
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
            post_data = request.form     # Example: ImmutableMultiDict([('data', 'Quotes,quote,attribution,notes')])
            #cls.show_post_data(post_data, "create_new_schema_class")

            try:
                class_specs = cls.extract_post_pars(post_data, required_par_list=["new_class_name"])
                DataManager.new_schema_class(class_specs)
                response_data = {"status": "ok"}                                    # Success
            except Exception as ex:
                err_details = f"Unable to create a new Schema Class.  {exceptions.exception_helper(ex)}"
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
            or if data nodes attached to that Class are present (those need to be deleted first)

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
                NeoSchema.delete_class(name=pars_dict["class_name"], safe_delete=True)
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
            Retrieve and return the contents of a TEXT media item (for now, just "Notes")

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
                payload = DataManager.get_text_media_content(uri, "n")
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
                2) specifically for Notes
                3) it only serves items that are marked as "public" in the database

            EXAMPLE invocation: http://localhost:5000/BA/api/remote_access_note/123
            """
            try:
                payload = DataManager.get_text_media_content(uri, "n", public_required=True)
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



        @bp.route('/serve_media/<uri>')
        @bp.route('/serve_media/<uri>/<th>')
        @login_required
        def serve_media(uri, th=None):
            """
            Retrieve and return the contents of a data media item (for now, just Images or Documents.)
            If ANY value is specified for the argument "th", then the thumbnail version is returned (only
                applicable to images)

            EXAMPLE invocation: http://localhost:5000/BA/api/serve_media/1234

            :param uri: The URI of a data node representing a media Item (such as an "Image" or "Document")
            :param th:  Only applicable to Images.  If not None, then the thumbnail version is returned
            :return:    A Flask Response object containing the data for the requested media,
                            with a header setting the MIME type appropriate for the media format
                        In case the media isn't found, a 404 response status is sent,
                            together with an error message
            """
            try:
                (suffix, content) = MediaManager.get_binary_content(uri, th)
                response = make_response(content)
                # Set the MIME type
                mime_type = MediaManager.get_mime_type(suffix)
                response.headers['Content-Type'] = mime_type
                #print(f"serve_media() is returning the contents of data file, with file suffix `{suffix}`.  "
                #      f"Serving with MIME type `{mime_type}`")
            except Exception as ex:
                err_details = f"Unable to retrieve Media Item with URI `{uri}`. {exceptions.exception_helper(ex)}"
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



        @bp.route('/get_records_by_link', methods=['POST'])
        @login_required
        def get_records_by_link_api():
            """
            Locate and return the data of the nodes linked to the one specified by uri,
            by the relationship named by rel_name, in the direction specified by dir
            EXAMPLE invocation:
                curl http://localhost:5000/BA/api/get_records_by_link -d "uri=123&rel_name=BA_served_at&dir=IN"
            """
            # Extract the POST values
            post_data = request.form
            # EXAMPLE: ImmutableMultiDict([('uri', '123'), ('rel_name', 'BA_served_at'), ('dir', 'IN')])
            #cls.show_post_data(post_data)

            try:
                data_dict = cls.extract_post_pars(post_data, required_par_list=['uri', 'rel_name', 'dir'])
                data_dict["uri"] = data_dict["uri"]
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

        @bp.route('/update', methods=['POST'])
        @login_required
        def update():
            """
            Update an existing Content Item.
            NOTE: the "schema_code" field in the POST data is currently required, but it's redundant.  Only
                  used as a safety mechanism against incorrect values of their uri

            EXAMPLES of invocation:
                curl http://localhost:5000/BA/api/update -d "uri=11&schema_code=h&text=my_header"
                curl http://localhost:5000/BA/api/update -d "uri=62&schema_code=r&English=Love&German=Liebe"
            """
            #TODO: maybe pass the Class name instead of the "schema_code", as a redundant field

            # Extract the POST values
            post_data = request.form    # Example: ImmutableMultiDict([('uri', '11'), ('schema_code', 'r')])
            #cls.show_post_data(post_data, "update")

            try:
                data_dict = cls.extract_post_pars(post_data, required_par_list=['uri'])
                DataManager.update_content_item(data_dict)
                response_data = {"status": "ok"}                                    # If no errors
            except Exception as ex:
                err_details = f"Unable to update the requested Content Item.  {exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}   # Error termination
        
            #print(f"update() is returning: `{response_data}`")

            return jsonify(response_data)   # This function also takes care of the Content-Type header



        @bp.route('/delete/<uri>/<schema_code>')
        @login_required
        def delete(uri, schema_code):
            """
            Delete the specified Content Item.
            Note that schema_code is redundant.  Only used
            as a safety mechanism against incorrect values of their uri

            EXAMPLE invocation: http://localhost:5000/BA/api/delete/46/n
            """
            try:
                DataManager.delete_content_item(uri, schema_code)
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

        '''                 ~  CATEGORY-RELATED  (incl. adding new Content Items)    ~                    '''

        def ________CATEGORY_RELATED________(DIVIDER):
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
                            -d "category_id=708&insert_after=711&schema_code=h&text=New Header"
        
            POST FIELDS:
                category_id         URI identifying the Category to which attach the new Content Item
                schema_code         A string to identify the Schema that the new Content Item belongs to
                insert_after        Either an URI of an existing Content Item attached to this Category,
                                    or one of the special values "TOP" or "BOTTOM"
                *PLUS* any applicable plugin-specific fields
            """
            # Extract the POST values
            post_data = request.form
            # Example: ImmutableMultiDict([('category_id', '123'), ('schema_code', 'h'), ('insert_after', '5'), ('text', 'My Header')])
            #cls.show_post_data(post_data, "add_item_to_category")
        
            # Create a new Content Item with the POST data
            try:
                pars_dict = cls.extract_post_pars(post_data, required_par_list=['category_id', 'schema_code', 'insert_after'])
                payload = DataManager.new_content_item_in_category(pars_dict)        # Include the newly-added ID as a payload
                response_data = {"status": "ok", "payload": payload}
            except Exception as ex:
                err_details = f"Unable to add the requested Content Item to the specified Category.  {exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}

            #print(f"add_item_to_category() is returning: `{err_details}`")

            return jsonify(response_data)   # This function also takes care of the Content-Type header



        @bp.route('/delete_category/<uri>')
        @login_required
        def delete_category(uri):
            """
            Delete the specified Category, provided that there are no Content Items linked to it.

            EXAMPLE invocation: http://localhost:5000/BA/api/delete_category/123

            :param uri: The URI of a data node representing a Category
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
            (if the Subcategory to link up to already exists, use add_subcategory_relationship instead)

            EXAMPLE invocation:
                curl http://localhost:5000/BA/api/add_subcategory -d
                            "category_id=some_category_uri&subcategory_name=SOME_NAME&subcategory_remarks=SOME_REMARKS"
        
            POST FIELDS:
                category_id                     URI to identify the Category to which to add the new Subcategory
                subcategory_name                The name to give to the new Subcategory
                subcategory_remarks (optional)  A comment field for the new Subcategory
            """
            # Extract the POST values
            post_data = request.form     # Example: ImmutableMultiDict([('category_id', '12'), ('subcategory_name', 'Astronomy')])

            try:
                data_dict = cls.extract_post_pars(post_data, required_par_list=['category_id', 'subcategory_name'])
                payload = Categories.add_subcategory(data_dict)     # Include the newly-added ID as a payload
                response_data = {"status": "ok", "payload": payload}
            except Exception as ex:
                err_details = f"Unable to add the requested Subcategory.  {exceptions.exception_helper(ex)}"
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
                #print(get_data)
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
            """
            try:
                Categories.pin_category(uri=uri, op=op)
                response_data = {"status": "ok"}                                    # Successful termination
            except Exception as ex:
                err_details = f"Unable to change the 'pinned' status of the specified Category.  {exceptions.exception_helper(ex)}"
                response_data = {"status": "error", "error_message": err_details}   # Error termination

            return jsonify(response_data)   # This function also takes care of the Content-Type header



        @bp.route('/link_content_at_end/<category_uri>/<item_uri>')
        @login_required
        def link_content_at_end(category_uri, item_uri):
            """
            Link an existing Content Item at the end of an existing Category

            EXAMPLE invocation: http://localhost:5000/BA/api/link_content_at_end/cat-123/i-222

            :param category_uri:    The URI of a data node representing a Category
            :param item_uri:        The URI of a data node representing a Content Item
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
        
        
        
        @bp.route('/reposition/<category_id>/<uri>/<move_after_n>')
        @login_required
        def reposition(category_id, uri, move_after_n):
            """
            Reposition the given Content Item after the n-th item (counting starts with 1) in specified Category.
            Note: moving after the 0-th item means to move to the very top
            TODO: switch to an after-item version?
        
            EXAMPLE invocation: http://localhost:5000/BA/api/reposition/60/576/4
            """
            try:
                Categories.reposition_content(category_uri=category_id, uri=uri, move_after_n=int(move_after_n))
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
            Mostly used for testing.

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

        @bp.route('/get-filtered-json', methods=['POST'])
        @login_required
        def get_filtered_JSON():     # *** NOT IN CURRENT USE; see get_filtered() ***
            """
            Note: a form-data version is also available
        
            EXAMPLE invocation -    send a POST request to http://localhost:5000/BA/api/get-filtered-json
                                    with body:
                                    {"label":"BA", "key_name":"uri", "key_value":123}
        
                On Win7 command prompt (but NOT the PowerShell!!), do:
                    curl http://localhost:5000/BA/api/get-filtered-json -d "{\"label\":\"BA\", \"key_name\":\"uri\", \"key_value\":123}"
        
            JSON KEYS (all optional):
                label       To name of a single Neo4j label
                key_name    A string with the name of a node attribute; if provided, key_value must be present, too
                key_value   The required value for the above key; if provided, key_name must be present, too
                                        Note: no requirement for the key to be primary
            """
            # Extract the POST values
            #post_data = request.form
            #json_data = dict(post_data).get("json")     # EXAMPLE: '{"label": "BA", "key_name": "uri", "key_value": 123}'
        
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
        def get_filtered():
            """
            Note: a JSON version is also available
        
            EXAMPLES of invocation:
                curl http://localhost:5000/BA/api/get_filtered -d "labels=BA&key_name=uri&key_value=123"
                curl http://localhost:5000/BA/api/get_filtered -d "labels=CLASS&key_name=code&key_value=h"
        
            POST FIELDS (all optional):
                labels      To name of a single Neo4j label (TODO: for now, just 1 label)
                key_name    A string with the name of a node attribute; if provided, key_value must be present, too
                key_value   The required value for the above key; if provided, key_name must be present, too
                                        Note: no requirement for the key to be primary
                limit       The max number of entries to return
            """
            # Extract the POST values
            post_data = request.form     # Example: ImmutableMultiDict([('label', 'BA'), ('key_name', 'uri'), ('key_value', '123')])
            cls.show_post_data(post_data, "get_filtered")
        
            try:
                result = DataManager.get_nodes_by_filter(dict(post_data))
                response = {"status": "ok", "payload": result}              # Successful termination
            except Exception as ex:
                response = {"status": "error", "error_message": str(ex)}    # Error termination
        
            print(f"get_filtered() is returning: `{response}`")
        
            return jsonify(response)        # This function also takes care of the Content-Type header




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

            print("request.files: ", request.files)
            # EXAMPLE: ImmutableMultiDict([('file', <FileStorage: 'julian_test.json' ('application/json')>)])

            try:
                post_pars = cls.extract_post_pars(post_data, required_par_list=["use_schema"])
                result = DataManager.upload_import_json_file(post_pars)
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
        
            return_url = request.form["return_url"] # This originates from the HTML form :
            #    <input type="hidden" name="return_url" value="my_return_url">
            #print("return_url: ", return_url)
        
            status = DataManager.upload_import_json(verbose=False, return_url=return_url)
            return status
        
        
        
        @bp.route('/upload_media', methods=['POST'])
        @login_required
        def upload_media():
            """
            Upload new media Content, to the (currently hardwired) media folder, and attach it to the Category
            specified in the POST variable "category_id"

            USAGE EXAMPLE:
                <form enctype="multipart/form-data" method="POST" action="/BA/api/upload_media">
                    <input type="file" name="file"><br>   <!-- IMPORTANT: the API handler expects the name value to be "file" -->
                    <input type="submit" value="Upload file">
                    <input type='hidden' name='category_id' value='123'>
                    <input type='hidden' name='pos' value='10'> <!-- TODO: NOT YET IN USE! Media is always added at END OF PAGE -->
                </form>
        
            (Note: the "Dropzone" front-end module invokes this handler in a similar way)
        
            If the upload is successful, a normal status (200) is returned (no response data);
                in case of error, a server error status is return (500), with a text error message
            """
            # TODO: move a lot of this function to MediaManager
            # TODO: media is currently added in a fixed position at the END of the Category page

            # Extract the POST values
            post_data = request.form     # Example: ImmutableMultiDict([('category_id', '3677'), ('pos', 'TBA_insert_after_JUST_ADDING_AT_END_FOR_NOW')])
        
            print("Uploading media content thru upload_media()")
            #print("Raw POST data: ", post_data)
            print("POST variables: ", dict(post_data))  # Example: {'category_id': '3677', 'pos': 'TBA_insert_after_JUST_ADDING_AT_END_FOR_NOW'}
        
            try:
                upload_dir = current_app.config['UPLOAD_FOLDER']    # The name of the temporary directory used for the uploads.
                                                                    #   EXAMPLES: "/tmp/" (Linux)  or  "D:/tmp/" (Windows)
                (tmp_filename_for_upload, full_filename, original_name, mime_type) = \
                            UploadHelper.store_uploaded_file(request, upload_dir=upload_dir, key_name="file", verbose=True)
                print(f"Upload successful so far for file: `{tmp_filename_for_upload}` .  Full name: `{full_filename}`")
            except Exception as ex:
                err_status = f"<b>ERROR in upload</b>: {ex}"
                print("upload_media(): ", err_status)
                response = make_response(err_status, 500)
                return response


            # Map the MIME type of the uploaded file into a schema_code
            # TODO: maybe store the MIME type in the database?
            if mime_type.split('/')[0] == "image":  # For example, 'image/jpeg', 'image/png', etc.
                class_name = "Images"
            else:
                class_name = "Documents"            # Any unrecognized MIME type is treated as a Document


            # Move the uploaded file from its temp location to the media folder
            # TODO: let upload_helper (optionally) handle it
        
            src_fullname = cls.UPLOAD_FOLDER + tmp_filename_for_upload

            dest_folder = MediaManager.lookup_file_path(class_name=class_name)
            dest_fullname = dest_folder + tmp_filename_for_upload
            print(f"Attempting to move `{src_fullname}` to `{dest_fullname}`")
            try:
                shutil.move(src_fullname, dest_fullname)
            except Exception as ex:
                # TODO: create the folder if not present
                err_status = f"Error in moving the file to the intended final destination ({dest_folder}) after upload. {ex}"
                return make_response(err_status, 500)
        
        
            category_uri = post_data["category_id"]


            (basename, suffix) = os.path.splitext(tmp_filename_for_upload)  # EXAMPLE: "test.jpg" becomes
                                                                            #          ("test", ".jpg")
            if suffix:
                suffix = suffix[1:]         # Drop the first character (the ".")  EXAMPLE: "jpg"

            properties = {"basename": basename, "suffix": suffix}

            # TODO: turn into a call to a plugin-provided method, prior to database add
            if class_name == "Images":
                # This is specifically for Images
                try:
                    extra_properties = ImageProcessing.process_uploaded_image(media_folder=dest_folder,
                                                                              basename=basename, suffix=suffix)
                    #   extra_properties may contain the following keys: "caption", "width", "height"

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


            # Update the database (for now, the media is added AT THE END of the Category page)
            # TODO: switch over to using DataManager.new_content_item_in_category_final_step()
            try:
                new_uri = Categories.add_content_at_end(category_uri=category_uri,
                                                        item_class_name=class_name, item_properties=properties)

                # Let the appropriate plugin handle anything they need to wrap up the operation
                if class_name == "Documents":
                    Documents.new_content_item_successful(uri=new_uri, pars=properties, mime_type=mime_type)

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
                        UploadHelper.store_uploaded_file(request, upload_dir=upload_dir, key_name="file", verbose=True)
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
                        UploadHelper.store_uploaded_file(request, upload_dir=upload_dir, key_name="imported_datafile", verbose=False)
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
                        UploadHelper.store_uploaded_file(request, upload_dir=upload_dir, key_name="imported_datafile", verbose=False)
            except Exception as ex:
                return f"<b>ERROR in upload</b>: {ex}"

            print("In import_datafile(): ", (tmp_filename_for_upload, full_filename, original_name))

            return_url = request.form["return_url"] # This originates from the HTML form - namely the line:
            #    <input type="hidden" name="return_url" value="my_return_url">
            #print("return_url: ", return_url)

            status_msg = "<a href='{return_url}' style='margin-left:10px; font-weight:bold'>GO BACK</a><br><br>"
            status_msg += DocumentationGenerator.import_python_file(tmp_filename_for_upload, full_filename)

            # Provide a return link
            status_msg += f" <a href='{return_url}' style='margin-left:10px; font-weight:bold'>GO BACK</a><br><br>"

            return status_msg



        @bp.route('/download_dbase_json/<download_type>')
        @login_required
        def download_dbase_json(download_type="full"):
            """
            Download the full Neo4j database as a JSON file
        
            EXAMPLES invocation:
                http://localhost:5000/BA/api/download_dbase_json/full
                http://localhost:5000/BA/api/download_dbase_json/schema

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
                    result = NeoSchema.export_schema()
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
        
            data = result["data"]
            response = make_response(data)
            response.headers['Content-Type'] = 'application/save'
            response.headers['Content-Disposition'] = f'attachment; filename=\"{export_filename}\"'
            return response


        ##################  END OF ROUTING DEFINITIONS  ##################
        