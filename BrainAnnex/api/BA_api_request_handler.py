from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema
from BrainAnnex.modules.categories.categories import Categories
from BrainAnnex.modules.PLUGINS.notes import Notes
from BrainAnnex.modules.upload_helper.upload_helper import UploadHelper
from BrainAnnex.modules.media_manager.media_manager import MediaManager
import re               # For REGEX
import pandas as pd
import os
from flask import request, current_app  # TODO: phase out (?)
from typing import Union
import sys                  # Used to give better feedback on Exceptions
import html
import shutil
from time import sleep
from datetime import datetime


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
    # The "db" and "FOLDER" properties get set by InitializeBrainAnnex

    db = None           # MUST be set before using this class!
                        # Database-interface object is a CLASS variable, accessible as cls.db

    MEDIA_FOLDER = None # Location where the media for Content Items is stored
                        # Example on Windows: "D:/Docs/- MY CODE/Brain Annex/BA-Win7/BrainAnnex/pages/static/media/"
    LOG_FOLDER = None   # Location where the log file is stored

    ongoing_data_intake = False
    import_file_count = 0

    log_filename = "IMPORT_LOG.txt"     # TODO: generalize to BrainAnnex-wide
    log_file_handle = None



    @classmethod
    def export_full_dbase(cls):
        return cls.db.export_dbase_json()



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




    #######################     SCHEMA-RELATED       #######################

    @classmethod
    def new_schema_class(cls, class_specs: dict) -> None:
        """
        Create a new Schema Class, possibly linked to another existing class,
        and also - typically but optionally - with the special "INSTANCE_OF" link
        to an existing class (often, "Records")
        In case of error, an Exception is raised.

        :param class_specs: A dictionary with the following
                DICTIONARY KEYS:
                new_class_name      The name of the new Class (tolerant of leading/trailing blanks)
                properties_list     The name of all desired Properties, in order
                                    (all comma-separated).  Tolerant of leading/trailing blanks, and of missing property names
                instance_of         Typically, "Records"

                [ALL THE REMAINING KEYS ARE OPTIONAL]
                linked_to           The name of an existing Class node, to link to
                rel_name            The name to give to the above relationship
                rel_dir             The relationship direction, from the point of view of the newly-added node

        :return:            None
        """
        new_class_name = class_specs["new_class_name"]
        new_class_name = new_class_name.strip()
        print("new_class_name: ", new_class_name)

        properties_str = class_specs.get("properties_list", "") # Make allowance for an absent properties_list
        property_list = properties_str.split(",")     # Note: if properties_str is an empty string, the result will be ['']
        print("property_list: ", property_list)

        # Zap missing property names, and clean up the names that are present
        property_list_clean = []
        for p in property_list:
            prop_name = p.strip()
            if prop_name:
                property_list_clean.append(prop_name)

        print("property_list_clean: ", property_list_clean)

        instance_of_class = class_specs.get('instance_of')   # Will be None if key is missing
        print(f"For 'INSTANCE_OF' relationship, requesting to link to Class: `{instance_of_class}`")

        # Validate the optional relationship to another class
        if  ( ("linked_to" in class_specs) or ("rel_name" in class_specs) or ("rel_dir" in class_specs) ) \
            and not \
            ( ("linked_to" in class_specs) and ("rel_name" in class_specs) and ("rel_dir" in class_specs) ):
            raise Exception("The parameters `linked_to`, `rel_name` and `rel_dir` must all be present or all be missing")


        # Create the new Class, and all of its Properties (as separate nodes, linked together)
        new_id = NeoSchema.new_class_with_properties(new_class_name, property_list_clean,
                                                     class_to_link_to=instance_of_class, link_to_name="INSTANCE_OF")


        # If requested, link to another existing class
        if ("linked_to" in class_specs) and ("rel_name" in class_specs) and ("rel_dir" in class_specs):
            linked_to = class_specs["linked_to"]
            linked_to_id = NeoSchema.get_class_id(class_name = linked_to)
            print(f"Linking the new class to the existing class `{linked_to}`, which has Schema ID {linked_to_id}")
            rel_name = class_specs["rel_name"]
            rel_dir = class_specs["rel_dir"]    # The link direction is relative to the newly-created class node
            print(f"rel_name: `{rel_name}` | rel_dir: {rel_dir}")

            assert rel_dir == "OUT" or rel_dir == "IN", f"The value for rel_dir must be either 'IN' or 'OUT' (passed value was {rel_dir})"

            try:
                if rel_dir == "OUT":
                    NeoSchema.create_class_relationship(from_id=new_id, to_id=linked_to_id, rel_name=rel_name)
                elif rel_dir == "IN":
                    NeoSchema.create_class_relationship(from_id=linked_to_id, to_id=new_id, rel_name=rel_name)
            except Exception as ex:
                raise Exception(f"The new class `{new_class_name}` was created successfully, but could not be linked to `{linked_to}`.  {ex}")



    @classmethod
    def add_schema_relationship_handler(cls, class_specs: dict) -> None:
        """

        In case of error, an Exception is raised.

        :param class_specs: A dictionary with the following
                DICTIONARY KEYS:
                    from_class_name
                    to_class_name
                    rel_name

        :return: None
        """
        from_class_name = class_specs["from_class_name"]
        from_class_name = from_class_name.strip()
        print("from_class_name: ", from_class_name)

        to_class_name = class_specs["to_class_name"]
        to_class_name = to_class_name.strip()
        print("to_class_name: ", to_class_name)

        rel_name = class_specs["rel_name"]
        rel_name = rel_name.strip()
        print("rel_name: ", rel_name)

        from_class_id = NeoSchema.get_class_id(from_class_name)
        to_class_id = NeoSchema.get_class_id(to_class_name)
        NeoSchema.create_class_relationship(from_id=from_class_id, to_id=to_class_id, rel_name=rel_name)



    @classmethod
    def delete_schema_relationship_handler(cls, class_specs: dict) -> None:
        """
        Delete the relationship(s) with the specified name
        between the 2 existing Class nodes (identified by their respective names),
        going in the from -> to direction direction.

        In case of error, an Exception is raised.

        :param class_specs: A dictionary with the following
                DICTIONARY KEYS:
                    from_class_name
                    to_class_name
                    rel_name

        :return: None
        """
        from_class_name = class_specs["from_class_name"]
        from_class_name = from_class_name.strip()
        print("from_class_name: ", from_class_name)

        to_class_name = class_specs["to_class_name"]
        to_class_name = to_class_name.strip()
        print("to_class_name: ", to_class_name)

        rel_name = class_specs["rel_name"]
        rel_name = rel_name.strip()
        print("rel_name: ", rel_name)

        # Delete the relationship(s)
        NeoSchema.delete_class_relationship(from_class=from_class_name, to_class=to_class_name, rel_name=rel_name)




    #######################     RECORDS-RELATED       #######################

    @classmethod
    def get_leaf_records(cls) -> [str]:
        """
        Get all Classes that are, directly or indirectly, INSTANCE_OF the Class "Records",
        as long as they are leaf nodes (with no other Class that is an INSTANCE_OF them.)

        EXAMPLE: if the "Foreign Vocabulary" Class is an INSTANCE_OF the Class "Records",
                 and if "French Vocabulary" and "German Vocabulary" are instances of "Foreign Vocabulary",
                 then "French Vocabulary" and "German Vocabulary" (but NOT "Foreign Vocabulary")
                 would be returned

        :return: A list of strings with the Class names
                 EXAMPLE:
                    ["Cuisine Type","Entrees","French Vocabulary","German Vocabulary","Restaurants","Site Link"]
        """

        return NeoSchema.get_class_instances("Records", leaf_only=True)



    @classmethod
    def get_records_schema_data(cls, category_id: int) -> [dict]:
        """
        TODO: test
        :param category_id:
        :return:
        """
        # Locate all the Classes of type record ("r") used by Content Items attached to the
        # given Category
        q = '''
            MATCH  (cat :BA {item_id: $category_id}) <- 
                        [:BA_in_category] - (rec :BA {schema_code:"r"}) - [:SCHEMA]->(cl:CLASS) 
            RETURN DISTINCT cl.name AS class_name, cl.schema_id AS schema_id
            '''

        class_list = cls.db.query(q, data_binding={"category_id": category_id})
        # EXAMPLE: [ {"class_name": "French Vocabulary" , "schema_id": 4},
        #            {"class_name": "Site Link" , "schema_id": 63}]


        # Now extract all the Property fields, in the schema-stored order, of the above Classes
        records_schema_data = {}
        for cl in class_list:
            prop_list = NeoSchema.get_class_properties(schema_id=cl["schema_id"], include_ancestors=True, sort_by_path_len="ASC")
            class_name = cl["class_name"]
            records_schema_data[class_name] = prop_list

        return records_schema_data




    #######################     CONTENT-ITEM RELATED      #######################

    @classmethod
    def get_text_media_content(cls, item_id: int, schema_code, public_required = False) -> str:
        """
        Fetch and return the contents of a media item stored on a local file,
        optionally requiring it to be marked as "public".
        In case of error, raise an Exception

        :param item_id:         An integer identifying the desired Content Item, which ought to be text media
        :param schema_code:     TODO: maybe phase out
        :param public_required: If True, the Content Item is returned only if has an the attribute "public: true"

        :return:                A string with the HTML text of the requested note;
                                    or an Exception in case of failure
                                    (e.g., if public_required is True and the item isn't public)

        """
        properties = {"item_id": item_id, "schema_code": schema_code}
        if public_required:
            properties["public"] = True     # Extend the match requirements

        match = cls.db.find(labels="BA", properties=properties)
        content_node = cls.db.get_nodes(match, single_row=True)
        #print("content_node:", content_node)
        if not content_node:    # Metadata not found
            raise Exception(f"The metadata for the Content Item (id {item_id}) wasn't found, or the items is not publicly accessible")

        basename = content_node['basename']
        suffix = content_node['suffix']
        filename = f"{basename}.{suffix}"

        try:
            file_contents = MediaManager.get_from_file(filename)
            return file_contents
        except Exception as ex:
            return f"I/O failure while reading in contents of item {item_id}. {ex}"     # File I/O failed



    @classmethod
    def get_binary_content(cls, item_id: int, th: str) -> (str, bytes):
        """
        Fetch and return the contents of a media item stored on a local file.
        In case of error, raise an Exception

        :param th:
        :param item_id:
        :return:    The binary data

        """
        match = cls.db.find(labels="BA", properties={"item_id": item_id})
        content_node = cls.db.get_nodes(match)
        #print("content_node:", content_node)
        if (content_node is None) or (content_node == []):
            raise Exception("Metadata not found")

        basename = content_node[0]['basename']
        suffix = content_node[0]['suffix']
        filename = f"{basename}.{suffix}"

        try:
            if th:
                file_contents = MediaManager.get_from_binary_file(cls.MEDIA_FOLDER + "resized/", filename)
            else:
                file_contents = MediaManager.get_from_binary_file(cls.MEDIA_FOLDER, filename)

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

        result = cls.db.query(q_out, data_binding={"item_id": item_id})
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
    def update_content_item(cls, post_data: dict) -> None:
        """
        Update an existing Content Item.
        In case of error, an Exception is raised

        NOTE: the "schema_code" field is currently required, but it's redundant.  Only
              used as a safety mechanism against incorrect values of item_id

        TODO: if any (non-special?) field is blank, drop it altogether from the node;
              maybe add this capability to set_fields()

        :return:    None
        """
        print("In update_content_item(). POST dict: ", post_data)

        # Validate the data
        schema_code = post_data.get("schema_code")   # If key not present, the value will be None
        print("Item Type: ", schema_code)

        try:
            item_id = int(post_data.get("item_id"))
        except Exception as ex:
            raise Exception(f"item_id is missing or not an integer. {ex}")

        print("Item Type: ", item_id)

        #print("All Item Data: ")
        #print("-----------")
        #for k, v in post_data.items():
            #print(k , " -> " , v)

        data_binding = post_data

        if item_id < 0:     # Validate item_id
            raise Exception(f"Bad item_id: {item_id}")


        set_dict = {}
        for k, v in data_binding.items():
            if k not in ("schema_code", "item_id"):    # Exclude some keys
                set_dict[k] = v

        # PLUGIN-SPECIFIC OPERATIONS that *change* set_dict and perform filesystem operations
        #       TODO: try to infer them from the Schema
        original_post_data = post_data.copy()   # Clone an independent copy of the dictionary - that won't be affected by changes to the original dictionary
        if schema_code == "n":
            set_dict = Notes.plugin_n_update_content(data_binding, set_dict)

        # TODO: utilize the schema layer, rather than directly access the database
        match = cls.db.find(labels="BA", properties={"item_id": item_id, "schema_code": schema_code})
        number_updated = cls.db.set_fields(match=match, set_dict=set_dict)

        if schema_code == "n":
            Notes.update_content_item_SUCCESSFUL(item_id, original_post_data)

        # If the update was NOT for a "note" (in which case it might only be about the note than its metadata)
        # verify that some fields indeed got changed
        if schema_code != "n" and number_updated == 0:
            raise Exception("No update performed")




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
            # If there's media involved, delete the media, too
            ###status = cls.delete_attached_media_file(item_id)
            status, record = cls.lookup_media_record(item_id)
            if status:
                MediaManager.delete_media_file(record["basename"], record["suffix"])

        if schema_code == "i":
            # Extra processing for the "Images" plugin
            ###status = cls.plugin_i_delete_content(item_id)
            status, record = cls.lookup_media_record(item_id)
            if status:
                MediaManager.delete_media_file(record["basename"], record["suffix"], subfolder="resized/")

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

        :param post_data:   A dict containing the following keys
            - "category_id"  (for the linking to a Category)
            - Schema-related keys:
                    * schema_code (Required)
                    * schema_id (Optional)
                    * class_name (Required only for Class Items of type "record")

            - insert_after        Either an item_id (int), or one of the special values "TOP" or "BOTTOM"
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
        #       TODO: invoke the plugin-specified code PRIOR to removing fields from the POST data
        original_post_data = post_data.copy()   # Clone an independent copy of the dictionary - that won't be affected by changes to the original dictionary
        if schema_code == "n":
            post_data = Notes.plugin_n_add_content(new_item_id, post_data)


        print("Revised post_data: ", post_data)
        # EXAMPLE:  {'text': 'My New Header'}
        # Note that several entries got removed from the dictionary;
        #       only the attributes that will go into the new node are still present.
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
        else:   # Insert at a position that is not the top nor bottom
            try:
                insert_after = int(insert_after)
            except Exception:
                raise Exception(f"`insert_after` must be an integer, unless it's 'TOP' or 'BOTTOM'. Value passed: `{insert_after}`")

            Categories.add_content_after_element(category_id=category_id,
                                             item_class_name=class_name, item_properties=post_data,
                                             insert_after=insert_after, new_item_id=new_item_id)


        # A final round of PLUGIN-SPECIFIC OPERATIONS
        if schema_code == "n":
            Notes.new_content_item_in_category_SUCCESSFUL(new_item_id, original_post_data)


        return new_item_id     # Success




    #######################     MEDIA-RELATED      #######################

    @classmethod
    def lookup_media_record(cls, item_id: int) -> tuple:
        """
        Delete the media file attached to the specified Content Item:
        """
        record = cls.db.get_record_by_primary_key("BA", "item_id", item_id)
        if record is None:
            return False, None

        if ("basename" not in record) or ("suffix" not in record):
            return False, None

        MediaManager.delete_media_file(record["basename"], record["suffix"])
        return True, record





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

        result = cls.db.get_nodes(match, limit=limit)

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
            upload_dir = current_app.config['UPLOAD_FOLDER']            # Defined in main file.  EXAMPLE: "D:/tmp/"
            (basename, full_filename, original_name) = UploadHelper.store_uploaded_file(request, upload_dir=upload_dir, key_name="imported_json", verbose=False)
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
            details = cls.db.import_json_dump(file_contents)
        except Exception as ex:
            return f"Import of JSON data failed: {ex}. {return_link}"

        # Now delete the temporary file created during the upload
        delete_status = MediaManager.delete_file(full_filename)

        # Prepare a status message to return
        status = f"File `{basename}` uploaded and imported successfully: {details}."
        if not delete_status:
            status += " However, the temporary import file could not be deleted."

        status += return_link

        return  status



    @classmethod
    def upload_import_json_file(cls, post_pars, verbose=False) -> str:
        """
        Manage the upload and import into the database of a data file in JSON format.

        :return:    Status string, if successful.  In case of error, an Exception is raised
        """
        print("In upload_import_json_file()")

        upload_dir = current_app.config['UPLOAD_FOLDER']            # Defined in main file.  EXAMPLE: "D:/tmp/"
                                                                    # TODO: maybe extract in the api_routing file
        # 'file' is just an identifier attached to the upload by the frontend
        (basename, full_filename, original_name) = UploadHelper.store_uploaded_file(request, upload_dir=upload_dir,
                                                                                    key_name=None, verbose=False)
        # basename and full name of the temporary file created during the upload

        assert post_pars["use_schema"], "Missing value for POST parameter `use_schema`"
        if post_pars["use_schema"] == "SCHEMA":
            assert post_pars["schema_class"], "Missing value for POST parameter `schema_class`"
        elif post_pars["use_schema"] == "NO_SCHEMA":
            assert post_pars["import_root_label"], "Missing value for POST parameter `import_root_label`"
        else:
            raise Exception(f"The value for the POST parameter `use_schema` must be 'SCHEMA' or 'NO_SCHEMA' (value passed: {post_pars['use_schema']})")


        # Read in the contents of the uploaded file
        with open(full_filename, 'r') as fh:
            file_contents = fh.read()
            if verbose:
                print(f"Contents of uploaded file:\n{file_contents}")

        file_size = len(file_contents)


        # Now delete the temporary file created during the upload.
        # TODO: maybe the API could offer the option to save the file as a Document
        MediaManager.delete_file(full_filename)

        # Import the JSON data into the database
        if post_pars["use_schema"] == "SCHEMA":
            new_ids = NeoSchema.import_json_data(file_contents, post_pars["schema_class"], provenance=original_name)
        else:
            new_ids = cls.db.import_json(file_contents, post_pars["import_root_label"], provenance=original_name)

        status = f"New top-level Neo4j node ID: {new_ids}"
        return f"Upload and import successful. {file_size} characters were read in. {status}"



    @classmethod
    def data_intake_status(cls):
        return cls.ongoing_data_intake


    @classmethod
    def do_stop_data_intake(cls) -> None:
        cls.ongoing_data_intake = False



    @classmethod
    def do_bulk_import(cls, intake_folder: str, outtake_folder: str, schema_class: str) -> str:
        """
        Bulk-import all the JSON files in the intake_folder directory.
        The import will continue until the folder is empty,
        or until the cls.ongoing_data_intake property is set to False

        Failure of individual imports is logged, but does not terminate the operation.
        An Exception is raised if any of the following happens:
            * The log file cannot be accessed/created
            * Any of the data files cannot be moved to their final destination

        :param intake_folder:   Name of folder (ending with "/") where the files to import are located
        :param outtake_folder:
        :param schema_class:
        :return: 
        """

        cls.ongoing_data_intake = True          # Activate the continuous intake

        file_list = os.listdir(intake_folder)   # List of filenames in the folder ("snapshot" of folder contents)

        # As long as files are present in the intake folder
        while file_list:
            #print(file_list)
            msg = f"{len(file_list)} file(s) found in the intake folder"
            print(msg)
            cls.append_to_log(msg)

            # Process all the files that were in the folder
            for f in file_list:
                if not cls.ongoing_data_intake:     # Before each import, check a switch that aborts the continuous-intake mode
                    msg = f"Detected request to stop ongoing import. Running total count of imported files is {cls.import_file_count}"
                    cls.append_to_log(msg)
                    return msg

                cls.process_file_to_import(f, intake_folder, outtake_folder, schema_class)

            file_list = os.listdir(intake_folder)    # Check if new files have arrived, while processing the earlier folder contents

        # TODO: instead of returning, sleep for progressively longer times, checking for new file arrivals

        msg = f"Processed all files. Running total count of imported files is {cls.import_file_count}"
        cls.append_to_log(msg)
        return msg



    @classmethod
    def process_file_to_import(cls, f: str, intake_folder: str, outtake_folder: str, schema_class: str) -> None:
        """
        Import a JSON file, located in a particular folder, and then move it to a designated folder.
        Keep a log of the operations.
        Exceptions are caught and logged; if the Exceptions involves moving the process file, a new one is raised

        :param f:               Name of file to import
        :param intake_folder:   Name of folder (ending with "/") where the files to import are located
        :param outtake_folder:
        :param schema_class:
        :return:                None
        """

        print(f"Processing file `{f}`...")

        src_fullname = f"{intake_folder}{f}"
        dest_fullname = f"{outtake_folder}{f}"

        #sleep(2)    # TODO: temp, for testing

        try:
            # Read in the contents of the data file to import
            with open(src_fullname, 'r') as fh:
                file_contents = fh.read()

            file_size = len(file_contents)

        except Exception as ex:
            error_msg = f"Failed to open/read file `{f}` : {ex}"
            print(error_msg)
            cls.append_to_log(error_msg)
            cls.archive_data_file(src_fullname, dest_fullname, outtake_folder)
            return    # Go back to resume the import loop


        # Import the JSON data into the database
        try:
            if len(file_contents) > 25:
                abridged_file_contents = file_contents[:25] + " ..."
            else:
                abridged_file_contents = file_contents

            print(f"About to import using: "
                  f"file_contents: `{abridged_file_contents}`, schema_class: `{schema_class}`, provenance: `{f}`")

            # Make a log of the PRE-import state
            log_msg = f'({cls.import_file_count}) Starting import of data file "{f}"'
            cls.append_to_log(log_msg)

            # ** THE ACTUAL IMPORT
            new_ids = NeoSchema.import_json_data(file_contents, schema_class, provenance=f)

            cls.import_file_count += 1

            # Make a log of the post-import operation
            log_msg = f'({cls.import_file_count}) Imported data file "{f}", {file_size} bytes, new Neo4j IDs: {new_ids}\n'
            cls.append_to_log(log_msg)

            cls.archive_data_file(src_fullname, dest_fullname, outtake_folder)

        except Exception as ex:
            error_msg = f"Failed import of of file `{f}` : {ex}"
            print(error_msg)
            cls.append_to_log(error_msg)
            cls.archive_data_file(src_fullname, dest_fullname, outtake_folder)
            return    # Go back to resume the import loop



    @classmethod
    def archive_data_file(cls, src_fullname, dest_fullname, outtake_folder) -> None:
        """
        Move the processed file to its final location.
        In case of error, the Exception is caught, logged and re-raised

        :param src_fullname:
        :param dest_fullname:
        :param outtake_folder:
        :return:                None
        """
        print(f"    ...processing complete.  Moving file to folder `{outtake_folder}`\n\n")
        try:
            shutil.move(src_fullname, dest_fullname)
        except Exception as ex:
            error_msg = f"Failed move of file `{src_fullname}` to destination folder `{outtake_folder}` : {ex}"
            print(error_msg)
            cls.append_to_log(error_msg)
            raise Exception(error_msg)      # The Exception is re-raised, because failure to move a file must stop the continuous import


    @classmethod
    def init_logfile(cls) -> None:
        """
        Prepare a handle for the log file

        :return:
        """
        # Open (creating it if necessary) the log file
        try:
            cls.log_file_handle = open(cls.LOG_FOLDER + cls.log_filename, "a")  # If not present, create it
        except Exception as ex:
            error_msg = f"Unable to open or create a log file named {cls.LOG_FOLDER + cls.log_filename} : {ex}"
            print(error_msg)
            #raise Exception(error_msg)     # TODO: This should happen at program startup, in main



    @classmethod
    def append_to_log(cls, msg) -> None:
        """

        :param msg:
        :return:
        """
        # Prepare timestamp
        now = datetime.now()
        dt_string = now.strftime("%m/%d/%Y %H:%M")   # mm/dd/YY H:M    (for seconds, add  :%S)

        if cls.log_file_handle is None:
            cls.init_logfile()

        # Make a log of the operation
        try:
            cls.log_file_handle.write(f"{dt_string} - {msg}\n")
            cls.log_file_handle.flush()             # To avoid buffering issues
        except Exception as ex:
            # To deal with situation where the log file got deleted/moved by user, but we're still attempting to use the old handle
            cls.init_logfile()




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
