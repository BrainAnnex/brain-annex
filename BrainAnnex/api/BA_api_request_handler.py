from BrainAnnex.modules.neo_access import neo_access
from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema
from BrainAnnex.modules.categories.categories import Categories
import re               # For REGEX
import pandas as pd
import os
from flask import request, current_app
from typing import Union
from PIL import Image
import unicodedata
import sys                  # Used to give better feedback on Exceptions
import html

"""
    MIT License.  Copyright (c) 2021-2022 Julian A. West
"""



class APIRequestHandler:
    """
    For general database-interaction operations.
    Used by the UI for Page Generation,
    as well as by the API to produce data for the endpoints.

    "Request Handlers" are the ONLY CLASSES THAT DIRECTLY COMMUNICATES WITH THE DATABASE INTERFACE
    """

    db = None           # MUST be set before using this class!
                        # Database-interface object is a CLASS variable, accessible as cls.db

    MEDIA_FOLDER = None # Location where the media for Content Items is stored
                        # Example: "D:/Docs/- MY CODE/Brain Annex/BA-Win7/BrainAnnex/pages/static/media/"



    @classmethod
    def exception_helper(cls, ex, safe_html=False) -> str:
        """
        To give better info on an Exception, in the form:
            EXCEPTION_TYPE : THE_INFO_MESSAGE_IN_ex

        The info returned by "ex" is skimpy;
        for example, in case of a key error, all that it returns is the key name!

        :param ex:          The Exemption object
        :param safe_html:   Flag indicating whether to make safe for display in a browser (for example,
                            the exception type may contain triangular brackets)

        :return:    A string with a more detailed explanation of the given Exception
                    (prefixed by the Exception type, in an HTML-safe form in case it gets sent to a web page)
                    EXAMPLE (as seen when displayed in a browser):
                        <class 'neo4j.exceptions.ClientError'> : THE_INFO_MESSAGE_IN_ex
        """
        (exc_type, _, _) = sys.exc_info()

        if safe_html:
            exc_type = html.escape(str(exc_type))

        return f"{exc_type} : {ex}"



    @classmethod
    def add_new_label(cls, label: str) -> bool:
        """
        Add a new blank node with the specified label

        :return:    True if successful, or False otherwise
        """

        cls.db.create_node(label, {})

        return True     # TODO: check the actual success of the operation




    #######################     SCHEMA-RELATED  ("Records" related)     #######################

    @classmethod
    def new_record_class(cls, class_specs: dict) -> None:
        """
        Create a new Class that is an instance of the Records Class

        :param class_specs: EXAMPLE : {"data": "Favorite Quotes,quote,attribution,notes"}
                                The first item in the comma-separated list is the Class name;
                                the remaining items are the desired Properties, in the wanted order.
                                Blanks before/after any name are ignored.
                                Empty Properties are ignored.
                                If the Class name is missing, an Exception is raised.
        :return:
        """

        if "data" not in class_specs:
            raise Exception("new_record_class(): Missing 'data' key in argument")

        specs = class_specs["data"]       # EXAMPLE:  "Quotes,quote,attribution,notes"

        if specs.strip() == "":
            raise Exception("new_record_class(): Empty 'data' value in argument")

        listing = specs.split(",")
        print("listing: ", listing)

        class_name = listing[0]
        property_list = listing[1:]     # Ditch the initial (0-th) element

        class_name = class_name.strip()
        print("class_name: ", class_name)

        property_list_clean = []
        for p in property_list:
            prop_name = p.strip()
            if prop_name:
                property_list_clean.append(prop_name)

        print("property_list_clean: ", property_list_clean)

        parent_id = NeoSchema.get_class_id(class_name = "Records")
        print("parent_id (ID of `Records` class): ", parent_id)

        new_id = NeoSchema.new_class_with_properties(class_name, property_list_clean)

        status = NeoSchema.create_class_relationship(child=new_id, parent=parent_id, rel_name ="INSTANCE_OF")
        assert status, f"Unable to link the newly-created Class ({class_name}) to the `Records` class"



    @classmethod
    def get_leaf_records(cls):
        """
        Get all Classes that are, directly or indirectly, INSTANCE_OF the Class "Records",
        as long as they are leaf nodes (with no other Class that is an INSTANCE_OF them.)

        EXAMPLE: if the "Foreign Vocabulary" Class is an INSTANCE_OF the Class "Records",
                 and if "French Vocabulary" and "German Vocabulary" are instances of "Foreign Vocabulary",
                 then "French Vocabulary" and "German Vocabulary" (but NOT "Foreign Vocabulary")
                 would be returned

        :return:
        """

        return NeoSchema.get_class_instances("Records", leaf_only=True)




    #######################     CONTENT-ITEM RELATED      #######################

    @classmethod
    def get_content(cls, schema_code, item_id: int) -> (bool, str):
        """
        Fetch and return the contents of a media item stored on a local file

        :param schema_code:     TODO: phase out
        :param item_id:

        :return:    The pair (status, data/error_message)   # TODO: generate an Exception in case of failure

        """
        content_node = cls.db.get_nodes("BA", properties_condition = {"schema_code": schema_code, "item_id": item_id})
        #print("properties_condition", {"schema_code": schema_code, "item_id": item_id})
        #print("content_node:", content_node)
        if (content_node is None) or (content_node == []):
            return (False, "Metadata not found")     # Metadata not found

        basename = content_node[0]['basename']
        suffix = content_node[0]['suffix']
        filename = f"{basename}.{suffix}"

        try:
            file_contents = cls.get_from_file(filename)
            return (True, file_contents)
        except Exception as ex:
            return (False, f"I/O failed. {ex}")     # File I/O failed


    @classmethod
    def get_binary_content(cls, item_id: int, th: str) -> (str, bytes):
        """
        Fetch and return the contents of a media item stored on a local file
        In case of error, raise an Exception

        :param th:
        :param item_id:
        :return:    The binary data

        """
        content_node = cls.db.get_nodes("BA", properties_condition = {"item_id": item_id})
        #print("content_node:", content_node)
        if (content_node is None) or (content_node == []):
            raise Exception("Metadata not found")

        basename = content_node[0]['basename']
        suffix = content_node[0]['suffix']
        filename = f"{basename}.{suffix}"

        try:
            if th:
                file_contents = cls.get_from_binary_file(cls.MEDIA_FOLDER + "resized/", filename)
            else:
                file_contents = cls.get_from_binary_file(cls.MEDIA_FOLDER, filename)

            return (suffix, file_contents)
        except Exception as ex:
            raise Exception(f"Reading of data file for Content Item {item_id} failed: {ex}")     # File I/O failed



    @classmethod
    def get_records_by_link(cls, request_data: dict) -> [dict]:
        """
        Locate and return the data of the nodes linked to the one specified by item_id,
        by the relationship named by rel_name, in the direction specified by dir

        :param request_data: A dictionary with 3 keys, "item_id", "rel_name", "dir"
        :return:             A list of dictionaries with all the properties of the neighbor nodes
        """
        item_id = request_data["item_id"]        # This must be an integer
        rel_name = request_data["rel_name"]
        dir = request_data["dir"]                # Must be either "IN or "OUT"

        assert dir in ["IN", "OUT"], f"get_records_by_link(): The value of the parameter `dir` must be either 'IN' or 'OUT'. The value passed was '{dir}'"
        assert type(item_id) == int, "get_records_by_link(): The value of the parameter `item_id` must be an integer"

        match = cls.db.find(labels="BA", key_name="item_id", key_value=item_id)

        return cls.db.follow_links(match, rel_name=rel_name, rel_dir=dir, neighbor_labels = "BA")



    @classmethod
    def get_link_summary(cls, item_id: int, omit_names = None) -> dict:
        """
        Return a dictionary structure identifying the names and counts of all
        inbound and outbound links to/from the given data node.
        TODO: move most of it to the "~ FOLLOW LINKS ~" section of NeoAccess

        :param item_id:     ID of a data node
        :param omit_names:  Optional list of relationship names to disregard
        :return:            A dictionary with the names and counts of inbound and outbound links.
                            Each inner list is a pair [name, count]
                            EXAMPLE:
                                {
                                    "in": [
                                        ["BA_served_at", 1]
                                    ],
                                    "out": [
                                        ["BA_located_in", 1],
                                        ["BA_cuisine_type", 2]
                                    ]
                                }
        """
        if omit_names:
            assert type(omit_names) == list, "If the `omit_names` argument is specified, it MUST be a LIST"
            where_clause = f"WHERE NOT type(r) IN {omit_names}"
        else:
            where_clause = ""

        # Get outbound links (names and counts)
        q_out = f'''
                MATCH (n :BA {{item_id:$item_id}})-[r]->(n2 :BA)
                {where_clause}
                RETURN type(r) AS rel_name, count(n2) AS rel_count
                '''

        result = cls.db.query(q_out,data_binding={"item_id": item_id})
        rel_out = [ [ l["rel_name"],l["rel_count"] ] for l in result ]


        # Get inbound links (names and counts)
        q_in = f'''
                MATCH (n :BA {{item_id:$item_id}})<-[r]-(n2 :BA)
                {where_clause}
                RETURN type(r) AS rel_name, count(n2) AS rel_count
                '''

        result = cls.db.query(q_in,data_binding={"item_id": item_id})
        rel_in = [ [ l["rel_name"],l["rel_count"] ] for l in result ]

        return  {"in": rel_in, "out": rel_out}




    ##############   MODIFYING CONTENT ITEMS   ##############

    @classmethod
    def update_content_item(cls, post_data: dict) -> str:
        """
        Update an existing Content Item

        :return:    An empty string if successful, or an error message otherwise
        """
        print("In update_content_item(). POST data: ", post_data)

        # Validate the data
        schema_code = post_data.get("schema_code")   # If key not present, the value will be None
        print("Item Type: ", schema_code)

        try:
            item_id = int(post_data.get("item_id"))
        except Exception as ex:
            return f"item_id is missing or not an integer. {ex}"

        print("Item Type: ", item_id)

        print("All Item Data: ")
        print("-----------")
        for k, v in post_data.items():
            print(k , " -> " , v)

        data_binding = post_data

        if item_id < 0:     # Validate item_id
            return f"Bad item_id: {item_id}"


        set_dict = {}
        for k, v in data_binding.items():
            if k not in ("schema_code", "item_id"):    # Exclude some keys
                set_dict[k] = v

        # PLUGIN-SPECIFIC OPERATIONS that change set_dict and perform filesystem operations
        #       TODO: try to infer them from the Schema
        if schema_code == "n":
            set_dict = cls.plugin_n_update_content(data_binding, set_dict)

        # TODO: check the actual success of the operation
        match = cls.db.find(labels="BA", properties={"item_id": item_id, "schema_code": schema_code})
        cls.db.set_fields(match=match, set_dict=set_dict)
        #cls.db.set_fields("BA", set_dict, properties_condition={"item_id": item_id, "schema_code": schema_code})

        return ""     # Success (no error message)



    @classmethod
    def delete_content_item(cls, item_id: str, schema_code: str) -> str:
        """
        Delete the specified individual Content Item.
        Note that schema_code is redundant.

        :param item_id:     String version of the unique ID
        :param schema_code: Redundant
        :return:            An empty string if successful, or an error message otherwise
        """
        print(f"In delete_content_item(). Attempting to delete item id {item_id} of type `{schema_code}`")

        try:
            item_id = int(item_id)
        except Exception as ex:
            return f"item_id is missing or not an integer. {ex}"


        # PLUGIN-SPECIFIC OPERATIONS that perform filesystem operations
        #       (TODO: try to infer them from the Schema)
        if schema_code in ["n", "i", "d"]:
            status = cls.delete_attached_media_file(item_id)   # If there's media involved, delete the media, too

        if schema_code == "i":
            status = cls.plugin_i_delete_content(item_id)   # Extra processing for the "Images" plugin

        match = cls.db.find(labels="BA", properties={"item_id": item_id, "schema_code": schema_code})
        number_deleted = cls.db.delete_nodes(match)

        if number_deleted == 1:
            return ""   # Successful termination, with 1 Content Item deleted, as expected
        elif number_deleted == 0:
            return f"Unable to delete Content Item id {item_id} of type `{schema_code}`"  # Error message (nothing deleted)
        else:
            return f"{number_deleted} Content Items deleted, instead of the expected 1" # Error message (too much deleted)
                                                                                        # Should not happen, since item_id is a primary key


    @classmethod
    def new_content_item_in_category(cls, post_data: dict) -> int:
        """
        Create a new Content Item attached to a particular Category

        :param post_data:
            - "category_id"  (for the linking to a Category)
            - Schema-related keys:
                    * schema_code (Required)
                    * schema_id (Optional)
                    * class_name (Required only for Class Items of type "record")

            - insert_after        Either an item_id, or one of the special values "TOP" or "BOTTOM"
            - PLUS all applicable plugin-specific fields (all the key/values for the new Content Item)

        :return:    The item_id of the newly-created node
                    In case of error, an Exception is raised
        """

        # NOTE: the post_data dictionary contains entries are not part of the data dictionary for the new Content Item;
        #       those will be eliminated below

        # Validate the data, and extract some special attributes, while also paring down the post_data dictionary

        # Category-related data
        category_id = post_data.get("category_id")  # If the key isn't present, the value will be None
        if not category_id:
            raise Exception("Missing Category ID")
        category_id = int(category_id)      # Correct the value, to make it an integer
        del post_data["category_id"]        # Remove this entry from the dictionary

        # Positioning within the Category
        insert_after = post_data.get("insert_after")
        if not insert_after:
            raise Exception("Missing insert_after (ID of Item to insert the new one after)")
        del post_data["insert_after"]

        # Schema-related data
        schema_code = post_data.get("schema_code")
        if not schema_code:
            raise Exception("Missing Schema Code (Item Type)")
        del post_data["schema_code"]

        schema_id = post_data.get("schema_id")
        if schema_id:
            schema_id = int(schema_id)
            del post_data["schema_id"]
        else:
            schema_id = NeoSchema.get_schema_id(schema_code)    # If not passed, try to look it up
            print("schema_id looked up as: ", schema_id)
            if schema_id == -1:
                raise Exception("Missing Schema ID")

        class_name = post_data.get("class_name")
        if class_name:
            del post_data["class_name"]
        else:
            # If not provided, look it up from the schema_id
            class_name = NeoSchema.get_class_name(schema_id)
            print(f"class_name looked up as: `{class_name}`")


        # Generate a new ID (which is needed by some plugin-specific modules)
        new_item_id = NeoSchema.next_available_datapoint_id()
        print("New item will be assigned ID:", new_item_id)

        # PLUGIN-SPECIFIC OPERATIONS that change data_binding and perform filesystem operations
        #       TODO: try to infer them from the Schema
        #             E.g., the Schema indicates that 2 Properties, "basename" and "suffix" are required;
        #               a call is made to a plugin-specific module, to produce those (and, in the process,
        #               some files are saved,
        #               some attributes are added to post_data, and some are whisked away)
        #             Note: the plugin might want to do some ops regardless of missing required Properties
        if schema_code == "n":
            post_data = cls.plugin_n_add_content(new_item_id, post_data)


        print("Revised post_data: ", post_data)
        # EXAMPLE:  {'text': 'My New Header'}
        # Note that several entries got removed from the dictionary;
        #       only attributes of the new node are still present.
        #       Some attributes may have been added by a plugin-specific module


        # Create the new node and required relationships
        if insert_after == "TOP":
            Categories.add_content_at_beginning(category_id=category_id,
                                                item_class_name=class_name, item_properties=post_data,
                                                new_item_id=new_item_id)
        elif insert_after == "BOTTOM":
            Categories.add_content_at_end(category_id=category_id,
                                                item_class_name=class_name, item_properties=post_data,
                                                new_item_id=new_item_id)
        else:
            try:
                insert_after = int(insert_after)
            except Exception:
                raise Exception(f"`insert_after` must be an integer, unless it's 'TOP' or 'BOTTOM'. Value passed: `{insert_after}`")

            Categories.add_content_after_element(category_id=category_id,
                                             item_class_name=class_name, item_properties=post_data,
                                             insert_after=insert_after, new_item_id=new_item_id)

        return new_item_id     # Success




    #######################     MEDIA-RELATED      #######################

    @classmethod
    def get_from_file(cls, filename: str) -> str:
        """

        :param filename:    EXCLUSIVE of MEDIA_FOLDER part (stored as class variable)
        :return:            The contents of the file
        """
        full_file_name = cls.MEDIA_FOLDER + filename
        with open(full_file_name, 'r', encoding='utf8') as fh:
            file_contents = fh.read()
            return file_contents


    @classmethod
    def get_from_binary_file(cls, path: str, filename: str) -> bytes:
        """

        :param path:
        :param filename:    EXCLUSIVE of path
        :return:            The contents of the binary file
        """
        #full_file_name = cls.MEDIA_FOLDER + filename
        full_file_name = path + filename
        with open(full_file_name, 'rb') as fh:
            file_contents = fh.read()
            return file_contents



    @classmethod
    def save_into_file(cls, contents: str, filename: str) -> None:
        """
        Save the given data into the specified file in the class-wide media folder.  UTF8 encoding is used.
        In case of error, detailed Exceptions are raised

        :param contents:    String to store into the file
        :param filename:    EXCLUSIVE of MEDIA_FOLDER part (stored as class variable)
        :return:            None.  In case of errors, detailed Exceptions are raised
        """

        full_file_name = cls.MEDIA_FOLDER + filename

        try:
            f = open(full_file_name, "w", encoding='utf8')
        except Exception as ex:
            raise Exception(f"Unable to open file {full_file_name} for writing. {ex}")

        try:
            f.write(contents)
        except Exception as ex:
            raise Exception(f"Unable write data to file {full_file_name}. First 20 characters: `{contents[:20]}`. {cls.exception_helper(ex)}")

        f.close()



    @classmethod
    def delete_attached_media_file(cls, item_id: int) -> bool:
        """
        Delete the media file attached to the specified Content Item:
        """
        record = cls.db.get_single_record_by_key("BA", "item_id", item_id)
        if record is None:
            return False

        if ("basename" not in record) or ("suffix" not in record):
            return False

        cls.delete_media_file(record["basename"], record["suffix"])
        return True



    @classmethod
    def delete_media_file(cls, basename: str, suffix: str, subfolder = "") -> bool:
        """
        Delete the specified media file, assumed in a standard location

        :param basename:
        :param suffix:
        :param subfolder:   It must end with "/"  .  EXAMPLE:  "resized/"
        :return:
        """
        filename = basename + "." + suffix
        print(f"Attempting to delete file `{filename}`")

        full_file_name = cls.MEDIA_FOLDER + subfolder + filename

        return cls.delete_file(full_file_name)



    @classmethod
    def delete_file(cls, fullname: str) -> bool:
        """
        Delete the specified file, assumed in a standard location

        :param fullname:
        :return:            True if successful, or False otherwise
        """

        if os.path.exists(fullname):
            os.remove(fullname)
            return True
        else:
            return False    # "The file does not exist"




    #######################     PLUGIN-SPECIFIC      #######################

    # TODO: move to a separate module

    #####  For "n" plugin

    @classmethod
    def plugin_n_add_content(cls, item_id: int, data_binding: dict) -> dict:
        """
        Special handling for Notes (ought to be specified in its Schema):
               the "body" value is to be stored in a file named "notes-ID.htm", where ID is the item_id,
               and NOT be stored in the database.  Instead, store in the database:
                       basename: "notes-ID"
                       suffix: "htm"

        :return: The altered data_binding dictionary.  In case of error, an Exception is raised.
        """
        # Save and ditch the "body" attribute - which is not to be stored in the database
        body = data_binding["body"]
        del data_binding["body"]

        # Create a file
        basename = f"notes-{item_id}"
        suffix = "htm"
        filename = basename + "." + suffix
        print(f"Creating file named `{filename}`, with contents:")
        print(body)
        cls.save_into_file(body, filename)

        # Introduce new attributes, "basename" and "suffix", to be stored in the database
        data_binding["basename"] = basename
        data_binding["suffix"] = suffix

        return data_binding



    @classmethod
    def plugin_n_update_content(cls, data_binding: dict, set_dict: dict) -> dict:
        """
        Special handling for Notes (ought to be specified in its Schema):
               the "body" value is to be stored in a file named "notes-ID.htm", where ID is the item_id,
               and NOT be stored in the database.  Instead, store in the database:
                       basename: "notes-ID"
                       suffix: "htm"

        :return: The altered data_binding dictionary
        """
        body = data_binding["body"]
        item_id = data_binding["item_id"]


        # Overwrite the a file
        basename = f"notes-{item_id}"
        filename = basename + ".htm"
        print(f"Overwriting file named `{filename}`, with contents:")
        print(body)
        cls.save_into_file(body, filename)

        # Ditch the "body" attribute - which is not to be stored in the database
        #del data_binding["body"]
        del set_dict["body"]
        # In its place, introduce 2 new attributes, "basename" and "suffix"
        #data_binding["basename"] = basename
        #data_binding["suffix"] = "htm"

        return set_dict



    #####  For "i" plugin

    @classmethod
    def plugin_i_delete_content(cls, item_id):
        """
        Delete the thumbnail file attached to the specified Content Item
        """
        record = cls.db.get_single_record_by_key("BA", "item_id", item_id)
        if record is None:
            return False

        if ("basename" not in record) or ("suffix" not in record):
            return False

        cls.delete_media_file(record["basename"], record["suffix"], subfolder="resized/")
        return True




    #############################################################
    #                            FILTERS                        #
    #############################################################



    @classmethod
    def get_nodes_by_filter(cls, filter_dict) -> [dict]:
        """

        :param filter_dict: A dictionary.
                            EXAMPLE: {"labels": "BA", "key_name": "item_id", "key_value": 123, "limit": 25}

        :return:            A (possibly-empty) list of dictionaries
        """
        print(f"In get_nodes_by_filter().  filter_dict: {filter_dict}")

        labels = filter_dict.get("labels")      # It will be None if key isn't present

        key_name = filter_dict.get("key_name")
        key_value = filter_dict.get("key_value")

        # Convert key_value to integer, if at all possible; otherwise, leave as string
        key_value = cls.to_int_if_possible(key_value)

        limit = filter_dict.get("limit", 10)    # Default value, if not provided

        try:
            limit = int(limit)
        except Exception:
            raise Exception(f"The parameter 'limit', if provided, must be an integer; value received: `{limit}`")

        print(f"labels: {labels} | key_name: {key_name} | key_value: {key_value} | limit: {limit}")

        match = cls.db.find(labels=labels, key_name=key_name, key_value=key_value)

        if limit > 500:
            limit = 500     # Set an upper bound

        result = cls.db.fetch_nodes(match, limit=limit)

        return result


    @classmethod
    def to_int_if_possible(cls, s: str) -> Union[int, str, None]:
        """
        Convert the argument to an integer, if at all possible; otherwise, leave it as a string
        (or leave it as None, if applicable)
        :param s:
        :return:    Either an int or a string
        """
        try:
            return int(s)
        except Exception:
            return s




    ###############################################################
    #                       MEDIA UPLOAD                          #
    ###############################################################

    @classmethod
    def upload_helper(cls, request_obj, html_name: str, verbose=False) -> (str, str):
        """
        It accepts a flask.request object, and it creates a file from the upload,
        into the folder specified by current_app.config['UPLOAD_FOLDER'],
        defined elsewhere (for example in the main file.)  EXAMPLE: "D:/tmp/"

        It decides, from the name of the file being uploaded, a meaningful name for the temporary file
        to create as part of the upload.

        It returns both the basename and the full filename of the temporary file thus created.

        In case of error, an Exception is raised

        TODO: maybe allow to optionally provide the final location/name for the uploaded file

        :param request_obj: A flask.request object
        :param html_name:   The name that was used in the HTML form INPUT tag: <input type="file" name="some_name_to_refer_to_the_upload">
                                TODO: maybe extract it from request.files
        :param verbose:     Flag for debugging

        :return:            The pair (filename, full_filename_including_path) where filename is the basename
                            EXAMPLE: ("my_file_being_uploaded.txt", "D:/tmp/my_file_being_uploaded.txt")

        """
        if verbose:
            request_dict = request_obj.__dict__     # A dictionary of all names and attributes of object.
            keys_list = list(request_dict)
            # EXAMPLE: ['method', 'scheme', 'server', 'root_path', 'path', 'query_string', 'headers', 'remote_addr', 'environ', 'shallow', 'cookies', 'url_rule', 'view_args']

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
            # EXAMPLE: ImmutableMultiDict([('categoryID', '123')])
            #               if the HTML form included <input type="hidden" name="categoryID" value="123">

            print("request.values: ", request_obj.values)
            print("request.json: ", request_obj.json)
            print("request.data: ", request_obj.data)


        # Check if the POST request has the file part, indexed by the string specified by html_name
        # Example from an invoking form:   <input type="file" name="some_name_to_refer_to_the_upload">
        if html_name not in request_obj.files:
            raise Exception(f"No file found in upload!  "
                            f"Check the `name` attribute in the HTML `input` tag (it should be '{html_name}').  No action taken...")

        f = request_obj.files[html_name]    # f is a Werkzeug FileStorage object
        #print("f: ", f)     # EXAMPLE: <FileStorage: 'abc.txt' ('text/plain')>
        #print("f.stream: ", f.stream)      # EXAMPLE: <tempfile.SpooledTemporaryFile object at 0x000001604F5E6700>
        #print("f.filename: ", f.filename)  # EXAMPLE: abc.txt
        #print("f.mimetype: ", f.mimetype)  # EXAMPLE: text/plain

        # If the user does not select a file, the browser submits an
        #       empty file without a filename
        if f.filename == '':
            raise Exception("No selected file!  Did you select a file to upload?")


        # Construct, from the name of the file being uploaded, a "safe" name for the temporary file to create as part of the upload
        tmp_filename_for_upload = cls.secure_filename_BA(f.filename)
        print(f"Name given to temporary file to upload to: `{tmp_filename_for_upload}`")
        # TODO: the "safe" name annoyingly has all the blank spaces replaced with underscores!  Maybe just eliminate slashes!
        # TODO: f.filename should be returned as well (e.g. for use in captions, or to save the original name)

        upload_dir = current_app.config['UPLOAD_FOLDER']        # Defined in main file.  EXAMPLE: "D:/tmp/"
        print(f"Attempting to upload to directory `{upload_dir}`")

        full_filename = f"{upload_dir}{tmp_filename_for_upload}"    # EXAMPLE: "D:/tmp/my_file_being_uploaded.txt"
        f.save(full_filename)                                       # Create the temporary file, which concludes the upload

        return (tmp_filename_for_upload, full_filename)             # Normal termination



    @classmethod
    def secure_filename_BA(cls, filename: str) -> str:
        """
        (ADAPTED FOR BRAIN ANNEX FROM werkzeug.utils.secure_filename(), version 0.5;
        blank spaces are no longer transformed to underscores.
        See: https://flask.palletsprojects.com/en/2.0.x/patterns/fileuploads/)

        Return a secure version of a filename.
        This filename can then safely be stored on a regular file system and passed
        to :func:`os.path.join`.  The filename returned is an ASCII only string
        for maximum portability.

        On windows systems the function also makes sure that the file is not
        named after one of the special device files.

        EXAMPLES:   secure_filename_BA("My cool ++ movie.mov")          -> 'My cool  movie.mov'
                    secure_filename_BA("../../../etc/passwd")           ->'etc_passwd'
                    secure_filename_BA('i contain \xfcml\xe4uts.txt')   -> 'i contain umlauts.txt'
                    secure_filename_BA("    blank-padded string  ")     -> 'blank-padded string'
                    secure_filename_BA("COM1.txt")       [On Windows]   -> '_COM1.txt'

        The function might return an empty filename.  It's your responsibility
        to ensure that the filename is unique and that you abort or
        generate a random filename if the function returned an empty one.

        :param filename:    A string with the filename to secure
        """
        _filename_ascii_strip_re = re.compile(r"[^A-Za-z0-9_. -]")  # List of allowed characters in the name;
                                                                    # note that blank is included
        _windows_device_files = (
            "CON",
            "AUX",
            "COM1", "COM2", "COM3", "COM4",
            "LPT1", "LPT2", "LPT3",
            "PRN",
            "NUL"
        )

        # Convert non-ASCII characters to closest ASCII equivalent.  EXAMPLE: "Rüdiger" -> "Rudiger"
        filename = unicodedata.normalize("NFKD", filename)  # Normal form "KD" (Compatibility Decomposition)
        filename = filename.encode("ascii", "ignore").decode("ascii")

        # Replace OS file path separators (such as forward and back slashes) with underscores.  EXAMPLE: "bin/src" -> "bin_src"
        for sep in os.path.sep, os.path.altsep:
            if sep:
                filename = filename.replace(sep, "_")

        #filename = "_".join(filename.split()   # Replace all blanks spaces with underscores
        filename = _filename_ascii_strip_re.sub("", filename)   # Zap all characters except the allowed ones
        filename = filename.strip("._ ")         # Zap periods and underscores at the start or end of the string

        # On nt (such as Windows 7, etc) a couple of special files are present in each folder.  We
        # have to ensure that the target file is not such a filename; if it is, we prepend an underline
        if  (
                os.name == "nt"
                and filename
                and filename.split(".")[0].upper() in _windows_device_files
            ):
            filename = f"_{filename}"

        return filename



    @classmethod
    def process_uploaded_image(cls, filename: str, fullname: str):
        """
        Obtain the size of the image, resize it to a thumbnail,
        and return a dictionary of properties that will go in the database

        :param filename:    EXAMPLE: "my image.jpg"
        :param fullname:    EXAMPLE (on Windows):  "D:/Docs/Brain Annex/media/my image.jpg"

        :return:            A dictionary of properties that will go in the database
        """
        (width, height) = ImageProcessing.get_image_size(fullname)  # Extract the dimensions of the uploaded image

        # Create and save a thumbnail version
        ImageProcessing.save_thumbnail(src_folder = cls.MEDIA_FOLDER,
                                       filename = filename,
                                       save_to_folder = cls.MEDIA_FOLDER+"resized/",
                                       src_width=width, src_height=height)


        (basename, suffix) = os.path.splitext(filename)     # EXAMPLE: "test.jpg" becomes ("test", ".jpg")
        suffix = suffix[1:]     # Drop the first character (the ".")  EXAMPLE: "jpg"

        # Create a dictionary of properties that will go in the database
        properties = {"caption": basename,
                      "basename": basename, "suffix": suffix,
                      "width": width, "height": height}

        print(f"Uploaded image has width : {width} | height: {height}")

        return properties




    ############################################################
    #                       IMPORT-EXPORT                      #
    ############################################################

    @classmethod
    def upload_import_json(cls, verbose=False, return_url=None) -> str:
        """
        Modify the database, based on the contents of the uploaded file (expected to contain the JSON format
        of a Neo4j export)

        :param verbose:
        :param return_url:
        :return:            Status string (error or success message)
        """
        # If a return URL was provided, compose a link for it
        return_link = "" if return_url is None else f" <a href='{return_url}'>Go back</a>"

        try:
            (basename, full_filename) = cls.upload_helper(request, html_name="imported_json", verbose=False)
            # basename and full name of the temporary file created during the upload
        except Exception as ex:
            return f"ERROR in upload: {ex} {return_link}"

        try:
            with open(full_filename, 'r') as fh:
                file_contents = fh.read()
                if verbose:
                    print(f"Contents of uploaded file:\n{file_contents}")
        except Exception:
            return f"File I/O failed. {return_link}"

        try:
            #neo = neo_access.NeoAccess()
            details = cls.db.import_json_data(file_contents)
        except Exception as ex:
            return f"Import of JSON data failed: {ex}. {return_link}"

        # Now delete the temporary file created during the upload
        delete_status = cls.delete_file(full_filename)

        # Prepare a status message to return
        status = f"File `{basename}` uploaded and imported successfully: {details}."
        if not delete_status:
            status += " However, the temporary import file could not be deleted."

        status += return_link

        return  status



    @classmethod
    def define_pattern(cls) -> str:
        """
        Define a REGEX pattern for parsing of data files, for use in import_datafile()

        :return:    A string with a REGEX pattern
        """
        # The R before the string escapes all characters ("raw strings" aka "verbatim strings")
        #pattern_1 = R"\n([a-zA-Z.'\- ,()]+)@@@\n"   # Full name
        pattern_1 = R"\n(.+)@@@\n"                  # Full name
        pattern_2 = ".+ profile\n"                  # Throwaway line
        pattern_3 = "---1st1st degree connection\n" # Throwaway line
        pattern_4 = "(.+)\n(.+)\n"                  # Role and location (across 2 lines)

        pattern = pattern_1 + pattern_2 + pattern_3 + pattern_4
        return pattern


    @classmethod
    def import_datafile(cls, basename, full_filename, test_only=True):
        """
        TODO: generalize!  For now, used for an ad-hoc import, using REGEX to extract the desired fields

        :param basename:        EXAMPLE: "my_file_being_uploaded.txt"
        :param full_filename:   EXAMPLE: "D:/tmp/my_file_being_uploaded.txt"
        :param test_only:       If True, the file is parsed, but nothing is actually added to the database
        :return:                Status message (whether successful or not)
        """

        try:
            with open(full_filename, 'r') as fh:
                file_contents = fh.read()
                print(f"\n--- First 500 bytes of uploaded file:\n{file_contents[:500]}")
        except Exception:
            return f"File I/O failed (on file {full_filename})"


        pattern = cls.define_pattern()
        all_matches = re.findall(pattern, file_contents)

        id_offset = NeoSchema.next_available_datapoint_id()

        # Zap leading/trailing blanks from all entries, and add 2 extra fields (for item_id and schema_code)
        all_matches = [list(map(lambda s: s.strip(), val)) + [i+id_offset] + ["r"]
                       for i, val in enumerate(all_matches)]

        if all_matches:     # If the list is not empty, i.e. if matches were found
            print(f"{len(all_matches)} MATCHES found")
            for match_instance in all_matches:   # Consider each match in turn
                print("Overall Match: " , match_instance)     # This would normally be a tuple of capture groups
                                                              # (which we previously turned to list, with 2 field added)
        else:
            print("NO MATCHES found")


        df = pd.DataFrame(all_matches, columns = ["name", "role", "location", "item_id", "schema_code"])
        print(df.count())
        print(df.head(10))
        print("...")
        print(df.tail(10))

        if test_only:
            return f"File `{basename}` uploaded successfully.  Nothing added to database, because in test_only mode"

        cls.db.load_pandas(df, label="IP")     # Using a temporary label for ease of the next steps
        """
        # Done manually.  The first item_id in the new data is 69, and we want to map it a pos value of 30;
        # 70 will map to 40, and so on:
        MATCH (c:BA {schema_code:"cat", item_id:61}),          // <------ This is the Category "Professional Networking"
        (n:IP)
        MERGE (n)-[:BA_in_category {pos:(n.item_id - 69)*10+30}]->(c)

        # Rename all "IP" labels to "BA"
        MATCH (n:IP) SET n:BA
        REMOVE n:IP
        """

        return f"File `{basename}` uploaded and imported successfully"




