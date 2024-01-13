from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema
from BrainAnnex.modules.categories.categories import Categories
from BrainAnnex.modules.PLUGINS.notes import Notes
from BrainAnnex.modules.PLUGINS.documents import Documents
from BrainAnnex.modules.upload_helper.upload_helper import UploadHelper
from BrainAnnex.modules.media_manager.media_manager import MediaManager, ImageProcessing
from BrainAnnex.modules.full_text_indexing.full_text_indexing import FullTextIndexing
import re                               # For REGEX
import pandas as pd
import os
from flask import request, current_app  # TODO: phase out (?)
from typing import Union
import shutil
import requests
import html
from datetime import datetime


"""
    MIT License.  Copyright (c) 2021-2023 Julian A. West     BrainAnnex.org
"""



class DataManager:
    """
    For general, high-level database-interaction operations.
    Used by the UI for Page Generation,
    as well as by the web API to produce data for the endpoints.

    This class does NOT get instantiated.
    """
    # The "db" and several other class properties get set by InitializeBrainAnnex.set_dbase()

    db = None           # Object of class "NeoAccess".  MUST be set before using this class!

    LOG_FOLDER = None   # Location where the log file is stored

    ongoing_data_intake = False
    import_file_count = 0

    log_filename = "IMPORT_LOG.txt"     # TODO: generalize to BrainAnnex-wide
    log_file_handle = None




    #######################     LOW-LEVEL DATABASE-NODE UTILITIES       #######################

    @classmethod
    def get_node_labels(cls) -> [str]:
        """
        Look up and return a list of all the node labels in the database.
        EXAMPLE: ["my_label_1", "my_label_2"]

        :return:    A list of strings
        """

        label_list = cls.db.get_labels()        # Fetch all the node labels in the database

        return label_list



    @classmethod
    def add_new_label(cls, label: str) -> int:
        """
        Create a new blank node with the specified label.
        Mostly used for testing.

        :return:    The internal database ID of the new node
        """

        return  cls.db.create_node(label)




    #####################################################################################################

    '''                                      ~   UTILITIES   ~                                        '''

    def ________UTILITIES________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################

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
        except ValueError:
            return s



    @classmethod
    def str_to_int(cls, s: str) -> int:
        """
        Helper function to give more friendly error messages in case non-integers are passed
        in situations where integers are expected.
        Without this function, the user would see cryptic messages such as
        "invalid literal for int() with base 10: 'q123'"

        EXAMPLE of usage:
            try:
                i = cls.str_to_int(i_str)
            except Exception as ex:
                # Do something

        :param s:   A string that should represent an integer
        :return:    The integer represented in the passed string, if applicable;
                        if not, an Exception is raised
        """
        #TODO: no longer being used.  Perhaps eliminate
        try:
            i = int(s)
        except Exception:
            raise Exception(f"The passed parameter ({s}) is not an integer as expected")

        return i



    @classmethod
    def experimental_par_dict_cleaner(cls, data_dict, required_par_list=None, int_list={}) -> dict:
        """
        NOT IN CURRENT USE YET
        TODO: test, and start using
        "Cleaner" for general dictionaries of parameters

        :param data_dict:           A generic dictionary of parameters
        :param required_par_list:   List of names of keys whose presence is required
        :param int_list:            List of names of keys whose values need to be integers
        :return:
        """
        if required_par_list:
            for par in required_par_list:
                assert par in data_dict, f"The expected parameter `{par}` is missing from the data"


        for key, val in data_dict.items():

            if val in int_list:
                try:
                    val = int(val)
                except Exception:
                    raise Exception(f"The passed parameter `{key}` is not an integer as expected; its value ({val} is of type {type(val)}")

            elif type(val) == str:
                val = val.strip()

            data_dict[key] = val

        return data_dict




    #####################################################################################################

    '''                                    ~   SCHEMA-RELATED   ~                                     '''

    def ________SCHEMA_RELATED________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################
    # TODO: possibly move to separate class

    @classmethod
    def all_schema_classes(cls) -> [str]:
        """
        Return a list of all the existing Schema classes
        :return:
        """
        return NeoSchema.get_all_classes()


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
        new_id, _ = NeoSchema.create_class_with_properties(new_class_name, property_list_clean,
                                                           class_to_link_to=instance_of_class, link_name="INSTANCE_OF")


        # If requested, link to another existing class
        if ("linked_to" in class_specs) and ("rel_name" in class_specs) and ("rel_dir" in class_specs):
            linked_to = class_specs["linked_to"]
            #linked_to_id = NeoSchema.get_class_id(class_name = linked_to)
            #print(f"Linking the new class to the existing class `{linked_to}`, which has ID {linked_to_id}")
            print(f"Linking the new class to the existing class `{linked_to}`")
            rel_name = class_specs["rel_name"]
            rel_dir = class_specs["rel_dir"]    # The link direction is relative to the newly-created class node
            print(f"rel_name: `{rel_name}` | rel_dir: {rel_dir}")

            assert rel_dir == "OUT" or rel_dir == "IN", f"The value for rel_dir must be either 'IN' or 'OUT' (passed value was {rel_dir})"

            try:
                if rel_dir == "OUT":
                    NeoSchema.create_class_relationship(from_class=new_id, to_class=linked_to, rel_name=rel_name)
                elif rel_dir == "IN":
                    NeoSchema.create_class_relationship(from_class=linked_to, to_class=new_id, rel_name=rel_name)
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
        #print("from_class_name: ", from_class_name)

        to_class_name = class_specs["to_class_name"]
        to_class_name = to_class_name.strip()
        #print("to_class_name: ", to_class_name)

        rel_name = class_specs["rel_name"]
        rel_name = rel_name.strip()
        #print("rel_name: ", rel_name)

        NeoSchema.create_class_relationship(from_class=from_class_name, to_class=to_class_name, rel_name=rel_name)



    @classmethod
    def schema_add_property_to_class_handler(cls, specs_dict: dict) -> None:
        """
        Add a new Property to an existing Classes

        In case of error, an Exception is raised.

        :param specs_dict: A dictionary with the following
                DICTIONARY KEYS:
                    prop_name       (any leading/trailing blanks are ignored)
                    class_name      (any leading/trailing blanks are ignored)

        :return: None
        """
        prop_name = specs_dict.get("prop_name")
        if not prop_name:
            raise Exception("The expected parameter `prop_name` is missing from the data")


        class_name = specs_dict.get("class_name")
        if not class_name:
            raise Exception("The expected parameter `class_name` is missing from the data")


        # Locate the internal ID of the Class node
        class_internal_id = NeoSchema.get_class_internal_id(class_name.strip())
        number_prop_added = NeoSchema.add_properties_to_class(class_node= class_internal_id, property_list = [prop_name])
        if number_prop_added != 1:
            raise Exception(f"Failed to add the new Property `{prop_name}` to the Class `{class_name}` (internal ID {class_internal_id})")



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
        #print("from_class_name: ", from_class_name)

        to_class_name = class_specs["to_class_name"]
        to_class_name = to_class_name.strip()
        #print("to_class_name: ", to_class_name)

        rel_name = class_specs["rel_name"]
        rel_name = rel_name.strip()
        #print("rel_name: ", rel_name)

        # Delete the relationship(s)
        NeoSchema.delete_class_relationship(from_class=from_class_name, to_class=to_class_name, rel_name=rel_name)




    #######################     RECORDS-RELATED       #######################

    @classmethod
    def add_data_relationship_handler(cls, data_dict: dict) -> None:
        """
        Add the specified relationship (edge) between data nodes.
        In case of error, an Exception is raised.

        :param data_dict: A dictionary with the following
                from                    The uri of the node from which the relationship originates
                to                      The uri of the node into which the relationship takes
                rel_name                The name of the relationship to add
                schema_code (optional)  If passed, the appropriate plugin gets invoked

        :return: None
        """
        from_id = data_dict['from']
        to_id = data_dict['to']
        rel_name = data_dict['rel_name']
        schema_code = data_dict.get('schema_code')         # Tolerant of missing values

        if schema_code == "cat":        # TODO: take this part away?
            Categories.add_relationship_before(from_id=from_id, to_id=to_id,
                                               rel_name=rel_name)       # Category-specific action

        # The adding of the relationship is done here
        NeoSchema.add_data_relationship_OLD(from_id=from_id, to_id=to_id,
                                            rel_name=rel_name, id_type="uri")




    @classmethod
    def remove_data_relationship_handler(cls, data_dict: dict) -> None:
        """
        Remove the specified relationship (edge) between data nodes.
        In case of error, an Exception is raised.

        :param data_dict: A dictionary with the following
                DICTIONARY KEYS:
                    from                    The uri of the node from which the relationship originates
                    to                      The uri of the node into which the relationship takes
                    rel_name                The name of the relationship to remove
                    schema_code (optional)  If passed, the appropriate plugin gets invoked

        :return: None
        """
        from_uri = data_dict['from']
        to_uri = data_dict['to']
        rel_name = data_dict['rel_name']
        schema_code = data_dict.get('schema_code')         # Tolerant of missing values

        if schema_code == "cat":
            Categories.remove_relationship_before(from_id=from_uri, to_id=to_uri,
                                                  rel_name=rel_name)       # Category-specific action

        NeoSchema.remove_data_relationship(from_uri=from_uri, to_uri=to_uri,
                                           rel_name=rel_name, labels="BA")



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




    #######################     CONTENT-ITEM RELATED      #######################

    @classmethod
    def get_text_media_content(cls, uri :str, schema_code, public_required = False) -> str:
        """
        Fetch and return the contents of a media item stored on a local file,
        optionally requiring it to be marked as "public".
        In case of error, raise an Exception

        :param uri:             A string identifying the desired Content Item, which ought to be text media
        :param schema_code:     TODO: maybe phase out
        :param public_required: If True, the Content Item is returned only if has an the attribute "public: true"

        :return:                A string with the HTML text of the requested note;
                                    or an Exception in case of failure
                                    (e.g., if public_required is True and the item isn't public)

        """
        properties = {"uri": uri, "schema_code": schema_code}
        if public_required:
            properties["public"] = True     # Extend the match requirements

        match = cls.db.match(labels="BA", properties=properties)
        content_node = cls.db.get_nodes(match, single_row=True)
        #print("content_node:", content_node)
        if content_node is None:    # Metadata not found
            raise Exception(f"The metadata for the Content Item (uri: `{uri}`) wasn't found, or the items is not publicly accessible")

        basename = content_node['basename']
        suffix = content_node['suffix']
        filename = f"{basename}.{suffix}"

        folder = MediaManager.lookup_file_path(schema_code=content_node['schema_code'])     # Includes the final "/"

        try:
            file_contents = MediaManager.get_from_text_file(folder, filename, encoding="utf8")
            return file_contents
        except Exception as ex:
            return f"I/O failure while reading in contents of Item with URI `{uri}`. {ex}"     # File I/O failed



    @classmethod
    def get_records_by_link(cls, request_data: dict) -> [dict]:
        """
        Locate and return the data of the nodes linked to the one specified by uri,
        by the relationship named by rel_name, in the direction specified by dir

        :param request_data: A dictionary with 3 keys, "uri", "rel_name", "dir"
        :return:             A list of dictionaries with all the properties of the neighbor nodes
        """
        uri = request_data["uri"]               # This must be a string
        rel_name = request_data["rel_name"]
        dir = request_data["dir"]               # Must be either "IN or "OUT"

        assert dir in ["IN", "OUT"], \
            f"get_records_by_link(): The value of the parameter `dir` must be either 'IN' or 'OUT'. The value passed was '{dir}'"
        assert type(uri) == str, \
            "get_records_by_link(): The value of the parameter `uri` must be an integer"

        match = cls.db.match(labels="BA", key_name="uri", key_value=uri)

        return cls.db.follow_links(match, rel_name=rel_name, rel_dir=dir, neighbor_labels ="BA")



    @classmethod
    def get_link_summary(cls, uri :str, omit_names = None) -> dict:
        """
        Return a dictionary structure identifying the names and counts of all
        inbound and outbound links to/from the given data node.
        TODO: move most of it to the "~ FOLLOW LINKS ~" section of NeoAccess

        :param uri:         String with the URI of a data node
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
                MATCH (n :BA {{uri:$uri}})-[r]->(n2 :BA)
                {where_clause}
                RETURN type(r) AS rel_name, count(n2) AS rel_count
                '''

        result = cls.db.query(q_out, data_binding={"uri": uri})
        rel_out = [ [ l["rel_name"],l["rel_count"] ] for l in result ]


        # Get inbound links (names and counts)
        q_in = f'''
                MATCH (n :BA {{uri:$uri}})<-[r]-(n2 :BA)
                {where_clause}
                RETURN type(r) AS rel_name, count(n2) AS rel_count
                '''

        result = cls.db.query(q_in,data_binding={"uri": uri})
        rel_in = [ [ l["rel_name"],l["rel_count"] ] for l in result ]

        return  {"in": rel_in, "out": rel_out}




    ##############   MODIFYING CONTENT ITEMS   ##############

    @classmethod
    def update_content_item(cls, post_data: dict) -> None:
        """
        Update an existing Content Item.
        In case of error, an Exception is raised

        NOTE: the "schema_code" field is currently required, but it's redundant.  Only
              used as a safety mechanism against incorrect values of the URI
              (TODO: maybe ditch, or use the Class name instead)

        :return:    None.  In case of error, an Exception is raised
        """
        #TODO: if any (non-special?) field is blank, drop it altogether from the node;
        #      maybe add this capability to set_fields()

        #print("In update_content_item(). POST dict: ", post_data)

        # Validate the data
        schema_code = post_data.get("schema_code")   # If key not present, the value will be None
        #print("Item Type: ", schema_code)

        uri = post_data.get("uri")
        assert uri, "update_content_item(): a value for `uri` is missing from the POST data"

        #print("Item Type: ", uri)


        data_binding = post_data


        set_dict = {}       # Dictionary of field values to set
        for k, v in data_binding.items():
            if k not in ("schema_code", "uri"):    # Exclude some special keys
                set_dict[k] = v


        # First, make sure that the requested Content Item exists.
        # TODO: get assistance from Schema layer.  Try:
        #       assert NeoSchema.data_node_exists(data_node=uri), f"update_content_item(): no Content Item found with URI `{uri}` and Schema Code '{schema_code}'
        match = cls.db.match(labels="BA", properties={"uri": uri, "schema_code": schema_code})
        records = cls.db.get_nodes(match)
        assert records != [], f"update_content_item(): no Content Item found with URI `{uri}` and Schema Code '{schema_code}'"


        # PLUGIN-SPECIFIC OPERATIONS that *change* set_dict and perform filesystem operations
        #       TODO: try to infer them from the Schema
        original_post_data = post_data.copy()   # Clone an independent copy of the dictionary - that won't be affected by changes to the original dictionary

        # TODO: instead of passing along in the POST request things like `basename` and `suffix`
        #       (which place a burden on the front end),
        #       get them from the database, and just pass all the node attributes to the plugin-specific modules
        #       Try:
        #           db_data = NeoSchema.fetch_data_node(uri=uri)
        #           Then pass db_data as a parameter to the plugin-specific modules


        if schema_code == "n":
            if data_binding.get("basename") == "undefined":
                raise Exception("update_content_item(): attempting "
                                "to pass a `basename` attribute to the value 'undefined'")
            set_dict = Notes.before_update_content(data_binding, set_dict)

        # Update, possibly adding and/or dropping fields, the properties of the existing Data Node
        #internal_dbase_id = NeoSchema.get_data_node_internal_id(uri)    # TODO: this will become unnecessary after switching to string uri's
        #number_updated = NeoSchema.update_data_node(data_node=internal_dbase_id, set_dict=set_dict, drop_blanks=True)
        number_updated = NeoSchema.update_data_node(data_node=uri, set_dict=set_dict, drop_blanks=True)

        if schema_code == "n":
            Notes.update_content_item_successful(uri, original_post_data)

        # If the update was NOT for a "note" (in which case it might only be about the note's body than its metadata)
        # verify that some fields indeed got changed
        if schema_code != "n" and number_updated == 0:
            raise Exception("No update performed")




    @classmethod
    def delete_content_item(cls, uri: str, schema_code: str) -> None:
        """
        Delete the specified individual Content Item.
        Note that schema_code is redundant.
        In case of error, an Exception is raised

        :param uri:         String version of the unique ID
        :param schema_code: Redundant
        :return:            None.  In case of error, an Exception is raised
        """
        #print(f"In delete_content_item(). Attempting to delete URI `{uri}` of type `{schema_code}`")

        assert uri, "delete_content_item(): argument `uri` is missing"


        # First, make sure that the requested Content Item exists.  TODO: get assistance from Schema layer
        match = cls.db.match(labels="BA", properties={"uri": uri, "schema_code": schema_code})
        records = cls.db.get_nodes(match)
        assert records != [], f"delete_content_item(): no Content Item found with URI `{uri}` and Schema Code '{schema_code}'"


        # PLUGIN-SPECIFIC OPERATIONS (often involving changes to files)
        #       (TODO: try to infer that from the Schema)
        if schema_code in ["n", "i", "d"]:
            # If there's media involved, delete the media, too
            record = cls.lookup_media_record(uri)
            if record is not None:
                MediaManager.delete_media_file(record["basename"], record["suffix"], schema_code)

        if schema_code == "i":
            # TODO: move this to the Images plugin, which should provide an Images.delete_content_before() method
            # Extra processing for the "Images" plugin (for the thumbnail images)
            record = cls.lookup_media_record(uri)
            if record is not None:
                MediaManager.delete_media_file(record["basename"], record["suffix"], schema_code, thumbs=True)

        if schema_code == "n":
            Notes.delete_content_before(uri)


        # Perform the actual deletion of the Content Item node
        number_deleted = cls.db.delete_nodes(match)     # TODO: switch to using the Schema layer


        if number_deleted == 1:
            if schema_code == "n":
                # Extra processing for the "Notes" plugin
                Notes.delete_content_successful(uri)    # Not actually needed for notes, but setting up the general system

            return       # Successful termination, with 1 Content Item deleted, as expected

        elif number_deleted == 0:
            raise Exception(f"Unable to delete Content Item id {uri} of type `{schema_code}`")  # Error message (nothing deleted)
        else:
            raise Exception(f"{number_deleted} Content Items deleted, instead of the expected 1")    # Error message (too much deleted)
                                                                                                     # Should not happen, since uri is a primary key


    @classmethod
    def new_content_item_in_category(cls, post_data: dict) -> str:
        """
        Create a new Content Item attached to a particular Category,
        at a specified position on the Category page

        :param post_data:   A dict containing the following keys
            - "category_id"  (for the linking to a Category)
            - Schema-related keys:
                    * schema_code (Required)
                    * schema_id (Optional)
                    * class_name (Required only for Class Items of type "record")

            - insert_after        Either a URI of an existing Content Item attached to this Category,
                                  or one of the special values "TOP" or "BOTTOM"
            - *PLUS* all applicable plugin-specific fields (all the key/values for the new Content Item)

        :return:    The URI of the newly-created node.
                    In case of error, an Exception is raised
        """

        # NOTE: the post_data dictionary contains entries are not part of the data dictionary for the new Content Item;
        #       those will be eliminated below

        # Validate the data, and extract some special attributes, while also paring down the post_data dictionary

        # TODO: give better error messages; for example, if the requested Category doesn't exist

        # TODO: possibly generalize from "Category" to "Collection"

        # Category-related data
        category_id = post_data.get("category_id")  # If the key isn't present, the value will be None
        if not category_id:
            raise Exception("Missing Category ID")
        del post_data["category_id"]        # Remove this entry from the dictionary

        # Positioning within the Category
        insert_after = post_data.get("insert_after")
        if not insert_after:
            raise Exception("Missing insert_after (URI of Item to insert the new one after)")
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
            class_name = NeoSchema.get_class_name_by_schema_id(schema_id)
            print(f"class_name looked up as: `{class_name}`")


        # Generate a new ID (which is needed by some plugin-specific modules)
        new_uri = NeoSchema.next_available_datanode_uri()
        print("New item will be assigned ID:", new_uri)

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
            post_data = Notes.add_content(new_uri, post_data)


        print("Revised post_data: ", post_data)
        # EXAMPLE:  {'text': 'My New Header'}
        # Note that several entries got removed from the dictionary;
        #       only the attributes that will go into the new node are still present.
        #       Some attributes may have been added by a plugin-specific module

        if post_data.get("basename") == "undefined":    # TODO: maybe extend to ALL fields being set!
            raise Exception("new_content_item_in_category(): attempting "
                            "to set a `basename` attribute to the value 'undefined'")

        # Create the new node and required relationships
        if insert_after == "TOP":
            Categories.add_content_at_beginning(category_uri=category_id,
                                                item_class_name=class_name, item_properties=post_data,
                                                new_uri=new_uri)
        elif insert_after == "BOTTOM":
            Categories.add_content_at_end(category_uri=category_id,
                                          item_class_name=class_name, item_properties=post_data,
                                          new_uri=new_uri)
        else:   # Insert at a position that is not the top nor bottom
            Categories.add_content_after_element(category_uri=category_id,
                                                 item_class_name=class_name, item_properties=post_data,
                                                 insert_after=insert_after, new_uri=new_uri)


        # A final round of PLUGIN-SPECIFIC OPERATIONS
        if schema_code == "n":
            Notes.new_content_item_successful(new_uri, original_post_data)


        return new_uri     # Success



    @classmethod
    def new_content_item_in_category_final_step(cls, insert_after :str, category_id :str, new_uri, class_name,
                                                post_data, original_post_data):
        # TODO: NOT YET IN USE
        #       Meant to take over the final parts of BA_Api_Routing.upload_media() and DataManager.new_content_item_in_category()
        # Create the new node and required relationships
        if insert_after == "TOP":
            Categories.add_content_at_beginning(category_uri=category_id,
                                                item_class_name=class_name, item_properties=post_data,
                                                new_uri=new_uri)
        elif insert_after == "BOTTOM":
            Categories.add_content_at_end(category_uri=category_id,
                                          item_class_name=class_name, item_properties=post_data,
                                          new_uri=new_uri)
        else:   # Insert at a position that is not the top nor bottom
            Categories.add_content_after_element(category_uri=category_id,
                                                 item_class_name=class_name, item_properties=post_data,
                                                 insert_after=insert_after, new_uri=new_uri)


        # A final round of PLUGIN-SPECIFIC OPERATIONS
        if class_name == "Notes":
            Notes.new_content_item_successful(new_uri, original_post_data)
        elif class_name == "Documents":
            Documents.new_content_item_successful(new_uri, original_post_data, mime_type='text/plain')  #TODO: check the MIME type




    #######################     MEDIA-RELATED      #######################

    @classmethod
    def lookup_media_record(cls, uri: int) -> Union[dict, None]:
        """
        Attempt to retrieve the metadata for the media file attached to the specified Content Item
        TODO: move to MediaManager class

        :param uri: An integer with the URI of the Content Item
        :return:        If found, return a dict with the record; otherwise, return None
        """
        record = cls.db.get_record_by_primary_key("BA", "uri", uri)
        if record is None:
            return None

        if ("basename" not in record) or ("suffix" not in record):
            return None

        return record




    #####################################################################################################

    '''                                        ~   SEARCH   ~                                         '''

    def ________SEARCH________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################

    @classmethod
    def search_for_word(cls, word: str) -> [dict]:
        """
        Look up any stored words that contains the requested string
        (ignoring case and leading/trailing blanks.)

        Then locate the Content nodes that are indexed by any of those words.
        Return a (possibly empty) list of the data of all the found nodes.

        :param word:    A string, typically containing a word or word fragment;
                            case and leading/trailing blanks are ignored
        :return:
        """
        result = FullTextIndexing.search_word(word, all_properties=True)
        # EXAMPLE:
        #   [{'basename': 'notes-2', 'uri': 55, 'schema_code': 'n', 'title': 'Beta 23', 'suffix': 'htm', 'internal_id': 318, 'neo4j_labels': ['BA', 'Notes']},
        #    {'basename': 'notes-3', 'uri': 14, 'schema_code': 'n', 'title': 'undefined', 'suffix': 'htm', 'internal_id': 3, 'neo4j_labels': ['BA', 'Notes']}}
        #   ]

        for node in result:
            internal_id = node["internal_id"]   # Ignore the PyCharm's complain about the data type!
            #print("\n\n--- internal_id: ", internal_id)


            # TODO: generalize the following line, to other types of links
            neighbor_props = cls.db.follow_links(match=internal_id,
                                                rel_name="BA_in_category", rel_dir="OUT", neighbor_labels="Categories")
            # EXAMPLE of neighbor_props:
            #   [{'uri': 966, 'schema_code': 'cat', 'name': "Deploying VM's on Oracle cloud"}]
            #print(neighbor_props)
            node["internal_links"] = neighbor_props

            if "date_created" in node:
                del node["date_created"]    # Datetime objects aren't serializable and lead to Flask errors
                                            # TODO: go beyond this ad-hoc fix!

            '''
            #TODO: consider the following generalized approach
            
            new_result = []     # SET OUTSIDE of this loop
            
            labels = node["neo4j_labels"]
            del node["internal_id"]
            del node["neo4j_labels"]
            dn = NeoSchema.DataNode(internal_id=internal_id, labels=labels], properties=node)
            # All the above lines would be un-necessary if FullTextIndexing.search_word returned a DataNode object!
            
            for neighbor_data in neighbor_props:
                neighbor_node = NeoSchema.DataNode(internal_id=None, labels="Categories", properties=neighbor_data)
                dn.add_relationship(link_name="BA_in_category", link_direction="OUT", link_properties=None, node_obj=neighbor_node)
                
            new_result.append(dn)
            
            # And then return new_result outside of the loop
            '''


        # Note: attributes 'pos' and 'class_name' (used by some HTML templates) are not in the the result
        #print("------- RESULT -------------  :\n", result)
        return result



    @classmethod
    def extract_website_title(cls, url :str) -> str:
        """
        Retrieve the Title of a remote webpage, given its URL

        :param url: URL of the website whose title we want to fetch.
                        EXAMPLE:  "https://brainannex.org"
        :return:    The "Title" of the website.
                        In case unable to locate the web page, or unable to extract its Title,
                        raise an Exception
        """
        response = requests.get(url, allow_redirects=True)

        if response.status_code == 200:     # Normal response code from remote website
            #print(response.text[:800])     # Show the early part of the file

            # Use regular expressions to find the title tag
            title_match = re.search(r'<title.*?>(.*?)</title>', response.text, re.IGNORECASE)
            #    .    means "any single character, except line breaks"
            #    *?   means "0 or more times (non-greedy)"
            #    ()   means "capture group"

            # TODO: some websites contain alternate way to express titles, such as:
            #       <meta data-react-helmet="true" name="title" content="THE REAL PAGE TITLE">

            if title_match:
                title = title_match.group(1)            # The 1st capture group
                unescaped_title = html.unescape(title)  # Turn HTML entities into characters;
                                                        # e.g. "&ndash;" into "-"
                print(unescaped_title)
                return unescaped_title
            else:
                err_status = f"Unable to extract title from website at {url}"
                raise Exception(err_status)     # Found the web page, but couldn't extract its title

            '''
            # Alternate approach using BeautifulSoup (untested):
            
                from bs4 import BeautifulSoup
                # Parse the HTML content
                soup = BeautifulSoup(response.text, 'html.parser')                  
                # Extract the title element and its text
                title = soup.title.string if soup.title else 'No Title Found
            '''

        else:   # Response status other that 200
            err_status =  f'Remote page ({url}) returned failure code {response.status_code}'
            raise Exception(err_status)         # Problems with locating the web page





    #####################################################################################################

    '''                                        ~   FILTERS   ~                                        '''

    def ________FILTERS________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################


    @classmethod
    def get_nodes_by_filter(cls, filter_dict) -> [dict]:
        """

        :param filter_dict: A dictionary.
                            EXAMPLE: {"labels": "BA", "key_name": "uri", "key_value": 123, "limit": 25}

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

        match = cls.db.match(labels=labels, key_name=key_name, key_value=key_value)

        if limit > 500:
            limit = 500     # Set an upper bound

        result = cls.db.get_nodes(match, limit=limit)

        return result




    #####################################################################################################

    '''                                  ~   IMPORT-EXPORT   ~                                        '''

    def ________IMPORT_EXPORT________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################

    @classmethod
    def export_full_dbase(cls):
        return cls.db.export_dbase_json()



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
        return_link = "" if return_url is None else f" <a href='{return_url}'>GO BACK</a><br><br>"

        try:
            upload_dir = current_app.config['UPLOAD_FOLDER']            # Defined in main file.  EXAMPLE: "D:/tmp/"
            (basename, full_filename, original_name, mime_type) = \
                        UploadHelper.store_uploaded_file(request, upload_dir=upload_dir, key_name="imported_json", verbose=False)
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
            details = cls.db.import_json_dump(file_contents)    # THE ACTUAL IMPORT TAKES PLACE HERE
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
        (basename, full_filename, original_name, mime_type) = \
                    UploadHelper.store_uploaded_file(request, upload_dir=upload_dir, key_name=None, verbose=False)
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
        """
        Request that the continuous data import cease upon the completion of the current import

        :return:    None
        """
        #print("do_stop_data_intake(): stopping the data intake")
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
        cls.ongoing_data_intake = False          # De-activate the continuous intake
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
    def import_datafile(cls, basename, full_filename, test_only=True) -> str:
        """
        TODO: NOT in current use.  See DocumentationGenerator.import_python_file()
        TODO: generalize!  For now, used for an ad-hoc import, using REGEX to extract the desired fields

        :param basename:        EXAMPLE: "my_file_being_uploaded.txt"
        :param full_filename:   EXAMPLE: "D:/tmp/my_file_being_uploaded.txt"
        :param test_only:       If True, the file is parsed, but nothing is actually added to the database

        :return:                String with status message (whether successful or not)
        """
        return "NOT IN CURRENT USE"

        n_chars_to_show = 400
        try:
            with open(full_filename, 'r') as fh:
                file_contents = fh.read()
                print(f"\n--- First {n_chars_to_show} bytes of uploaded file:\n{file_contents[:n_chars_to_show]}")
        except Exception:
            return f"import_datafile(): File I/O failed (on uploaded file {full_filename})"


        pattern = cls.define_pattern()
        print("Pattern used for the matches: ", pattern)

        all_matches = re.findall(pattern, file_contents, re.DOTALL)
        # It returns (possibly-empty) list of tuples
        # OR a list of strings (if there's only 1 capture group in pattern)

        #print("all_matches: ", all_matches)

        # Zap leading/trailing blanks from all entries, and add 2 extra fields (for uri and schema_code)
        '''
        id_offset = NeoSchema.next_available_datanode_id()
        
        all_matches = [list(map(lambda s: s.strip(), val)) + [i+id_offset] + ["r"]
                       for i, val in enumerate(all_matches)]
        '''
        if all_matches:     # If the list is not empty, i.e. if matches were found
            #print(f"{len(all_matches)} MATCH(ES) found")
            scan_results = "<table border='1' style='border-collapse: collapse'>"
            for match_instance in all_matches:   # Consider each match in turn
                #print("Overall Single Match: " , match_instance) # This would normally be a tuple of capture groups
                                                                 # (which we previously turned to list, with 2 field added)
                scan_results += "<tr>"
                for item in match_instance:
                    scan_results += f"<td>{item}</td>"
                scan_results += "</tr>"

            scan_results += f"</table>"
        else:
            print("NO MATCHES found")
            return f"File `{basename}` uploaded successfully, but <b>NO MATCHES</b> found"


        #column_names = ["name", "role", "location", "uri", "schema_code"]
        column_names = ["method_name", "args", "return_value", "comments", "class_name", "class_description"]
        df = pd.DataFrame(all_matches, columns = column_names)
        print(df.count())
        print(df.head(10))
        print("...")
        print(df.tail(10))

        DocumentationGenerator.generate_documentation(df)


        if test_only:
            return f"File `{basename}` uploaded successfully.  <b>{len(all_matches)} MATCH(ES)</b> found.  Nothing added to database, because in test_only mode.  Scan results:<br><br>{scan_results}<br>"

        '''
        cls.db.load_pandas(df, label="IP")     # Using a temporary label for ease of the next steps
        '''
        """
        # Done manually.  The first uri in the new data is 69, and we want to map it a pos value of 30;
        # 70 will map to 40, and so on:
        MATCH (c:BA {schema_code:"cat", uri:61}),          // <------ This is the Category "Professional Networking"
        (n:IP)
        MERGE (n)-[:BA_in_category {pos:(n.uri - 69)*10+30}]->(c)

        # Rename all "IP" labels to "BA"
        MATCH (n:IP) SET n:BA
        REMOVE n:IP
        """

        return f"File `{basename}` uploaded and scanned successfully.  Scan results:<br><br>{scan_results}"



    @classmethod
    def define_pattern(cls) -> str:
        """
        Define a REGEX pattern for parsing of data files, for use in import_datafile()

        The pattern is expected to be used in a re.findall() that uses re.DOTALL as the last argument

        :return:    A string with a REGEX pattern
        """
        # The R before the string escapes all characters ("raw strings" aka "verbatim strings")

        # THIS PARTICULAR PATTERN IS FOR THE CREATION OF DOCUMENTATION FROM PYTHON FILES

        pattern_1 = R'def\s+([a-zA-Z_][a-zA-Z0-9_]*)' # Match and capture the method name:
        #   "def" followed by 1 or more blanks, followed by
        #   (one letter or underscore, followed by any number of letters, numbers or underscores)

        pattern_2 = R'\((.*?)\)'                    # Match and capture (non-greedy) everything inside round parentheses after method name

        pattern_3 = R'\s*(?:\s*->\s*(.*?)\s*)?:'    # Match and capture (non-greedy) the method's return type - which may or may not be present.
        #   The ?: after the opening parenthesis = grouping WITHOUT capturing
        #   The ? at the end makes the previous expression optional

        pattern_4 = R'(?:\s+"""(.*?)""")?'          # TODO: deal with the comments that might be at the end of the definition line
        # Match and capture (non-greedy) everything within the following pair of """
        #   The ?: after the opening parenthesis = grouping WITHOUT capturing
        #   \s+ = 1 or more blanks.  Note: that required character is the newline

        pattern_A = pattern_1 + pattern_2 + pattern_3 + pattern_4


        pattern_1 = R'class\s+([a-zA-Z][a-zA-Z0-9_]*)\s*:'  # Match and capture the class name

        pattern_2 = R'.+?"""(.*?)"""'               # Match and capture (non-greedy) everything within the following pair of """
        #   The .+? at the beginning = 1 or more characters (non-greedy).  Note: that required character is the newline
        pattern_B = pattern_1 + pattern_2


        pattern = f"(?:{pattern_A})|(?:{pattern_B})"    # Deal with alternations


        '''
        # Test for LinkedIn connections:
        pattern_1 = R"\n([a-zA-Z.'\- ,()]+)@@@\n"   # Full name
        pattern_1 = R"\n(.+)@@@\n"                  # Full name
        pattern_2 = ".+ profile\n"                  # Throwaway line
        pattern_3 = "---1st1st degree connection\n" # Throwaway line
        pattern_4 = "(.+)\n(.+)\n"                  # Role and location (across 2 lines)
        pattern = pattern_1 + pattern_2 + pattern_3 + pattern_4
        '''
        return pattern




    #####################################################################################################

    '''                                        ~   LOGGING   ~                                        '''

    def ________LOGGING________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################

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