########################    IMAGES  (TODO: move to a separate module)  ############################################################

class ImageProcessing:
    """
    The "th" format from the Classic BA, is:
    "default (largish) thumbs - 3 fit in a row" : width sized to 300

    formats =
    {
        "th": { "description": "default (largish) thumbs - 3 fit in a row",
                "size": 300,
                "affected": "w"
        }
    }
    """

    @classmethod
    def save_thumbnail(cls, src_folder: str, filename: str, save_to_folder: str,
                       src_width: int, src_height: int) -> None:
        """
        Make a thumbnail of the specified image, and save it in a file.
        The "th" thumbnail format is being followed.

        :param src_folder:      Full path of folder with the file to resize.  It MUST end with "/"
                                    EXAMPLE (on Windows): "D:/Docs/Brain Annex/media/"
        :param filename:        Name of file to resize.  EXAMPLE: "my image.jpg"
        :param save_to_folder:  Full path of folder where to save the resized file.  It MUST end with "/"
                                    EXAMPLE (on Windows): "D:/Docs/Brain Annex/media/resized/"
        :param src_width:       Pixel width of the original image
        :param src_height:      Pixel height of the original image
        :return:                None.  In case of error, an Exception is raised
        """
        cls.scale_down_horiz(src_folder, filename, save_to_folder, src_width, src_height, target_width=300)



    @classmethod
    def scale_down_horiz(cls, src_folder: str, filename: str, save_to_folder: str,
                              src_width: int, src_height: int, target_width: int) -> None:
        """
        Resize an image to the target WIDTH, and save it in a file.

        :param src_folder:      Full path of folder with the file to resize.  It MUST end with "/"
                                    EXAMPLE (on Windows): "D:/Docs/Brain Annex/media/"
        :param filename:        Name of file to resize.  EXAMPLE: "my image.jpg"
        :param save_to_folder:  Full path of folder where to save the resized file.  It MUST end with "/"
                                    EXAMPLE (on Windows): "D:/Docs/Brain Annex/media/resized/"
        :param src_width:       Pixel width of the original image
        :param src_height:      Pixel height of the original image
        :param target_width:    Desired pixel width of the resized image
        :return:                None.  In case of error, an Exception is raised
        """
        image = Image.open(src_folder + filename)

        resized_full_name = save_to_folder + filename

        if target_width >= src_width:   # Don't transform the image; just save it as it is
            image.save(resized_full_name)
        else:
            scaling_ratio = src_width / target_width    # This will be > 1 (indicative of reduction)
            print("scaling_ratio: ", scaling_ratio)
            target_height = int(src_height / scaling_ratio)
            new_image = image.resize((target_width, target_height))
            new_image.save(resized_full_name)



    @classmethod
    def get_image_size(cls, source_full_name) -> (int, int):
        """
        Return the size of the given image.

        :param source_full_name:    EXAMPLE (on Windows): "D:/Docs/Brain Annex/media/resized/my image.jpg"
        :return:                    The pair (width, height) with the image dimensions in pixels.  In case of error, an Exception is raised
        """
        image = Image.open(source_full_name)

        return image.size   # EXAMPLE: (1920, 1280)



    @classmethod
    def describe_image(cls, source_full_name) -> None:
        """
        Print out some info about the given image.

        :param source_full_name:    EXAMPLE (on Windows): "D:/Docs/Brain Annex/media/resized/my image.jpg"
        :return:                    None.  In case of error, an Exception is raised
        """
        image = Image.open(source_full_name)

        # The file format
        print(image.format) # EXAMPLE: "JPEG" or "PNG"

        # The pixel format used by the image
        print(image.mode)   # Typical values are "RGB", "RGBA", "1", "L", "CMYK"

        # Image size, in pixels, as a 2-tuple (width, height)
        print(image.size)   # EXAMPLE: (1920, 1280)

        # Color palette table, if any
        print(image.palette) # EXAMPLE: None




#############################################################################################################################

def test():
    """
    Tester function for regex.   TODO: move to test folders

    :return:
    """
    file_contents = "HERE DEFINE STRING TO PARSE"

    pattern_1 = R"\n([a-zA-Z ]+)@@@\n"          # Full name
    pattern_2 = ".+ profile\n"                  # Throwaway line
    pattern_3 = "---1st1st degree connection\n" # Throwaway line
    pattern_4 = "(.+)\n(.+)\n"                  # Role and location (across 2 lines)

    pattern = pattern_1 + pattern_2 + pattern_3 + pattern_4
    #pattern = R"\n([a-zA-Z ]+)@@@\n.+ profile\n---1st1st degree connection\n(.+)\n(.+)"  # R"---1st1st degree connection\n(.+)"
    all_matches = re.findall(pattern, file_contents)
    if all_matches:     # If the list is not empty, i.e. if matches were found
        print(f"{len(all_matches)} MATCHES found")
        for matchInstance in all_matches:   # Consider each match in turn
            print("Overall Match: " , matchInstance)     # This will be a tuple of capture groups
    else:
        print("NO MATCHES found")
