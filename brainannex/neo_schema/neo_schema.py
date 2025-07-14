from typing import Union, List
from neoaccess.cypher_utils import CypherUtils, CypherMatch
from neoaccess import NeoAccess
import json
import math
from datetime import datetime
from neo4j.time import DateTime     # TODO: move to NeoAccess
import pandas as pd
import numpy as np


class NeoSchema:
    """
    Note: major implementation changes introduced in version 5 Release Candidate 2

    A layer above the class NeoAccess (or, in principle, another library providing a compatible interface),
    to provide an optional schema to the underlying database.

    Schemas may be used to either:
        1) acknowledge the existence of typical patterns in the data
        OR
        2) to enforce a mold for the data to conform to

    MOTIVATION

        Relational databases are suffocatingly strict for the real world.
        Neo4j by itself may be too anarchic.
        A schema (whether "lenient/lax/loose" or "strict") in conjunction with Neo4j may be the needed compromise.

    GOALS

        - Data integrity
        - Data filtering upon import
        - Assist the User Interface
        - Self-documentation of the database
        - Graft into graph database some of the semantic functionality that some people turn to RDF for.
            However, carving out a new path rather than attempting to emulate RDF!



    OVERVIEW

        - "Class" nodes capture the abstraction of entities that share similarities.
          Example: "car", "star", "protein", "patient"

          In RDFS lingo, a "Class" node is the counterpart of a resource (entity)
                whose "rdf:type" property has the value "rdfs:Class"

        - The "Property" nodes linked to a given "Class" node, represent the attributes of the data nodes of that class

        - Data nodes are linked to their respective classes by a "SCHEMA" relationship.

        - Some classes contain an attribute named "code" that identifies the UI code to display/edit them [this might change!],
          as well as their descendants under the "INSTANCE_OF" relationships.
          Conceptually, the "code" is a relationship to an entity consisting of software code.

        - Class can be of the "S" (Strict) or "L" (Lenient) type.
            A "lenient" Class will accept data nodes with any properties, whether declared in the Class Schema or not;
            by contrast, a "strict" class will prevent data nodes that contains properties not declared in the Schema

            (TODO: also implement required properties and property data types)


    IMPLEMENTATION DETAILS

        - Every node used by this class, as well as the data nodes it manages,
          contains has a unique attribute "uri" (formerly "schema_id" and "item_id", respectively);
          note that this is actually a "token", i.e. a part of a URI - not a full URI.
          The uri's of schema nodes have the form "schema-n", where n is a unique number.
          Data nodes can have any unique uri's, with optional prefixes and suffixes chosen by the higher layers.
          The Schema layer manages the auto-increments for any desired set of namespaces (and itself makes use
          of the "schema_node" namespace)

        - The names of the Classes and Properties are stored in node attributes called "name".
          We also avoid calling them "label", as done in RDFS, because in Labeled Graph Databases
          like Neo4j, the term "label" has a very specific meaning, and is pervasively used.

        - For convenience, data nodes contain a label equal to their Class name


    AUTHOR:
        Julian West



    ----------------------------------------------------------------------------------
	MIT License

        Copyright (c) 2021-2025 Julian A. West and the BrainAnnex.org project

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

    db = None           # MUST be set before using this class!
                        # Database-interface object is a CLASS variable, accessible as cls.db
                        # For use with the NeoAccess library

    debug = False       # Flag indicating whether a debug mode is to be used by the methods of this class


    #TODO:   - continue the process of making the methods more efficient,
    #          by directly generate Cypher code, rather than using high-level methods in NeoAccess;
    #          for example, as done by create_data_node()



    @classmethod
    def set_database(cls, db :NeoAccess) -> None:
        """
        IMPORTANT: this method MUST be called before using this class!

        :param db:  Database-interface object, created with the NeoAccess library
        :return:    None
        """

        assert type(db) == NeoAccess, \
            "NeoSchema.set_database(): argument passed isn't a valid `NeoAccess` object"

        cls.db = db




    #####################################################################################################

    '''                                     ~   Schema CLASSES   ~                                     '''

    def ________Schema_CLASSES________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################

    @classmethod
    def assert_valid_class_name(cls, class_name: str) -> None:
        """
        Raise an Exception if the passed argument is not a valid Class name

        :param class_name:  A string with the putative name of a Schema Class
        :return:            None
        """
        assert type(class_name) == str, \
            f"NeoSchema.assert_valid_class_name(): " \
            f"The class name ({class_name}) must be a string (instead, it's of type {type(class_name)})"

        assert class_name != "", \
            "NeoSchema.assert_valid_class_name(): Class name cannot be an empty string"

        assert class_name == class_name.strip(), \
            f"NeoSchema.assert_valid_class_name(): Class name (`{class_name}`) cannot contain leading or trailing blanks"


    @classmethod
    def is_valid_class_name(cls, class_name: str) -> bool:
        """
        Return True if the passed argument is a valid Class name, or False otherwise

        :param class_name:  A string with the putative name of a Schema Class
        :return:            None
        """
        if type(class_name) == str and class_name != "":
            return True
        else:
            return False



    @classmethod
    def assert_valid_class_identifier(cls, class_node :Union[int, str]) -> None:
        """
        Raise an Exception is the argument is not a valid "identifier" for a Class node,
        meaning either a valid name or a valid internal database ID

        :param class_node:  Either an integer with the internal database ID of an existing Class node,
                                or a string with its name
        :return:            None (an Exception is raised if the validation fails)
        """
        if type(class_node) == int:
            assert CypherUtils.valid_internal_id(class_node)
        else:
            cls.assert_valid_class_name(class_node)



    @classmethod
    def create_class(cls, name :str, code = None, strict = False, no_datanodes = False) -> (int, str):
        """
        Create a new Class node with the given name and type of schema,
        provided that the name isn't already in use for another Class.

        Return a pair with internal database ID,
        and the auto-incremented uri, assigned to the new Class.
        Raise an Exception if a class by that name already exists.

        NOTE: if you want to add Properties at the same time that you create a new Class,
              use the function create_class_with_properties() instead.

        :param name:        Name to give to the new Class
        :param code:        Optional string indicative of the software handler for this Class and its subclasses
        :param strict:      If True, the Class will be of the "S" (Strict) type;
                                otherwise, it'll be of the "L" (Lenient) type
                            Explained under the comments for the NeoSchema class

        :param no_datanodes If True, it means that this Class does not allow data node to have a "SCHEMA" relationship to it;
                                typically used by Classes having an intermediate role in the context of other Classes

        :return:            An (int, str) pair of integers with the internal database ID and the unique uri
                                assigned to the node just created, if it was created;
                                an Exception is raised if a class by that name already exists
        """
        #TODO: offer the option to link to an existing Class, like create_class_with_properties() does
        #       link_to=None, link_name="INSTANCE_OF", link_dir="OUT"
        #TODO: maybe an option to add multiple Classes of the same type at once???
        #TODO: maybe stop returning the uri ?

        name = name.strip()     # Strip any leading/trailing whitespace at the ends
        assert name != "", \
            "NeoSchema.create_class(): Unacceptable Class name that is empty or blank"

        if cls.class_name_exists(name):
            raise Exception(f"NeoSchema.create_class(): A class named `{name}` ALREADY exists")

        schema_uri = cls._next_available_schema_uri()    # A schema-wide uri, also used for Property nodes

        attributes = {"name": name, "uri": schema_uri, "strict": strict}
        if code:
            attributes["code"] = code
        if no_datanodes:
            attributes["no_datanodes"] = True

        #print(f"create_class(): about to call db.create_node with parameters `CLASS` and `{attributes}`")
        internal_id = cls.db.create_node(labels=["CLASS", "SCHEMA"], properties=attributes)
        return (internal_id, schema_uri)



    @classmethod
    def get_class_internal_id(cls, class_name :str) -> int:
        """
        Returns the internal database ID of the Class node with the given name,
        or raise an Exception if not found, or if more than one is found.
        Note: unique Class names are assumed.

        :param class_name:  The name of the desired class
        :return:            The internal database ID of the specified Class
        """
        cls.assert_valid_class_name(class_name)

        match = cls.db.match(labels="CLASS", key_name="name", key_value=class_name)
        result = cls.db.get_nodes(match, return_internal_id=True)

        assert result, \
            f"NeoSchema.get_class_internal_id(): no Class node named `{class_name}` was found in the Schema"

        assert len(result) <= 1, \
            f"NeoSchema.get_class_internal_id(): more than 1 Class node named `{class_name}` was found in the Schema"

        return result[0]["internal_id"]



    @classmethod
    def get_class_uri(cls, class_name :str) -> str:
        """
        Returns the Schema uri of the Class with the given name;
        raise an Exception if not found

        :param class_name:  The name of the desired class
        :return:            The Schema uri of the specified Class
        """
        #TODO: maybe raise an Exception if more than one is found

        cls.assert_valid_class_name(class_name)

        match = cls.db.match(labels="CLASS", key_name="name", key_value=class_name)
        result = cls.db.get_nodes(match, single_cell="uri")

        if result is None:
            raise Exception(f"No Schema Class named '{class_name}' was found")

        return result



    @classmethod
    def get_class_uri_by_internal_id(cls, internal_class_id: int) -> int:
        """
        Returns the Schema uri of the Class with the given internal database ID.

        :param internal_class_id:
        :return:            The Schema ID of the specified Class; raise an Exception if not found
        """

        result = cls.db.get_nodes(internal_class_id, single_cell="uri")

        if result is None:
            raise Exception(f"NeoSchema.get_class_id_by_neo_id(): no Class with internal id {internal_class_id} found")

        return result



    @classmethod
    def class_neo_id_exists(cls, neo_id: int) -> bool:
        """
        Return True if a Class by the given internal database ID already exists, or False otherwise

        :param neo_id:  Integer with internal database ID
        :return:        A boolean indicating whether the specified Class exists
        """
        cls.db.assert_valid_internal_id(neo_id)

        return cls.db.exists_by_internal_id(neo_id)



    @classmethod
    def class_uri_exists(cls, schema_uri :str) -> bool:
        """
        Return True if a Class by the given uri already exists, or False otherwise

        :param schema_uri:  The uri of the Class node of interest
        :return:            True if the Class already exists, or False otherwise
        """
        assert cls.is_valid_schema_uri(schema_uri), \
            f"NeoSchema.class_uri_exists(): argument `schema_uri` " \
            f"must be a string of the form 'schema-n' for some integer n)"

        return cls.db.exists_by_key(labels="CLASS", key_name="uri", key_value=schema_uri)


    @classmethod
    def class_name_exists(cls, class_name: str) -> bool:
        """
        Return True if a Class by the given name already exists, or False otherwise

        :param class_name:  The name of the class of interest
        :return:            True if the Class already exists, or False otherwise
        """
        cls.assert_valid_class_name(class_name)

        return cls.db.exists_by_key(labels="CLASS", key_name="name", key_value=class_name)



    @classmethod
    def get_class_name_by_schema_uri(cls, schema_uri :str) -> str:
        """
        Returns the name of the class with the given Schema URI;
        raise an Exception if not found

        :param schema_uri:  A string uniquely identifying the desired Class
        :return:            The name of the Class with the given Schema uri
        """
        # TODO: maybe phase out?
        assert cls.is_valid_schema_uri(schema_uri), \
            "get_class_name_by_schema_uri(): The schema uri MUST be a string " \
            "of the form 'schema-n' for some integer n"

        match = cls.db.match(labels="CLASS", key_name="uri", key_value=schema_uri)
        result = cls.db.get_nodes(match, single_cell="name")

        if not result :
            raise Exception(f"No Schema Class with uri '{schema_uri}' found")

        return result



    @classmethod
    def get_class_name(cls, internal_id: int) -> str:
        """
        Returns the name of the class with the given internal database ID,
        or raise an Exception if not found

        :param internal_id: An integer with the internal database ID
                                of the desired class
        :return:            The name of the class with the given Schema ID;
                                raise an Exception if not found
        """
        cls.db.assert_valid_internal_id(internal_id)

        result = cls.db.get_nodes(internal_id, single_cell="name")

        if not result :
            raise Exception(f"NeoSchema.get_class_name_by_neo_id(): no Class with a Neo4j ID of {internal_id} found")

        return result



    @classmethod
    def get_class_attributes(cls, class_internal_id: int) -> dict:
        """
        Returns all the attributes (incl. the name) of the Class node with the given internal database ID,
        or raise an Exception if the Class is not found.
        If no "name" attribute is found, an Exception is raised.

        :param class_internal_id:   An integer with the Neo4j ID of the desired class
        :return:                    A dictionary of attributed of the class with the given Schema ID;
                                        an Exception is raised if not found
                                        EXAMPLE:  {'name': 'MY CLASS', 'uri': '123', 'strict': False}
        """
        #cls.db.assert_valid_internal_id(class_internal_id)

        match = cls.db.match(labels="CLASS", internal_id=class_internal_id)
        result = cls.db.get_nodes(match, single_row=True)

        if result is None :
            raise Exception(f"NeoSchema.get_class_attributes(): no Class with an internal database ID of {class_internal_id} found")

        if "name" not in result:
            raise Exception(f"get_class_attributes(): the expected attribute `name` wasn't found"
                            f" among the attributes of the Class node {class_internal_id}")

        return result



    @classmethod
    def get_all_classes(cls, only_names=True) -> [str]:
        """
        Fetch and return a list of all the existing Schema classes - either just their names (sorted alphabetically)
        (TODO: or a fuller listing - not yet implemented)

        TODO: disregard capitalization in sorting

        :return:    A list of all the existing Class names
        """
        match = cls.db.match(labels="CLASS")
        return cls.db.get_single_field(match=match, field_name="name", order_by="name")



    @classmethod
    def rename_class(cls, old_name :str, new_name :str, rename_data_fields=True) -> None:
        """
        Rename the specified Class.
        If the Class is not found, an Exception is raised

        :param old_name:            The current name (to be changed) of the Class of interest
        :param new_name:            The new name to give to the above Class
        :param rename_data_fields:  If True (default), the corresponding label in the data nodes of that Class
                                        is renamed as well
        :return:                    None
        """
        # TODO: pytest
        # TODO: fix bug causing an early crash if no data point of the old Class is present
        assert old_name != new_name, \
            "rename_class(): The old name and the new name cannot be the same"

        assert new_name != "", \
            "rename_class(): The new name cannot be an empty (blank) string"

        q = f'''
            MATCH (c :CLASS {{ name: $old_name }})
            SET c.name = $new_name
            '''

        data_binding = {"old_name": old_name, "new_name": new_name}
        #cls.db.debug_query_print(q, data_binding)

        result = cls.db.update_query(q, data_binding=data_binding)



        if rename_data_fields:
            q = f'''
                MATCH (dn) 
                WHERE dn._SCHEMA = `{old_name}`
                SET dn._SCHEMA = $new_name, dn:`{new_name}`
                REMOVE dn:`{old_name}`
                '''

        data_binding = {"old_name": old_name, "new_name": new_name}
        #cls.db.debug_query_print(q, data_binding)

        result = cls.db.update_query(q, data_binding=data_binding)
        #print(result)

        '''
        #TODO: revisit
        if not rename_data_fields:
            assert result.get("properties_set") == 1, \
                "rename_class(): Failed to rename the Class (may have failed to find it)"
        else:
            assert result.get("properties_set") >= 1 and (result.get("labels_added") == result.get("labels_removed")), \
                "rename_class(): Failed to rename the Class (may have failed to find it)"
        '''



    @classmethod
    def delete_class(cls, name: str, safe_delete=True) -> None:
        """
        Delete the given Class AND all its attached Properties.
        If safe_delete is True (highly recommended), then delete ONLY if there are no data nodes of that Class
        (i.e., linked to it by way of "SCHEMA" relationships.)

        :param name:        Name of the Class to delete
        :param safe_delete: Flag indicating whether the deletion is to be restricted to
                            situations where no data node would be left "orphaned".
                            CAUTION: if safe_delete is False,
                                     then data nodes may be left without a Schema
        :return:            None.  In case of no node deletion, an Exception is raised
        """
        # TODO: maybe eliminate the dangerous safe_delete=False option!
        # TODO: in case of failure, investigate further the problem
        #       (e.g. no class by that name vs. class has data points still attached to it)
        #       and give a more specific error message

        # Delete classes and property nodes; TODO: also delete "LINK" nodes
        if safe_delete:     # A clause is added in this branch, in the form of a subquery
            q = '''
            MATCH (c :CLASS {name: $name})
            WHERE NOT EXISTS {
                MATCH (dn {`_SCHEMA`: $name})
            }
            WITH c
            OPTIONAL MATCH (c)-[:HAS_PROPERTY]->(p :PROPERTY)         
            DETACH DELETE c, p
            '''

        else:
            q = '''
            MATCH (c :CLASS {name: $name})
            WITH c
            OPTIONAL MATCH (c)-[:HAS_PROPERTY]->(p :PROPERTY)
            DETACH DELETE c, p
            '''
        #print(q)

        result = cls.db.update_query(q, data_binding={"name": name})
        cls.debug_print("result of update query in delete_class(): ", result)
        number_nodes_deleted = result.get("nodes_deleted", 0)   # 0 is given as default value, if not present

        if number_nodes_deleted < 1:     # If no nodes were deleted
            if safe_delete:
                raise Exception(f"Nothing was deleted; potential cause: the specified Class (`{name}`) doesn't exist, or data nodes are attached to it")
            else:
                raise Exception(f"Nothing was deleted; potential cause: the specified Class (`{name}`) doesn't exist")



    @classmethod
    def is_strict_class(cls, name :str) -> bool:
        """
        Return True if the given Class is of "Strict" type,
        or False otherwise (or if the information is missing).
        If no Class by that name exists, an Exception is raised

        :param name:    The name of a Schema Class node
        :return:        True if the Class is "strict" or False if not (i.e., if it's "lax")
        """
        q = '''
            MATCH (c :CLASS {name: $name})
            RETURN c.strict AS strict
            '''
        result = cls.db.query(q, data_binding={"name": name},
                              single_row=True)

        assert result is not None, \
            f"is_strict_class(): no schema Class named `{name}` exists"

        return True if (result.get("strict")) else False



    @classmethod
    def is_strict_class_fast(cls, class_internal_id: int) -> bool:
        """
        Return True if the given Class is of "Strict" type,
        or False otherwise (or if the information is missing)

        :param class_internal_id:   The internal ID of a Schema Class node
        :return:                    True if the Class is "strict" or False if not (i.e., if it's "lax")
        """
        class_attrs = cls.get_class_attributes(class_internal_id)

        return class_attrs.get('strict', False)    # True if a "Strict" Class



    @classmethod
    def allows_data_nodes(cls, class_name = None, class_internal_id = None) -> bool:
        """
        Determine if the given Class allows data nodes directly linked to it

        :param class_name:      Name of the Class
        :param class_internal_id :(OPTIONAL) Alternate way to specify the class; if both specified, this one prevails
        :return:                True if allowed, or False if not
                                    If the Class doesn't exist, raise an Exception
        """
        if class_internal_id is None:    # Note: class_neo_id might legitimately be zero
            class_internal_id = cls.get_class_internal_id(class_name)


        class_node_dict = cls.db.get_nodes(match=class_internal_id, single_row=True)


        if class_node_dict is None:
            raise Exception(f"NeoSchema.allows_data_nodes(): Class named `{class_name}` not found in the Schema")

        if "no_datanodes" in class_node_dict:
            return not class_node_dict["no_datanodes"]

        return True    # If key is not in dictionary, then it defaults to True





    #####################################################################################################

    '''                          ~   RELATIONSHIPS AMONG CLASSES   ~                                   '''

    def ________RELATIONSHIPS_AMONG_CLASSES________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################

    @classmethod
    def assert_valid_relationship_name(cls, rel_name :str) -> None:
        """
        Raise an Exception if the passed argument is not a valid name for a database relationship

        :param rel_name:A string with the relationship (link) name whose validity we want to check
        :return:        None
        """
        assert type(rel_name) == str, \
            f"assert_valid_relationship_name(): the relationship name must be a string " \
            f"(the passed value was of type {type(rel_name)})"

        assert rel_name != "", \
            "assert_valid_relationship_name(): the relationship name cannot be an empty string"



    @classmethod
    def create_class_relationship(cls, from_class: Union[int, str], to_class: Union[int, str],
                                  rel_name="INSTANCE_OF", use_link_node=False, link_properties=None) -> None:
        """
        Create a relationship (provided that it doesn't already exist) with the specified name
        between the 2 existing Class nodes (identified by names or by their internal database IDs),
        in the ( from -> to ) direction.

        Note: multiple relationships by the same name between the same nodes are allowed by Neo4j,
              as long as the relationships differ in their attributes
              (but this method doesn't allow setting properties on the new relationship)

        :param from_class:  Either an integer with the internal database ID of an existing Class node,
                                or a string with its name.
                                Used to identify the node from which the new relationship originates.
        :param to_class:    Either an integer with the internal database ID of an existing Class node,
                                or a string with its name.
                                Used to identify the node to which the new relationship terminates.
        :param rel_name:    Name of the relationship to create, in the from -> to direction
                                (blanks allowed)
        :param use_link_node: If True, insert an intermediate "LINK" node in the newly-created
                                relationship; otherwise, simply create a direct link.
                                Note: if rel_name has the special value "INSTANCE_OF",
                                      this argument must be False
        :param link_properties: [OPTIONAL] List of Property names to attach to the newly-created link.
                                    Note: if link_properties is specified, then use_link_node is automatically True
        :return:            None
        """
        #TODO: maybe rename rel_name to link_name, for consistency
        #TODO: add a method that reports on all existing relationships among Classes?
        #TODO: provide more feedback in case of failure

        # Validate the arguments
        assert (type(rel_name) == str) and (rel_name != ""), \
            "create_class_relationship(): A name (non-empty string) must be provided for the new relationship, " \
            "in the argument `rel_name`"

        if link_properties:
            use_link_node = True

        assert not (rel_name == "INSTANCE_OF" and use_link_node), \
            "create_class_relationship(): if the argument `rel_name` has the special (default) value of 'INSTANCE_OF', " \
            "then the flag `use_link_node` must be False"

        cls.assert_valid_class_identifier(from_class)
        cls.assert_valid_class_identifier(to_class)

        # Prepare the WHERE clause for a Cypher query
        if type(from_class) == int:
            from_clause = "id(from) = $from_class"
        else:
            from_clause = "from.name = $from_class"

        if type(to_class) == int:
            to_clause = "id(to) = $to_class"
        else:
            to_clause = "to.name = $to_class"

        data_binding = {"from_class": from_class, "to_class": to_class}

        q = f'''
            MATCH (from:CLASS), (to:CLASS)
            WHERE {from_clause} AND {to_clause}
            '''

        if use_link_node:
            new_link_uri = cls.reserve_next_uri(namespace="schema_node")     # For the "LINK" node about to get created
            q += f'''MERGE (from)-[:`{rel_name}`]->
                    (l:LINK {{uri: $link_uri}})
                    -[:`{rel_name}`]->(to) \n'''
            data_binding["link_uri"] = new_link_uri
            number_rel_expected = 2

            if link_properties:
                index = 1
                for prop in link_properties:
                    new_property_uri = cls.reserve_next_uri(namespace="schema_node")     # For the "PROPERTY" node about to get created
                    q += f'''
                        MERGE (l)
                        -[:HAS_PROPERTY {{index: {index}}}]->
                        (:PROPERTY {{name: $link_property_{index}, uri: '{new_property_uri}'}}) \n'''
                    data_binding[f"link_property_{index}"] = prop
                    number_rel_expected += 1
                    index += 1

                # EXAMPLE of the additional Cypher created when link_properties = ["p1", "p2"], on link "CONNECTED_TO":
                '''
                    MERGE (from)-[:`CONNECTED_TO`]->(l:LINK {uri: $link_uri})-[:`CONNECTED_TO`]->(to)
                    MERGE (l)-[:HAS_PROPERTY {index: 1}]->(:PROPERTY {name: $link_property_1, uri: 'schema-123'})
                    MERGE (l)-[:HAS_PROPERTY {index: 2}]->(:PROPERTY {name: $link_property_2, uri: 'schema-124'})
                '''
                # The corresponding addition to data_binding dict would be:
                #                   {"link_property_1": "p1", "link_property_2": "p2"}

        else:
            q += f"MERGE (from)-[:`{rel_name}`]->(to)"
            number_rel_expected = 1

        #cls.db.debug_query_print(q, data_binding)

        result = cls.db.update_query(q, data_binding)
        #print("result of update_query in create_class_relationship(): ", result)


        if result.get("relationships_created") != number_rel_expected:
            raise Exception(f"create_class_relationship: failed to create new relationship named `{rel_name}` "
                            f"from Class '{from_class}' to Class '{to_class}'")



    @classmethod
    def rename_class_rel(cls, from_class: int, to_class: int, new_rel_name) -> bool:
        """
        #### TODO: NOT IN CURRENT USE
        Rename the old relationship between the specified classes
        TODO: if more than 1 relationship exists between the given Classes,
              then they will all be replaced??  TO FIX!  (the old name ought be provided)

        :param from_class:
        :param to_class:
        :param new_rel_name:
        :return:            True if another relationship was found, and successfully renamed;
                            otherwise, False
        """
        q = f'''
            MATCH (from :`CLASS` {{ uri: '{from_class}' }})
                  -[rel]
                  ->(to :`CLASS` {{ uri: '{to_class}' }})
            MERGE (from)-[:{new_rel_name}]->(to)
            DELETE rel 
            '''
        # EXAMPLE:
        '''
            MATCH (from :`CLASS` { uri: 'schema-4' })
                  -[rel]
                  ->(to :`CLASS` { uri: 'schema-19' })
            MERGE (from)-[:INSTANCE_OF]->(to)
            DELETE rel
        '''
        #print(q)
        result = cls.db.update_query(q)
        #print("result of rename_class_rel in remove_property_from_class(): ", result)
        if (result.get("relationships_deleted") == 1) and (result.get("relationships_created") == 1):
            return True
        else:
            return False



    @classmethod
    def delete_class_relationship(cls, from_class: str, to_class: str, rel_name) -> int:
        """
        Delete the relationship(s) with the specified name
        between the 2 existing Class nodes (identified by their respective names),
        going in the from -> to direction direction.
        In case of error or if no relationship was found, an Exception is raised

        Note: there might be more than one - relationships with the same name between the same nodes
              are allowed, provided that they have different properties.
              If more than one is found, they will all be deleted.
              The number of relationships deleted will be returned

        :param from_class:  Name of one existing Class node (blanks allowed in name)
        :param to_class:    Name of another existing Class node (blanks allowed in name)
        :param rel_name:    Name of the relationship(s) to delete,
                                if found in the from -> to direction (blanks allowed in name)

        :return:            The number of relationships deleted.
                            In case of error, or if no relationship was found, an Exception is raised
        """
        #TODO: provide more feedback in case of failure
        #TODO: maybe merge with unlink_classes()
        #TODO: test if more than one link is found, they will all be deleted

        assert from_class, "NeoSchema.delete_class_relationship(): A name must be provided for the 'from_class' argument"
        assert to_class, "NeoSchema.delete_class_relationship(): A name must be provided for the 'to_class' argument"
        assert rel_name, "NeoSchema.delete_class_relationship(): A name must be provided for the relationship to delete"

        try:
            # Define the criteria to identify the given Class nodes
            match_from = cls.db.match(labels="CLASS", key_name="name", key_value=from_class, dummy_node_name="from")
            match_to = cls.db.match(labels="CLASS", key_name="name", key_value=to_class, dummy_node_name="to")
            # Remove the specified relationship between them
            number_removed = cls.db.remove_links(match_from=match_from, match_to=match_to, rel_name=rel_name)
        except Exception as ex:
            raise Exception(f"delete_class_relationship(): failed to delete the `{rel_name}` relationship from Schema Class `{from_class}` to Schema Class `{to_class}`. {ex}")

        return number_removed



    @classmethod
    def unlink_classes(cls, class1 :Union[int, str], class2 :Union[int, str]) -> int:
        """
        Remove ALL relationships (in any direction) between the specified Classes

        :param class1:  Either the integer internal database ID, or name, to identify the first Class
        :param class2:  Either the integer internal database ID, or name, to identify the second Class
        :return:        The number of relationships deleted (possibly zero)
        """
        #TODO: maybe merge with delete_class_relationship()
        if type(class1) == int:
            where_clause = "ID(c1) = $class1"
        else:
            where_clause = "c1.name = $class1"

        where_clause += " AND "

        if type(class2) == int:
            where_clause += "ID(c2) = $class2"
        else:
            where_clause += "c2.name = $class2"

        q = f'''
            MATCH (c1 :CLASS) - [r] - (c2 :CLASS) 
            WHERE {where_clause}
            DELETE r
            '''

        # EXAMPLE:
        '''
        MATCH (c1 :CLASS) - [r] - (c2 :CLASS) 
        WHERE "ID(c1) = $class1 AND c2.name = $class2"
        DELETE r
        '''
        #print(q)

        result = cls.db.update_query(q, data_binding={"class1": class1, "class2": class2})
        #print("result of unlink_classes: ", result)
        return result.get("relationships_deleted")



    @classmethod
    def class_relationship_exists(cls, from_class: str, to_class: str, rel_name :str) -> bool:
        """
        Return True if a relationship with the specified name exists between the two given Classes,
        in the specified direction.
        The Schema allows several scenarios:
            - A direct relationship from one Class node to the other
            - A relationship that goes thru an intermediary "LINK" node
            - Either of the 2 above scenarios, but between "ancestors" of the two nodes;
              "ancestors" are defined by means of following
              any number of "INSTANCE_OF" hops to other Class nodes

        SEE ALSO:  is_link_allowed()

        :param from_class:  Name of an existing Class node
        :param to_class:    Name of another existing Class node
        :param rel_name:    Name of the relationship being sought between the above classes
        :return:            True if the Class relationship exists, or False otherwise
        """

        assert (type(rel_name) == str) and (rel_name != ""), \
            "class_relationship_exists(): the argument `rel_name` must be a non-empty string"

        # Note: from_class and to_class get validated in the next 2 function calls
        from_id = cls.get_class_internal_id(from_class)
        to_id = cls.get_class_internal_id(to_class)

        common_query_end = f'''WHERE id(from) = {from_id} AND id(to) = {to_id}
            RETURN COUNT(r) AS number_links
            '''

        # First, try the simplest scenario: direct link between the Classes
        # For efficiency, we'll try to rule out the most common scenarios first,
        # rather than constructing one big query that looks at ll scenarios
        q = f'''
            MATCH (from :CLASS)-[r:`{rel_name}`]->(to :CLASS) 
            {common_query_end}
            '''
        #print(q)
        result = cls.db.query(q, single_cell="number_links")
        if result > 0:
            return True

        # If unsuccessful, see if it's possible to find a link
        # between "ancestors" of the two nodes (thru "INSTANCE_OF" relationships)
        q = f'''
            MATCH (from :CLASS)-[:INSTANCE_OF*0..]->
            (left :CLASS)-[r:`{rel_name}`]->(right :CLASS)
            <-[:INSTANCE_OF*0..]-(to :CLASS) 
            {common_query_end}
            '''
        #print("Attempt 2: ", q)
        result = cls.db.query(q, single_cell="number_links")
        if result > 0:
            return True

        # If still unsuccessful, see if it's possible to find a relationship by means of
        # an intermediary "LINK" node
        q = f'''
            MATCH (from :CLASS)-[r:`{rel_name}`]->(:LINK)-[:`{rel_name}`]->(to :CLASS) 
            {common_query_end}
            '''
        #print("Attempt 3: ", q)
        result = cls.db.query(q, single_cell="number_links")
        if result > 0:
            return True

        # If still unsuccessful, see if it's possible to find a relationship by means of
        # a "LINK" intermediary node, as well as "INSTANCE_OF" ancestors
        q = f'''
            MATCH (from :CLASS)-[:INSTANCE_OF*0..]->
            (left :CLASS)-[r:`{rel_name}`]->(:LINK)-[:`{rel_name}`]->(right :CLASS)
            <-[:INSTANCE_OF*0..]-(to :CLASS) 
            {common_query_end}
            '''
        #print("Attempt 4: ", q)
        result = cls.db.query(q, single_cell="number_links")
        if result > 0:
            return True


        return False    # Connection could not be found under any scenario



    @classmethod
    def get_class_instances(cls, class_name: str, leaf_only=False) -> [str]:
        """
        Get the names of all Classes that are, directly or indirectly, instances of the given Class,
        i.e. pointing to that node thru a series of 1 or more "INSTANCE_OF" relationships;
        if leaf_only is True, then only as long as they are leaf nodes (with no other Class
        that is an instance of them.)

        :param class_name:  Name of the Class for which we want to find
                            other Classes that are an instance of it
        :param leaf_only:   If True, only return the leaf nodes (those that
                            don't have other Classes that are instances of them)
        :return:            A list of Class names
        """
        if leaf_only:
            q = '''
                MATCH (leaf :CLASS)-[:INSTANCE_OF*1..]->(r :CLASS {name: $class_name})
                WHERE not exists( (:CLASS)-[:INSTANCE_OF]->(leaf) )
                RETURN leaf.name AS NAME
                ORDER BY NAME
                '''
        else:
            q = '''
                MATCH (c :CLASS)-[:INSTANCE_OF*1..]->(r :CLASS {name: $class_name})
                RETURN c.name AS NAME
                ORDER BY NAME
                '''

        return cls.db.query(q, data_binding={"class_name": class_name}, single_column="NAME")


    @classmethod
    def is_instance_of(cls, class1 :str, class2 :str) -> bool:
        """
        Return True if class1 is an instance, directly or indirectly, of class2;
        False otherwise.

        :param class1:
        :param class2:
        :return:
        """
        # TODO: perform a more direct Cypher query
        instance_list = cls.get_class_instances(class2)
        return (class1 in instance_list)



    @classmethod
    def get_linked_class_names(cls, class_name :str, rel_name :str, enforce_unique=False) -> Union[str, List[str]]:
        """
        Given a Class, specified by its name, locate and return the name(s) of the other Class(es)
        that it's linked to by means of the relationship with the specified name.
        Typically, the result will contain no more than 1 name, but it could be more;
        it's probably a bad design to use the same relationship name to connect a class to multiple other classes
        (though currently allowed.)
        Relationships are followed in the OUTbound direction only.

        :param class_name:      Name of a Class in the schema
        :param rel_name:        Name of relationship to follow (in the OUTbound direction) from the above Class
        :param enforce_unique:  If True, it raises an Exception if the number of results isn't exactly one

        :return:                If enforce_unique is True, return a string with the class name;
                                otherwise, return a list of names (typically just one)
        """
        q = f'''
            MATCH (from :`CLASS` {{name: $class_name}})
                  -[:{rel_name}]
                  ->(to :`CLASS`)
            RETURN to.name AS related_class_name
        '''
        result = cls.db.query(q, data_binding={"class_name": class_name}, single_column="related_class_name")

        if enforce_unique:
            if len(result) == 0:
                raise Exception(f"This relationship (`{rel_name}`) doesn't connect to other classes in the Schema")
            if len(result) > 1:
                raise Exception(f"This relationship (`{rel_name}`) ambiguously leads to multiple other classes in the Schema: {result}")

            return result[0]    # If we get thus far, there's exactly one element in result


        return result       # This will be a list (though normally with just 1 element)



    @classmethod
    def get_class_relationships(cls, class_name :str, link_dir="BOTH", omit_instance=False) -> Union[dict, list]:
        """
        Fetch and return the names of all the relationships (both inbound and outbound)
        attached to the given Class.
        Treat separately the inbound and the outbound ones.
        If the Class doesn't exist, empty lists are returned.

        :param class_name:      The name of the desired Class
        :param link_dir:        Desired direction(s) of the relationships; one of "BOTH" (default), "IN" or "OUT"
        :param omit_instance:   If True, the common outbound relationship "INSTANCE_OF" is omitted

        :return:                If link_dir is "BOTH", return a dictionary of the form
                                    {"in": list of inbound-relationship names,
                                     "out": list of outbound-relationship names}
                                Otherwise, just return the inbound or outbound list, based on the value of link_dir
        """
        assert link_dir in ["BOTH", "IN", "OUT"], \
                f'get_class_relationships(): the argument `link_dir` must be one of "BOTH", "IN" or "OUT" (value passed was {link_dir})'

        if link_dir == "IN":
            rel_out = []        # We only want the inbound relationships; disregard the outbound ones
        else:
            if omit_instance:
                q_out = '''
                    MATCH (:CLASS {name: $class_name})-[r]->(:CLASS)
                    WHERE type(r) <> "INSTANCE_OF"
                    RETURN type(r) AS rel_name
                    '''
            else:
                q_out = '''
                    MATCH (:CLASS {name: $class_name})-[r]->(:CLASS) 
                    RETURN type(r) AS rel_name
                    '''
            rel_out = cls.db.query(q_out, data_binding={"class_name": class_name}, single_column="rel_name")


        if link_dir == "OUT":
            rel_in = []        # We only want the outbound relationships; disregard the inbound ones
        else:
            q_in = '''
                    MATCH (:CLASS {name: $class_name})<-[r]-(:CLASS) 
                    RETURN type(r) AS rel_name
                    '''
            rel_in = cls.db.query(q_in, data_binding={"class_name": class_name}, single_column="rel_name")

        if link_dir == "BOTH":
            return  {"in": rel_in, "out": rel_out}
        elif link_dir == "IN":
           return rel_in
        else:
            return rel_out



    @classmethod
    def get_class_outbound_data(cls, class_neo_id :int, omit_instance=False) -> dict:
        """
        Efficient all-at-once query to fetch and return the names of all the outbound relationship
        attached to the given Class, as well as the names of the other Classes on the other side of those links.

        IMPORTANT: it's probably a bad design to use the same relationship name to connect a class
        to multiple other classes.  Though currently allowed in the Schema, this particular method
        assumes - and enforces - uniqueness

        :param class_neo_id:    An integer to identify the desired Class
        :param omit_instance:   If True, the common outbound relationship "INSTANCE_OF" is omitted

        :return:                A (possibly empty) dictionary,
                                    where the keys are the name of outbound relationships,
                                    and the values are the names of the Class nodes on the other side of those links.
                                    An Exception will be raised if link names are not unique [though currently allowed by the Schema]
                                    EXAMPLE: {'IS_ATTENDED_BY': 'doctor', 'HAS_RESULT': 'result'}
        """

        if omit_instance:
            q_out = '''
                MATCH (from :CLASS)-[r]->(to :CLASS)
                WHERE id(from) = $class_neo_id AND type(r) <> "INSTANCE_OF"
                RETURN type(r) AS rel_name, to.name AS neighbor
                '''
        else:
            q_out = '''
                MATCH (from :CLASS)-[r]->(to :CLASS)
                WHERE id(from) = $class_neo_id
                RETURN type(r) AS rel_name, to.name AS neighbor
                '''

        results = cls.db.query(q_out, data_binding={"class_neo_id": class_neo_id})
        #print("********** get_class_outbound_data intermediate: ", results)


        outbound_link_map = {}
        for record in results:
            k, val = record['rel_name'], record['neighbor']
            if record['rel_name'] in outbound_link_map:
                raise Exception(f"NeoSchema.get_class_outbound_data: this function doesn't allow "
                                f"multiple outgoing links with same name ({k}) from a Class (neo_id {class_neo_id})")
            else:
                outbound_link_map[k] = val

        #print("********** get_class_outbound_data final: ", outbound_link_map)

        return outbound_link_map




    #####################################################################################################

    '''                                ~   PROPERTIES-RELATED   ~                                     '''

    def ________CLASS_PROPERTIES________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################

    @classmethod
    def get_class_properties(cls, class_node: Union[int, str],
                             include_ancestors=False, sort_by_path_len="ASC", exclude_system=False) -> [str]:
        """
        Return the list of all the names of the Properties associated with the given Class
        (including those inherited thru ancestor nodes by means of "INSTANCE_OF" relationships,
        if include_ancestors is True),
        sorted by the schema-specified position (or, optionally, by path length)

        EXAMPLES:
            get_class_properties(class_node="Quote", include_ancestors=False)
                    => ['quote', 'attribution', 'notes']

            NeoSchema.get_class_properties(class_node="Quote", include_ancestors=True, exclude_system=False)
                    => ['quote', 'attribution', 'notes', 'uri']

            NeoSchema.get_class_properties(class_node="Quote", include_ancestors=True, sort_by_path_len="DESC", exclude_system=False)
                    => ['uri', 'quote', 'attribution', 'notes']

            NeoSchema.get_class_properties(class_node="Quote", include_ancestors=True, exclude_system=True)
                    => ['quote', 'attribution', 'notes']


        :param class_node:          Either an integer with the internal database ID of an existing Class node,
                                        or a string with its name
        :param include_ancestors:   If True, also include the Properties attached to Classes that are ancestral
                                    to the given one by means of a chain of outbound "INSTANCE_OF" relationships
                                    Note: the sorting by relationship index won't mean much if ancestral nodes are included,
                                          with their own indexing of relationships; if order matters in those cases, use the
                                          "sort_by_path_len" argument, below
        :param sort_by_path_len:    Only applicable if include_ancestors is True.
                                        If provided, it must be either "ASC" or "DESC", and it will sort the results by path length
                                        (either ascending or descending), before sorting by the schema-specified position for each Class.
                                        Note: with "ASC", the immediate Properties of the given Class will be listed first
        :param exclude_system:      [OPTIONAL] If True, Property nodes with the attribute "system" set to True will be excluded;
                                        default is False

        :return:                    A list of the Properties of the specified Class
                                        (including indirect Properties, if include_ancestors is True)
        """
        if sort_by_path_len is not None:
            assert (sort_by_path_len == "ASC" or sort_by_path_len == "DESC"), \
                "get_class_properties(): If the argument `sort_by_path_len` is provided, it must be either 'ASC' or 'DESC'"
        else:
            if include_ancestors:
                raise Exception("get_class_properties(): If `include_ancestors` is True, then the argument `sort_by_path_len` must be provided")

        if type(class_node) == str:
            clause = "c.name = $class_node"
        elif type(class_node) == int:
            clause = "id(c) = $class_node"
        else:
            raise Exception(f"get_class_properties(): argument `class_node` must be either a string or an integer ;"
                            f"the value passed was of type {type(class_node)}")

        if exclude_system:
            clause += " AND (p.system IS NULL  OR  p.system = false)"

        if include_ancestors:
            # Follow zero or more outbound "INSTANCE_OF" relationships from the given Class node;
            #   "zero" relationships means the original node itself (handy in situations when there are no such relationships)
            q = f'''
                MATCH path=(c :CLASS)-[:INSTANCE_OF*0..]->(c_ancestor)
                            -[r:HAS_PROPERTY]->(p :PROPERTY)
                WHERE {clause}
                RETURN p.name AS prop_name
                ORDER BY length(path) {sort_by_path_len}, r.index
                '''
        else:
            # NOT including ancestor nodes
            q = f'''
                MATCH (c :CLASS)-[r :HAS_PROPERTY]->(p :PROPERTY)
                WHERE {clause}
                RETURN p.name AS prop_name
                ORDER BY r.index
                '''

        name_list = cls.db.query(q, {"class_node": class_node}, single_column="prop_name")

        return name_list



    @classmethod
    def add_properties_to_class(cls, class_node = None, class_uri = None, property_list = None) -> int:
        """
        Add a list of Properties to the specified (ALREADY-existing) Class.
        The properties are given an inherent order (an attribute named "index", starting at 1),
        based on the order they appear in the list.
        If other Properties already exist, the existing numbering gets extended.

        NOTE: if the Class doesn't already exist, use create_class_with_properties() instead;
              attempting to add properties to an non-existing Class will result in an Exception

        :param class_node:      An integer with the internal database ID of an existing Class node,
                                    or a string with its name
        :param class_uri:       (OPTIONAL) String with the schema_uri of the Class to which attach the given Properties
                                TODO: remove

        :param property_list:   A list of strings with the names of the properties, in the desired order.
                                    Whitespace in any of the names gets stripped out.
                                    If any name is a blank string, an Exception is raised
                                    If the list is empty, an Exception is raised
        :return:                The number of Properties added
        """
        #TODO: rename "property_list" to "properties"; also allow a single string
        #TODO: Offer a way to change the order of the Properties,
        #      maybe by first deleting all Properties and then re-adding them

        assert (class_node is not None) or (class_uri is not None), \
            "add_properties_to_class(): class_internal_id and class_id cannot both be None"

        if class_node is not None and class_uri is None:
            if type(class_node) == int:
                class_uri = cls.get_class_uri_by_internal_id(class_node)
            else:
                class_uri = cls.get_class_uri(class_node)       # class_node is taken to be the Class name

        assert type(class_uri) == str,\
            f"add_properties_to_class(): Argument `class_uri` must be a string; value passed was {class_uri}"
        assert type(property_list) == list, \
            "add_properties_to_class(): Argument `property_list` in add_properties_to_class() must be a list"
        assert cls.class_uri_exists(class_uri), \
            f"add_properties_to_class(): No Class with ID {class_uri} found in the Schema"


        clean_property_list = [prop.strip() for prop in property_list]
        for prop_name in clean_property_list:
            assert prop_name != "", "add_properties_to_class(): Unacceptable Property name, either empty or blank"
            assert type(prop_name) == str, "add_properties_to_class(): Unacceptable non-string Property name"

        # Locate the largest index of the Properties currently present (stored on the "HAS_PROPERTY" links)
        q = '''
            MATCH (:CLASS {uri: $schema_uri})-[r:HAS_PROPERTY]-(:PROPERTY)
            RETURN MAX(r.index) AS MAX_INDEX
            '''
        max_index = cls.db.query(q, {"schema_uri": class_uri}, single_cell="MAX_INDEX")

        # Determine the index value to use for the next Property
        if max_index is None:
            new_index = 1               # Start a new Property count
        else:
            new_index = max_index + 1   # Continue an existing Property count

        number_properties_nodes_created = 0

        for property_name in clean_property_list:
            new_schema_uri = cls._next_available_schema_uri()
            q = f'''
                MATCH (c: `CLASS` {{ uri: '{class_uri}' }})
                MERGE (c)-[:HAS_PROPERTY {{ index: {new_index} }}]
                         ->(p :PROPERTY:SCHEMA {{ uri: '{new_schema_uri}', name: $property_name }})
                '''
            # EXAMPLE:
            '''
            MATCH (c:`CLASS` {uri: 'schema-3'})
            MERGE (c)-[:HAS_PROPERTY {index: 1}]->(p :PROPERTY:SCHEMA {uri: 'schema-8', name: $property_name})
            '''
            #print(q)
            result = cls.db.update_query(q, {"property_name": property_name})
            number_properties_nodes_created += result.get("nodes_created")
            new_index += 1

        return number_properties_nodes_created



    @classmethod
    def set_property_attribute(cls, class_name :str, prop_name :str, attribute_name :str, attribute_value) -> None:
        """
        Set an attribute on an existing "PROPERTY" node of the specified Class

        EXAMPLES:   set_property_attribute(class_name="Content Item", prop_name="uri",
                                           attribute_name="system", attribute_value=True)

                    set_property_attribute(class_name="User", prop_name="admin",
                                           attribute_name="dtype", attribute_value="boolean")
                    set_property_attribute(class_name="User", prop_name="user_id",
                                           attribute_name="dtype", attribute_value="integer")

                    set_property_attribute(class_name="User", prop_name="username",
                                           attribute_name="required", attribute_value=True)

        :param class_name:      The name of an existing CLASS node
        :param prop_name:       The name of an existing PROPERTY node
        :param attribute_name:  The name of an attribute (field) of the PROPERTY node
        :param attribute_value: The value to give to the above attribute (field) of the PROPERTY node;
                                    if a value was already set, it will be over-written
        :return:                None
        """
        #TODO: provide support for some attributes, such as "dtype", "required", "system"
        q = f'''
            MATCH (:CLASS {{name: $class_name}})-[:HAS_PROPERTY]->(p :PROPERTY {{name: $prop_name}})
            SET p.`{attribute_name}`= $attribute_value
            '''
        #print(q)
        result = cls.db.update_query(q,
                            data_binding={"class_name": class_name, "prop_name": prop_name, "attribute_value": attribute_value})
        #print(result)
        assert result.get('properties_set') == 1, \
            f"set_property_attribute() : " \
            f"failed to set the attribute named '{attribute_name}' for Property '{prop_name}' of Class '{class_name}'"



    @classmethod
    def create_class_with_properties(cls, name :str, properties :[str], code=None, strict=False,
                                     class_to_link_to=None, link_name="INSTANCE_OF", link_dir="OUT") -> (int, str):
        """
        Create a new Class node, with the specified name, and also create the specified Properties nodes,
        and link them together with "HAS_PROPERTY" relationships.

        Return the internal database ID and the auto-incremented unique ID ("scheme ID") assigned to the new Class.
        Each Property node is also assigned a unique "schema ID";
        the "HAS_PROPERTY" relationships are assigned an auto-increment index,
        representing the default order of the Properties.

        If a class_to_link_to name is specified, link the newly-created Class node to that existing Class node,
        using an outbound relationship with the specified name.  Typically used to create "INSTANCE_OF"
        relationships from new Classes.

        If a Class with the given name already exists, nothing is done,
        and an Exception is raised.

        NOTE: if the Class already exists, use add_properties_to_class() instead

        :param name:            String with name to assign to the new class
        :param properties:      List of strings with the names of the Properties, in their default order (if that matters)
        :param code:            Optional string indicative of the software handler for this Class and its subclasses.
        :param strict:          If True, the Class will be of the "Strict" type;
                                    otherwise, it'll be of the "Lenient" type

        :param class_to_link_to: If this name is specified, and a link_to_name (below) is also specified,
                                    then create an OUTBOUND relationship from the newly-created Class
                                    to this existing Class
        :param link_name:       Name to use for the above relationship, if requested.  Default is "INSTANCE_OF"
        :param link_dir:        Desired direction(s) of the relationships: either "OUT" (default) or "IN"

        :return:                If successful, the pair (internal database ID, string "schema_uri" assigned to the new Class);
                                otherwise, raise an Exception
        """
        # TODO: possibly deprecate argument "code" in favor of the new (not-yet-used) "handler"
        # TODO: it would be safer to use fewer Cypher transactions; right now, there's the risk of
        #       adding a new Class and then leaving it without properties or links, in case of mid-operation error

        # TODO: merge with create_class()

        # TODO: provide an option to link up to an existing AutoIncrement node of a given namespace
        #       (with a "HAS_URI_GENERATOR" relationship)

        # TODO: maybe add argument 'extra_labels'

        if class_to_link_to:
            assert link_name, \
                "create_class_with_properties(): if the argument `class_to_link_to` is provided, " \
                "a valid value for the argument `link_to_name` must also be provided"

            assert (link_dir == "OUT") or (link_dir == "IN"), \
                f"create_class_with_properties(): if the argument `class_to_link_to` is provided, " \
                f"the argument `link_dir` must be either 'OUT' or 'IN' (value passed: {link_dir})"


        # Create the new Class
        new_class_int_id , new_class_uri = cls.create_class(name, code=code, strict=strict)
        cls.debug_print(f"Created new schema CLASS node (name: `{name}`, Schema ID: '{new_class_uri}')")

        number_properties_added = cls.add_properties_to_class(class_node=new_class_int_id, property_list = properties)
        if number_properties_added != len(properties):
            raise Exception(f"The number of Properties added ({number_properties_added}) does not match the size of the requested list: {properties}")

        cls.debug_print(f"{number_properties_added} Properties added to the new Class: {properties}")


        if class_to_link_to and link_name:
            # Create a relationship between the newly-created Class and an existing Class whose name is given by class_to_link_to
            #other_class_id = cls.get_class_id(class_name = class_to_link_to)
            #cls.debug_print(f"Internal database ID of the `{class_to_link_to}` class to link to: {other_class_id}")
            try:
                if link_dir == "OUT":
                    cls.create_class_relationship(from_class=new_class_int_id, to_class=class_to_link_to, rel_name =link_name)
                else:
                    cls.create_class_relationship(from_class=class_to_link_to, to_class=new_class_int_id, rel_name =link_name)
            except Exception as ex:
                raise Exception(f"New Class ({name}) created successfully, but unable to link it to the `{class_to_link_to}` class. {ex}")

        return new_class_int_id, new_class_uri



    @classmethod
    def remove_property_from_class(cls, class_uri :str, property_uri :str) -> None:
        """
        Take out the specified (single) Property from the given Class.
        If the Class or Property was not found, an Exception is raised

        :param class_uri:   The uri of the Class node
        :param property_uri:The uri of the Property node
        :return:            None
        """
        #TODO: switch from uri's to names
        #TODO: offer the option to remove the property from Data Nodes
        #TODO: if the Class is strict, property from Data Nodes must happen unless explicitly over-ridden

        assert cls.class_uri_exists(class_uri), \
            f"remove_property_from_class(): the schema has no Class with the requested ID of {class_uri}"

        q = f'''
            MATCH (c :CLASS {{ uri: '{class_uri}' }})
                  -[:HAS_PROPERTY]
                  ->(p :PROPERTY {{ uri: '{property_uri}'}})
            DETACH DELETE p
            '''

        result = cls.db.update_query(q)
        #print("result of update_query in remove_property_from_class(): ", result)

        # Validate the results of the query
        assert result.get("nodes_deleted") == 1, f"Failed to find or delete the Property node (with schema_uri {property_uri})"
        assert result.get("relationships_deleted") == 1, "Failed to find or delete the relationship"



    @classmethod
    def rename_property(cls, old_name :str, new_name :str, class_name :str, rename_data_fields=True) -> None:
        """
        Rename the specified (single) Property from the given Class.
        If the Class or Property is not found, an Exception is raised

        :param old_name:            The current name (to be changed) of the Property of interest
        :param new_name:            The new name to give to the above Property
        :param class_name:          The name of the Class node to which the Property is attached
        :param rename_data_fields:  If True (default), the field names in the data nodes of that Class
                                        are renamed as well (NOT YET IMPLEMENTED)
        :return:                    None
        """
         #TODO: implement rename_data_fields.  Pytests

        assert old_name != new_name, \
            "rename_property(): The old name and the new name cannot be the same"

        assert new_name != "", \
            "rename_property(): The new name cannot be an empty (blank) string"

        q = f'''
            MATCH (:CLASS {{ name: $class_name }})
                  -[:HAS_PROPERTY]
                  ->(p :PROPERTY {{ name: $old_property_name}})
            SET p.name = $new_property_name
            '''

        data_binding = {"class_name": class_name, "old_property_name": old_name, "new_property_name": new_name}
        #cls.db.debug_query_print(q, data_binding)
        result = cls.db.update_query(q, data_binding=data_binding)

        assert result.get("properties_set") == 1, \
            "rename_property(): Failed to rename the Property (may have failed to find it)"



    @classmethod
    def is_property_allowed(cls, property_name :str, class_name :str) -> bool:
        """
        Return True if the given Property is allowed by the specified Class,
        or False otherwise.

        For a Property to be allowed, at least one of the following must hold:

            A) the Class isn't strict (i.e. every property is allowed)
        OR
            B) the Property has been registered with the Schema, for that Class
        OR
            C) the Property has been registered with the Schema, for an ancestral Class - reachable
               from our given Class thru a chain of "INSTANCE_OF" relationships

        It's permissible for the specified Class not to exist; in that case, False will be returned
        (TODO: may be better to raise an Exception in such cases!)

        :param property_name:   Name of a Property (i.e. a field name) whose permissibility
                                    we want to check
        :param class_name:      Name of a Class in the Schema
        :return:                True if the given Property is allowed by the specified Class,
                                    or False otherwise
        """
        assert property_name, f"NeoSchema.is_property_allowed(): no name was provided for the property"

        # We use a Conditional Cypher Execution of the line that starts with "MATCH (c)-[:INSTANCE_OF*0..]->" ,
        # i.e. we execute it to look up the Class Properties ONLY if the Class is "strict"
        # (if not strict, then there's no need to do that check; we already have an answer!)
        q = '''
            MATCH (c :CLASS {name: $class_name})

            CALL {           
                WITH c            
                WITH c
            
                WHERE c.strict
                MATCH (c)-[:INSTANCE_OF*0..]->(c_ancestor :CLASS)-[:HAS_PROPERTY]->(p:PROPERTY {name: $property_name})
            
                RETURN count(p) > 0 AS has_property           
            }
            
            RETURN  (NOT c.strict OR has_property) AS allowed
            '''
            # Note that count(p) will evaluate to 0 in case the Cypher "MATCH" immediately above it does not get executed.
            # The repeated "WITH c" is necessary because of a quirk about "WITH" being used in subqueries with a "WHERE" clause;
            # more info: https://neo4j.com/developer/kb/conditional-cypher-execution/

        return cls.db.query(q, data_binding={"property_name": property_name, "class_name": class_name},
                            single_cell="allowed")



    @classmethod
    def is_link_allowed(cls, link_name :str, from_class :str, to_class :str) -> bool:
        """
        Return True if the given Link is allowed between the specified Classes (in the given direction),
        or False otherwise.

        For a Link to be allowed, at least one of the following must hold:

            A) BOTH of the Classes aren't strict (in which case any arbitrary link is allowed!)
        OR
            B) the Link has been registered with the Schema, for those Classes (possibly going thru intermediate "INSTANCE_OF" hops)

        Note: links being allowed is inherited from other Classes
              that are ancestors of the given Class thru "INSTANCE_OF" relationships

        If either of the specified Classes doesn't exist, an Exception is raised

        :param link_name:   Name of a Link (i.e. relationship) whose permissibility
                                we want to check
        :param from_class:  Name of a Class that we want to check whether the given Link can originate from
        :param to_class:    Name of a Class that we want to check whether the given Link can terminate into
        :return:            True if the given Link is allowed by the specified Classes,
                                or False otherwise
        """
        assert link_name, \
            f"NeoSchema.is_link_allowed(): empty name was provided for the argument `link_name`"

        # Check whether both Classes aren't strict
        if not cls.is_strict_class(from_class) and not cls.is_strict_class(to_class):
            return True     # "Letting things slide" because both end Classes are lax


        return cls.class_relationship_exists(from_class=from_class, to_class=to_class, rel_name=link_name)



    @classmethod
    def allowable_props(cls, class_internal_id: int, requested_props: dict, silently_drop: bool) -> dict:
        """
        If any of the properties in the requested list of properties is not a declared (and thus allowed) Schema property,
        then:
            1) if silently_drop is True, drop that property from the returned pared-down list
            2) if silently_drop is False, raise an Exception

        Note: if the Class is not "strict", then anything goes! (and any property can be set)

        :param class_internal_id:   The internal database ID of a Schema Class node
        :param requested_props:     A dictionary of properties one wishes to assign to a new data node,
                                        if the Schema allows them
        :param silently_drop:       If True, any requested properties not allowed by the Schema are simply dropped from the returned list;
                                        otherwise, an Exception is raised if any property isn't allowed

        :return:                    A possibly pared-down version of the requested_props dictionary
        """
        # TODO: possibly expand to handle REQUIRED properties

        if requested_props == {} or requested_props is None:
            return {}     # It's a moot point, if not attempting to set any property

        if not cls.is_strict_class_fast(class_internal_id):
            return requested_props      # Any properties are allowed if the Class isn't strict


        allowed_props = {}
        # Determine the list of Properties registered with the Class, or with any ancestral Class thru INSTANCE_OF relationships
        class_properties = cls.get_class_properties(class_node=class_internal_id, include_ancestors=True)

        for requested_prop in requested_props.keys():
            # Check each of the requested properties
            if requested_prop in class_properties:
                allowed_props[requested_prop] = requested_props[requested_prop]     # Allowed
            else:
                # Not allowed
                if not silently_drop:
                    raise Exception(f"NeoSchema.allowable_props(): "
                                    f"the requested property `{requested_prop}` is not among the registered Properties "
                                    f"of the Class `{cls.get_class_name(class_internal_id)}`")

        return allowed_props




    #####################################################################################################

    '''                          ~   SCHEMA-CODE  RELATED   ~                                   '''

    def ________SCHEMA_CODE________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################

    @classmethod
    def get_schema_code(cls, class_name: str) -> str:
        """
        Obtain the "schema code" of a Class, specified by its name.
        The "schema code" is an optional but convenient text code,
        stored either on a Class node, or on any of its ancestors by way of "INSTANCE_OF" relationships

        :return:    A string with the Schema code (empty string if not found)
                    EXAMPLE: "i"
        """
        # TODO: obsolete - still being used during the transition period
        q = '''
        MATCH (c:CLASS {name: $_CLASS_NAME})-[:INSTANCE_OF*0..]->(ancestor:CLASS)
        WHERE ancestor.code IS NOT NULL 
        RETURN ancestor.code AS code
        '''
        # Search 0 or more hops from the given Class node

        result = cls.db.query(q, {"_CLASS_NAME": class_name})   # TODO: use the single_cell argument of query()
        if result == []:
            return ""       # not found

        return result[0]["code"]



    @classmethod
    def get_schema_uri(cls, schema_code :str) -> str:
        """
        Get the Schema URI most directly associated to the given Schema Code

        :return:    A string with the Schema uri (or "" if not present)
        """
        #TODO: obsolete

        match = cls.db.match(labels="CLASS", key_name="code", key_value=schema_code)
        result = cls.db.get_nodes(match, single_cell="uri")

        if result is None:
            return ""

        return result





    #####################################################################################################

    '''                         ~   DATA NODES : READING  ~                                           '''

    def ________DATA_NODES_READING_______(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################


    @classmethod
    def all_properties(cls, label :str, primary_key_name :str, primary_key_value) -> [str]:
        """
        Return the list of the *names* of all the Properties associated with the specified DATA node,
        based on the Schema it is associated with, sorted their by position stored in the Schema.
        The desired node is identified by specifying which one of its attributes is a primary key,
        and providing a value for it.

        IMPORTANT : this function returns the NAMES of the Properties; not their values

        :param label:               Required label on the node to look up
        :param primary_key_name:    A field name used to identify our desired Data Node
        :param primary_key_value:   The corresponding field value to identify our desired Data Node
        :return:                    A list of the names of the Properties associated
                                        with the given DATA node
        """
        q = f'''
            MATCH  (d :`{label}` {{ {primary_key_name}: $primary_key_value}})
            WITH dn.`_SCHEMA` AS schema_name
            MATCH (c :`CLASS` {{name: schema_name}})
                  -[r :HAS_PROPERTY]->(p :`PROPERTY`)        
            RETURN p.name AS prop_name
            ORDER BY r.index
            '''

        # EXAMPLE:
        '''
        MATCH (dn: `my data label` {uri: $primary_key_value})
        WITH dn._SCHEMA AS schema_name
        MATCH (c :`CLASS` {name: schema_name})
              -[r :HAS_PROPERTY]->(p :`PROPERTY`)
        RETURN p.name AS prop_name
        ORDER BY r.index
        '''

        result_list = cls.db.query(q, {"primary_key_value": primary_key_value})

        name_list = [item["prop_name"] for item in result_list]

        return name_list



    @classmethod
    def get_data_node_internal_id(cls, uri :str, label=None) -> int:
        """
        Returns the internal database ID of the given Data Node,
        specified by the value of its uri attribute
        (and optionally by a label)

        :param uri:     A string to identify a Data Node by the value of its "uri" attribute
        :param label:   (OPTIONAL) String to require the Data Node to have (redundant,
                            since "uri" already uniquely specifies a Data Node - but
                            could be used for speed or data integrity)

        :return:        The internal database ID of the specified Data Node;
                            if none (or more than one) found, an Exception is raised
        """
        #TODO: merge with get_data_node_id()

        match = cls.db.match(key_name="uri", key_value=uri, labels=label)
        result = cls.db.get_nodes(match, return_internal_id=True)

        if label:
            assert result, f"NeoSchema.get_data_node_internal_id(): " \
                           f"no Data Node with the given uri ('{uri}') and label ('{label}') was found"
        else:
            assert result, f"NeoSchema.get_data_node_internal_id(): " \
                           f"no Data Node with the given uri ('{uri}') was found"

        if len(result) > 1:
            raise Exception(f"NeoSchema.get_data_node_internal_id(): more than 1 Data Node "
                            f"with the given uri ('{uri}') was found ({len(result)} were found)")

        return result[0]["internal_id"]



    @classmethod
    def get_data_node_id(cls, key_value :str, key_name="uri") -> int:
        """
        Get the internal database ID of a Data Node, given some other primary key

        :param key_value:   The name of a primary key to use for the node lookup
        :param key_name:    The value of the above primary key
        :return:            The internal database ID of the specified Data Node
        """
        #TODO: merge with get_data_node_internal_id()

        match = cls.db.match(key_name=key_name, key_value=key_value)
        result = cls.db.get_nodes(match, return_internal_id=True, single_cell="internal_id")

        assert result is not None, \
            f"get_data_node_id(): unable to find a data node with the attribute `{key_name}={key_value}`"

        return result



    @classmethod
    def data_node_exists(cls, node_id: Union[int, str], id_key=None, class_name=None) -> bool:
        """
        Return True if the specified Data Node exists, or False otherwise.

        :param node_id:     Either an internal database ID or a primary key value
        :param id_key:      [OPTIONAL] Name of a primary key used to identify the data node; for example, "uri".
                                Leave blank to use the internal database ID
        :param class_name:  [OPTIONAL] Used for a stricter check
        :return:            True if the specified Data Node exists, or False otherwise
        """
        #TODO: pytest

        # Prepare the clause part of a Cypher query
        if id_key is None:
            clause = "WHERE id(dn) = $node_id"
        elif type(node_id) == str:
            clause = f"WHERE dn.`{id_key}` = $node_id"
        else:
            raise Exception(f"data_node_exists(): "
                            f"argument `node_id` must be None or a string; "
                            f"instead, it is {type(node_id)}")

        if class_name:
            schema_clause = "AND dn.`_SCHEMA` = $class_name"
        else:
            schema_clause = ""



        # Prepare a Cypher query to locate the number of the data nodes
        q = f'''
            MATCH (dn) 
            {clause} {schema_clause}
            RETURN COUNT(dn) AS number_found
            '''

        #cls.db.debug_query_print(q, {"node_id" : node_id, "class_name": class_name})
        number_found = cls.db.query(q, {"node_id" : node_id, "class_name": class_name},
                                    single_cell="number_found")

        if number_found == 0:
            return False
        elif number_found == 1:
            return True
        else:
            raise Exception(f"data_node_exists(): more than 1 node was found "
                            f"with the same URI ({node_id}), which ought to be unique")



    @classmethod
    def data_link_exists(cls, node1_id, node2_id, link_name :str, id_key=None) -> bool:
        """
        Return True if the specified link exists, in the direction from the Data Node node_1 to node_2,
        or False otherwise.
        Note that more than 1 link by the same name may exist between any two given nodes, if
        the links have different properties; as long as at least 1 link exists, True is returned

        :param node1_id:    A unique value to identify the 1st data node:
                                either an internal database ID or a primary key value
        :param node2_id:    A unique value to identify the 1st data node:
                                either an internal database ID or a primary key value
        :param link_name:   The name of the link (relationship) to look for
        :param id_key:      [OPTIONAL] Name of a primary key used to identify the data nodes; for example, "uri".
                                Leave blank to use the internal database ID

        :return:            True if the specified Data Node link, or False otherwise
        """
        # TODO: also allow to optionally pass Class names for double-check (and for efficiency of search)
        # TODO: maybe make a version of this function for NeoAccess

        # Prepare the clause part of a Cypher query
        if id_key is None:
            clause = "WHERE id(dn1) = $data_node_1 AND id(dn2) = $data_node_2"
        else:
            clause = f"WHERE dn1.{id_key} = $data_node_1 AND dn2.{id_key} = $data_node_2"


        # Prepare a Cypher query to locate the link count
        q = f'''
            MATCH (dn1) -[r :`{link_name}`]-> (dn2)
            {clause} 
            RETURN COUNT(r) AS number_found
            '''
        data_dict = {"data_node_1": node1_id, "data_node_2": node2_id}
        #cls.db.debug_query_print(q, data_dict)

        number_found = cls.db.query(q, data_dict, single_cell="number_found")

        if number_found == 0:
            return False
        else:   # 1 link, or possibly more, found
            return True



    @classmethod
    def get_data_link_properties(cls, node1_id, node2_id, link_name :str, id_key=None, include_internal_id=False) -> [dict]:
        """
        Return all the properties of the link(s), of the specified name, between the two given Data nodes.

        Note that more than 1 link by the same name may exist between any two given nodes, if
        the links have different properties; as long as at least 1 link exists, True is returned

        :param node1_id:   A unique value to identify the 1st data node:
                                either an internal database ID or a primary key value
        :param node2_id:   A unique value to identify the 1st data node:
                                either an internal database ID or a primary key value
        :param link_name:   The name of the link (relationship) to look for
        :param id_key:      [OPTIONAL] Name of a primary key used to identify the data nodes; for example, "uri".
                                Leave blank to use the internal database ID
        :param include_internal_id: [OPTIONAL] If True, then the internal database ID of the relationships is also
                                        included in the dict's, using the key "internal_id"

        :return:            A list of dict, with key/values for the properties of each link.
                                If include_internal_id is True, an extra key named "internal_id" will be present.
                                EXAMPLE, with include_internal_id = False:
                                    [{'Rank': 99}, {'Rank': 123}, {}]     (Two links with properties, and one without)
        """
        # TODO: also allow to optionally pass Class names for double-check (and for efficiency of search)
        # TODO: maybe make a version of this function for NeoAccess
        # TODO: pytest

        # Prepare the clause part of a Cypher query
        if id_key is None:
            clause = "WHERE id(dn1) = $data_node_1 AND id(dn2) = $data_node_2"
        else:
            clause = f"WHERE dn1.{id_key} = $data_node_1 AND dn2.{id_key} = $data_node_2"


        data_dict = {"data_node_1": node1_id, "data_node_2": node2_id}

        # Prepare a Cypher query to locate the link count
        if include_internal_id:
            q = f'''
                MATCH (dn1) -[r :`{link_name}`]-> (dn2)
                {clause} 
                RETURN r
                '''
            result = cls.db.query_extended(q, data_dict, flatten=True,
                fields_to_exclude=['neo4j_start_node', 'neo4j_end_node', 'neo4j_type'])
        else:
            q = f'''
                MATCH (dn1) -[r :`{link_name}`]-> (dn2)
                {clause} 
                RETURN properties(r) AS props
                '''

            result = cls.db.query(q, data_dict, single_column="props")

        #cls.db.debug_query_print(q, data_dict)

        return result



    @classmethod
    def get_data_node(cls, class_name :str, node_id, id_key=None, hide_schema=True) -> Union[dict, None]:
        """
        Return a dictionary with all the key/value pairs of the attributes of given Data Node,
        specified by its Class name, and a unique identifier

        :param class_name:  The name of the Schema Class that this Data Node is associated to
        :param node_id:     Either an internal database ID or a primary key value
        :param id_key:      [OPTIONAL] Name of a primary key used to identify the data node; for example, "uri".
                                Leave blank to use the internal database ID
        :param hide_schema: [OPTIONAL] By default (True), the special schema field `_SCHEMA` is omitted
        :return:            If not found, return None;
                                otherwise, return a dict with the name/values of the node's properties
        """
        if id_key is None:
            where_clause = "WHERE (id(dn) = $node_id)"
        else:
            where_clause = f"WHERE (dn.`{id_key}` = $node_id)"

        q = f'''
            MATCH (dn)
            {where_clause} AND (dn.`_SCHEMA` = $class_name)
            RETURN dn
            '''

        data_binding = {"class_name": class_name, "node_id": node_id}

        #cls.db.debug_query_print(q, data_binding, "class_of_data_node")

        result = cls.db.query(q, data_binding, single_row=True)

        if result is None:
            return None

        assert len(result) == 1, \
            f"get_data_node(): the specified key ({id_key}) is not unique - multiple records were located"

        d = result["dn"]    # EXAMPLE:  {'_SCHEMA': 'Car', 'color': 'white', 'make': 'Toyota'}

        if hide_schema:
            del d["_SCHEMA"]

        return d



    @classmethod
    def search_data_node(cls, uri = None, internal_id = None, hide_schema=True) -> Union[dict, None]:
        """
        Return a dictionary with all the key/value pairs of the attributes of given (single) data node

        See also get_data_node() and locate_node()

        :param uri:         The `uri` field value to uniquely identify the data node
        :param internal_id: Alternate way to specify the data node;
                                cannot specify both `uri` and `internal_id` arguments

        :param hide_schema: [OPTIONAL] By default (True),
                                the special schema field `_SCHEMA` is omitted from the results

        :return:            A dictionary with all the key/value pairs, if node is found; or None if not
        """
        # TODO: merge with get_data_node() and perhaps also with locate_node()
        # TODO: add function that only returns a specified single Property, or specified list of Properties
        # TODO: optionally also return node label

        if uri is not None:
            assert internal_id is None, \
                "NeoSchema.search_data_node(): arguments `uri` and `internal_id` cannot both be specified"

            match = cls.db.match(key_name="uri", key_value=uri)
        else:   # uri is None
            assert internal_id is not None, \
                "NeoSchema.search_data_node(): one of arguments `uri` and `internal_id` must be specified"

            match = cls.db.match(internal_id=internal_id)


        d = cls.db.get_nodes(match, single_row=True)    # EXAMPLE:  {'_SCHEMA': 'Car', 'color': 'white', 'make': 'Toyota'}

        if d is None:               # No matching node found
            return  None

        if "_SCHEMA" not in d:      # If not a Data Node
            return None

        if hide_schema:
            del d["_SCHEMA"]

        return d



    @classmethod
    def locate_node(cls, node_id: Union[int, str], id_type=None, labels=None, dummy_node_name="n") -> CypherMatch:
        """
        EXPERIMENTAL - a generalization of get_data_node()

        Return the "match" structure to later use to locate a node identified
        either by its internal database ID (default), or by a primary key (with optional label.)

        NOTE: No database operation is actually performed.

        :param node_id: This is understood be the Neo4j ID, unless an id_type is specified
        :param id_type: For example, "uri";
                            if not specified, the node ID is assumed to be Neo4j ID's
        :param labels:  (OPTIONAL) Labels - a string or list/tuple of strings - for the node
        :param dummy_node_name: (OPTIONAL) A string with a name by which to refer to the node (by default, "n")

        :return:        A "CypherMatch" object
        """
        if id_type:
            match_structure = cls.db.match(key_name=id_type, key_value=node_id, labels=labels)
        else:
            match_structure = cls.db.match(internal_id=node_id)

        return CypherUtils.process_match_structure(match_structure, dummy_node_name=dummy_node_name)



    @classmethod
    def class_of_data_node(cls, node_id, id_key=None, labels=None) -> str:
        """
        Return the name of the Class of the given data node: identified
        either by its internal database ID (default), or by a primary key (such as "uri")

        :param node_id:     Either an internal database ID or a primary key value
        :param id_key:      OPTIONAL - name of a primary key used to identify the data node; for example, "uri".
                                Leave blank to use the internal database ID
        :param labels:      Optional string, or list/tuple of strings, with internal database labels

        :return:            A string with the name of the Class of the given Data Node, if found;
                                if not found, an Exception is raised
        """
        match = cls.locate_node(node_id=node_id, id_type=id_key, labels=labels)
        # This is an object of type "CypherMatch"

        node = match.node
        where_clause = CypherUtils.prepare_where([match.where])
        data_binding = match.data_binding
        dummy_node_name = match.dummy_node_name

        q = f'''
            MATCH  {node}
            {where_clause}
            RETURN {dummy_node_name}.`_SCHEMA` AS class_name
            '''
        #cls.db.debug_query_print(q, data_binding, "class_of_data_node")

        result = cls.db.query(q, data_binding)
        #print(result)

        if len(result) == 0:    # TODO: separate the 2 scenarios leading to this
            if id_key:
                raise Exception(f"class_of_data_node(): The requested data node ({id_key}: `{node_id}`) "
                                f"does not exist")
            else:
                raise Exception(f"The requested data node (internal database id: {node_id}) "
                                f"does not exist")

        # Note: if the `_SCHEMA` field was missing, result = [{'class_name': None}]
        class_name = result[0].get("class_name")

        assert class_name is not None, \
            "class_of_data_node(): The given data node ({id_key}: `{node_id}`) lacks a `_SCHEMA` field"

        assert type(class_name) == str, \
            f"class_of_data_node(): The given data node ({id_key}: `{node_id}`) has a `_SCHEMA` value ({class_name}) that isn't valid, " \
            f"of type {type(class_name)} rather than a string"

        return class_name



    @classmethod
    def get_all_data_nodes_of_class(cls, class_name :str, hide_schema=True) -> [dict]:
        """
        Return all the values stored at all the Data Nodes of the specified Class.
        Each values comprises all the node fields, the internal database ID and the node labels.

        EXAMPLE: [{'year': 2023, 'make': 'Ford', 'internal_id': 123, 'neo4j_labels': ['Motor Vehicle']},
                  {'year': 2013, 'make': 'Toyota', 'internal_id': 4, 'neo4j_labels': ['Motor Vehicle']}
                 ]

        See also: data_nodes_of_class()

        :param class_name:  The name of a Class in the Schema
        :param hide_schema: [OPTIONAL] By default (True),
                                the special schema field `_SCHEMA` is omitted from the results
        :return:            A (possibly-empty) list of dicts; each list item contains data from a node
        """
        #TODO: add new arguments `clause` (eg, "dn.root <> true OR dn.root is NULL"),
        #      `fields` and `order_by` (eg "toLower(dn.name)")
        cls.assert_valid_class_name(class_name)

        q = '''
            MATCH (dn {_SCHEMA: $class_name})
            RETURN dn
            '''
        node_list = cls.db.query_extended(q, data_binding={"class_name": class_name}, flatten=True)

        if not hide_schema:
            return node_list

        filtered_list = [{k: v for k, v in d.items() if k != '_SCHEMA'} for d in node_list]
        return filtered_list



    @classmethod
    def data_nodes_of_class(cls, class_name :str, return_option="uri") -> Union[List[str], List[int]]:
        """
        Return the uri's, or alternatively the internal database ID's,
        of all the Data Nodes of the given schema Class.

        See also: get_all_data_nodes_of_class()

        :param class_name:      Name of a Schema Class
        :param return_option:   Either "uri" or "internal_id"
        :return:                Return the uri's or internal database ID's
                                        of all the Data Nodes of the given Class
        """
        # TODO: offer the option of returning some or all of the fields
        # TODO: offer to optionally pass a label?
        # TODO: pytest the 'return_option' argument
        # TODO: offer options to select only some nodes

        assert return_option in ["uri", "internal_id"], \
            "data_nodes_of_class(): the argument `return_option` must be either 'uri' or 'internal_id'"

        q = '''
            MATCH (n {_SCHEMA: $class_name}) 
            '''

        if return_option == "uri":
            q += "RETURN n.uri AS uri"
        else:
            q += "RETURN id(n) AS internal_id"


        res = cls.db.query(q, {"class_name": class_name}, single_column=return_option)

        # Alternate approach
        #match = cls.db.match(labels="CLASS", properties={"name": class_name})
        #cls.db.follow_links(match, rel_name="SCHEMA", rel_dir="IN", neighbor_labels="BA")

        return res



    @classmethod
    def count_data_nodes_of_class(cls, class_name: str) -> [int]:
        """
        Return the count of all the Data Nodes attached to the given Class.
        If the Class doesn't exist, an Exception is raised

        :param class_name:  The name of the Schema Class of interest
        :return:            The count of all the Data Nodes attached to the given Class
        """
        assert cls.class_name_exists(class_name), \
            f"count_data_nodes_of_class(): there is no Class named `{class_name}`"

        q = '''
            MATCH (dn {_SCHEMA: $class_name})
            RETURN count(dn) AS number_datanodes
            '''
        #print(q)
        res = cls.db.query(q, data_binding={"class_name": class_name},
                           single_cell="number_datanodes")

        return res



    @classmethod
    def data_nodes_lacking_schema(cls, label :str) -> [int]:
        """
        Locate and return all nodes with the given label
        that aren't associated to any Schema Class

        :label:     A string with a graph-database label
        :return:    A (possibly empty) list of internal database id's of the located nodes
        """
        #  TODO: test

        q = f'''
            MATCH  (n :`{label}`)
            WHERE  n._SCHEMA IS NULL
            RETURN id(n)
            '''

        return cls.db.query(q)



    @classmethod
    def follow_links(cls, class_name :str, node_id, link_name :str, id_key=None, properties=None, labels=None) -> List:
        """
        From the given starting node, follow all the relationships that have the specified name,
        from/into neighbor nodes (optionally having the given labels),
        and return some of the properties of those found nodes.

        :param class_name:  String with the name of the Class of the given data node
        :param node_id:     Either an internal database ID or a primary key value
        :param link_name:   A string with the name of the link(s) to follow
        :param id_key:      [OPTIONAL] Name of a primary key used to identify the data node; for example, "uri";
                                use None to refer to the internal database ID
        :param properties:  [OPTIONAL] String, or list/tuple of strings, with the name(s)
                                of the properties to return on the found nodes;
                                if not specified, ALL properties are returned
        :param labels:      [OPTIONAL] string, or list/tuple of strings,
                                with node labels required to be present on the neighbor nodes
                                TODO: not currently in use

        :return:            A (possibly empty) list of values, if properties only contains a single element;
                                otherwise, a list of dictionaries
        """
        #TODO: pytest
        #TODO: allow an option to return the internal database ID's
        '''
        TODO - idea to expand `links`:
        
                    EXAMPLE: [("occurs", "OUT", "Indexer"),
                              ("has_index", "IN", None)]
                              
                    Each triplet is: (relationship name,
                                      direction,
                                      name of Class of data node on other side)
                    Any component could be None
        '''
        if properties:
            assert (type(properties) == str or type(properties) == list), \
                "follow_links(): the argument `properties` must be a string or list of strings"

        if id_key:
            where_clause = f"from.`{id_key}` = $node_id"
        else:
            where_clause = "id(from) = $node_id"

        if properties is None:
            properties_cypher_str = "to"    # None is interpreted as "ALL properties"
        elif type(properties) == str:
            properties_cypher_str = f"to.`{properties}` AS `{properties}`"
        elif (type(properties) == list or type(properties) == tuple):
            properties_cypher_list = [f"to.`{prop}` AS `{prop}`"
                                      for prop in properties]
            properties_cypher_str = ", ".join(properties_cypher_list)
        else:
            raise Exception(f"follow_links(): the argument `properties` must be a string, or list of strings, or None; "
                            f"the value given was of type: {type(properties)}")

        q = f'''
            MATCH (from :`{class_name}`) -[:`{link_name}`]-> (to)
            WHERE {where_clause}
            RETURN {properties_cypher_str}
            '''
        #cls.db.debug_query_print(q, data_binding={"node_id": node_id}, method="follow_links")
        result = cls.db.query(q, data_binding={"node_id": node_id})


        if (type(properties) == list or type(properties) == tuple):
            return result           # List of dicts

        data = []
        for node in result:
            if properties is None:
                data.append(node["to"])     # The Cypher query is returning whole nodes
            else:
                data.append(node[properties])

        return data                 # List of values



    @classmethod
    def remove_schema_info(cls, dataset :[dict]) -> None:
        """
        Given a "databaset", i.e. a list of dictionaries with key/value from node properties,
        remove-in-place (scrub out) any Schema-related info that higher layers may not want to see

        :param dataset:
        :return:        None
        """
        # Ditch Schema-related attributes in each dict in the list
        for item in dataset:
            if "_SCHEMA" in item:
                del item["_SCHEMA"]





    #####################################################################################################

    '''                     ~   DATA NODES : CREATING / MODIFYING  ~                                  '''

    def ________DATA_NODES_CREATE_MODIFY______(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################


    @classmethod
    def create_data_node(cls, class_node :Union[int, str], properties = None, extra_labels = None,
                         new_uri=None, silently_drop=False, links = None) -> int:
        """
        Create a new data node, of the specified Class,
        with the given (possibly None) properties, and optional extra label(s),
        optionally linked to other, already existing, DATA nodes.

        The name of the Class is always used as a label, and additional labels may be specified.
        If the specified Class doesn't exist, or doesn't allow for Data Nodes, an Exception is raised.

        Optionally, link up the new data node to other existing data nodes; this is an atomic operation that will
            fail (with no data node created) if the other nodes aren't found.

        CAUTION: no check is made whether another data node with identical fields already exists;
                 if that should be prevented, use add_data_node_merge() instead,
                 or utilize unique indices in the database

        URI optional field: The new data node, if successfully created, will optionally be assigned an additional field named `uri`
            with the value passed by `new_uri`.
            The responsibility for picking a URI belongs to the calling function,
            which will typically make use of a namespace, and make use of reserve_next_uri()

        ALTERNATIVES:
            - If creating multiple data nodes at once, consider using import_pandas_nodes()

        EXAMPLE:
            create_data_node(class_name="Cars",
                             properties={"make": "Toyota", "color": "white"},
                             links=[{"internal_id": 123, "rel_name": "OWNED_BY", "rel_dir": "IN"}])
                                    {"internal_id": 789, "rel_name": "OWNS", "rel_attrs": {"since": 2022}}
                            )

        :param class_node:  Either the internal database ID of an existing Class node,
                                or its name
        :param properties:  [OPTIONAL] Dictionary with the properties of the new data node.  Possibly empty, or None.
                                EXAMPLE: {"make": "Toyota", "color": "white"}
        :param extra_labels:[OPTIONAL] String, or list/tuple of strings, with label(s) to assign to the new data node,
                                IN ADDITION TO the Class name (which is always used as label)
        :param new_uri:     [OPTIONAL]  If a string is passed as `new_uri`, then a field (node property) called "uri"
                                is set to that value
        :param silently_drop: If True, any requested properties not allowed by the Schema are simply dropped;
                                otherwise, an Exception is raised if any property isn't allowed
                                Note: only applicable for "Strict" schema - otherwise, anything goes!
        :param links:       OPTIONAL list of dicts identifying existing nodes,
                                and specifying the name, direction and optional properties
                                to give to the links connecting to them;
                                use None, or an empty list, to indicate if there aren't any
                                Each dict contains the following keys:
                                    "internal_id"   REQUIRED - to identify an existing node
                                    "rel_name"      REQUIRED - the name to give to the link
                                    "rel_dir"       OPTIONAL (default "OUT") - either "IN" or "OUT" from the new node
                                    "rel_attrs"     OPTIONAL - A dictionary of relationship attributes

        :return:            The internal database ID of the new data node just created;
                                if unable to create it, an Exception is raised
        """
        # TODO: verify that required attributes are present
        # TODO: verify that all the requested links conform to the Schema
        # TODO: consider allowing creation of multiple nodes from one call
        # TODO: allow a new URI to be automatically generated from a namespace?
        # TODO: invoke special plugin-code, if applicable???

        # Validate arguments
        cls.assert_valid_class_identifier(class_node)

        assert (extra_labels is None) or isinstance(extra_labels, (str, list, tuple)), \
            "NeoSchema.create_data_node(): argument `extra_labels`, " \
            "if passed, must be a string, or list/tuple of strings"

        if properties is not None:
            assert type(properties) == dict, \
                "NeoSchema.create_data_node(): The `properties` argument, if provided, MUST be a dictionary"

        assert links is None or type(links) == list, \
            f"NeoAccess.create_data_node(): The argument `links` must be a list or None; instead, it's of type {type(links)}"


        # Obtain both the Class name and its internal database ID
        if type(class_node) == str:         # TODO: this makes an assumption about the database internal IDs
            class_name = class_node
            class_internal_id = cls.get_class_internal_id(class_node)
        else:
            class_name = cls.get_class_name(class_node)
            class_internal_id = class_node


        # Make sure that the specified Class accepts Data Nodes
        assert cls.allows_data_nodes(class_internal_id=class_internal_id),\
            f"NeoSchema.create_data_node(): addition of data nodes to Class `{class_name}` is not allowed by the Schema"


        # Verify whether all the requested properties are allowed, and possibly trim them down
        properties_to_set = cls.allowable_props(class_internal_id=class_internal_id, requested_props=properties,
                                                silently_drop=silently_drop)


        # Prepare the list of labels to use on the new Data Node
        labels = cls._prepare_data_node_labels(class_name=class_name, extra_labels=extra_labels)


        # In addition to the passed properties for the new node, data nodes may contain a special attribute: "uri";
        # if a value for `new_uri` was provided, expand `properties_to_set` accordingly
        if new_uri is not None:
            assert type(new_uri) == str, \
                "create_data_node(): argument `new_uri`, if provided, must be a string"

            #print("URI assigned to new data node: ", new_uri)
            properties_to_set["uri"] = new_uri                   # Expand the dictionary

            # EXAMPLE of properties_to_set at this stage:
            #       {"make": "Toyota", "color": "white", "uri": "car-123"}
            #       where "car-123" is the passed URI


        # TODO: perhaps merge the two approaches, node creation with and without links
        if links is not None:
            allowed_keys = {'internal_id', 'rel_name', 'rel_dir', 'rel_attrs'}
            for d in links:
                assert "internal_id" in d, \
                    f"NeoSchema.create_data_node(): the `links` argument must be a list of dicts that contain the key 'internal_id'; the dict in question: {d}"

                assert "rel_name" in d, \
                    f"NeoSchema.create_data_node(): the `links` argument must be a list of dicts that contain the key 'rel_name'; the dict in question: {d}"

                unexpected_keys = set(d) - allowed_keys     # Set difference.  It should be the empty set

                assert unexpected_keys == set(), \
                    f"NeoSchema.create_data_node(): the `links` argument must be a list of dicts whose keys are one of {allowed_keys}; the dict in question: {d}"

            properties_to_set["_SCHEMA"] = class_name       # Expand the dictionary, to also include the Schema data
            new_internal_id = cls.db.create_node_with_links(labels=labels,
                                               properties=properties_to_set,
                                               links=links, merge=False)
        else:
            new_internal_id = cls._create_data_node_helper(class_name=class_name,
                                                labels=labels, properties_to_set=properties_to_set)

        return new_internal_id



    @classmethod
    def _create_data_node_helper(cls, class_name :str,
                                 labels=None, properties_to_set=None,
                                 uri_namespace=None, primary_key=None, duplicate_option=None) -> Union[int, None]:
        """
        Helper function, to create a new data node (or merge into an existing one), of the type indicated by specified Class,
        with the given label(s) and properties.

        IMPORTANT: all validations/schema checks are assumed to have been performed by the caller functions;
                   this is a private method not meant for the end user!

        :param class_name:
        :param labels:              String, or list/tuple of strings, with label(s)
                                        to assign to the new Data node,
                                        (note: the Class name should be among the labels to assign)
        :param properties_to_set:   [OPTIONAL] Dictionary with the properties of the new data node.
                                        EXAMPLE: {"make": "Toyota", "color": "white"}
        :param uri_namespace:       [OPTIONAL] String with a namespace to use to auto-assign a uri value on the new data node;
                                        if not passed, no uri value gets set on the new node
        :param primary_key:         [OPTIONAL] Name of a field that is to be regarded as a primary key
        :param duplicate_option:    Only applicable if primary_key is specified;
                                        if provided, must be "merge" or "replace"

        :return:                    If a new Data node gets created, return its internal database ID;
                                        otherwise (in case of a duplicate node already present) return None
        """
        if uri_namespace:
            new_uri = cls.reserve_next_uri(namespace=uri_namespace)
            properties_to_set["uri"] = new_uri          # Expand the dictionary, to include the "uri" field

        # Prepare strings and a data-binding dictionary suitable for inclusion in a Cypher query,
        #   to define the new node to be created
        # TODO: labels_str ought to be handled by the calling function (for efficiency; likely always the same)
        labels_str = CypherUtils.prepare_labels(labels)    # EXAMPLE:  ":`CAR`:`INVENTORY`"
        (cypher_props_str, data_binding) = CypherUtils.dict_to_cypher(properties_to_set)
        # EXAMPLE:
        #   cypher_props_str = "{`name`: $par_1, `city`: $par_2}"
        #   data_binding = {'par_1': 'Julian', 'par_2': 'Berkeley'}


        if primary_key:
            set_operator = "" if duplicate_option == "replace" else "+"

            q = f'''
                WITH $record AS rec
                MERGE (dn {labels_str} {{`{primary_key}`: rec['{primary_key}']}}) 
                SET dn {set_operator}= rec 
                SET dn.`_SCHEMA` = "{class_name}" 
                RETURN id(dn) as internal_id 
                '''
            # EXAMPLE, with data_binding {'record': {'name': 'CA'}},
            #          assuming the dbase internal ID of the Class node "State" is 123:
            '''
                WITH $record AS rec
                MERGE (dn :`State` {`name`: rec['name']}) 
                SET dn += rec 
                SET dn.`_SCHEMA` = "my class name" 
                RETURN id(dn) as internal_id 
            '''

            result = cls.db.update_query(q, data_binding={"record": properties_to_set})
            #cls.db.debug_query_print(q, data_binding={"record": properties_to_set})

        else:
            # Create a new Data node, with a "SCHEMA" relationship to its Class node
            # TODO: allow the creation of multiple nodes with a single Cypher query, with an UNWIND ;
            #       see the counterpart  NeoAccess.load_pandas()
            q = f'''          
                CREATE (dn {labels_str} {cypher_props_str})
                SET dn.`_SCHEMA` = "{class_name}"        
                RETURN id(dn) AS internal_id
                '''

            result = cls.db.update_query(q, data_binding)
            #cls.db.debug_query_print(q, data_binding=data_binding)


        #print("_create_data_node_helper(): result = ", result)
        if result.get('nodes_created') == 1:
            return result['returned_data'][0]['internal_id']    # The internal database ID of the newly-created node

        return None     # No new node was created



    @classmethod
    def add_data_node_merge(cls, class_name :str, properties :dict) -> (int, bool):
        """
        A new Data Node gets created ONLY IF there's no other Data Node
        containing the same specified properties (and possibly unspecified others),
        and attached to the given Class.

        An Exception is raised if any of the requested properties
        is not registered with the given Schema Class,
        or if that Class doesn't accept Data Nodes.

        :param class_name:  The Class node for the Data Node to locate, or create if not found
        :param properties:  A dictionary with the properties to look up the Data Node by,
                                or to give to a new one if an existing one wasn't found.
                                EXAMPLE: {"make": "Toyota", "color": "white"}

        :return:            A pair with:
                                1) The internal database ID of either an existing Data Node or of a new one just created
                                2) True if a new Data Node was created, or False if not (i.e. an existing one was found)
        """
        # TODO: eventually absorb into create_data_node()
        # TODO: maybe return a dict with 2 keys: "internal_id" and "created" ? (like done by NeoAccess)

        assert (type(properties) == dict) and (properties != {}), \
            "NeoSchema.add_data_node_merge(): the `properties` argument MUST be a dictionary, and cannot be empty"

        class_internal_id = cls.get_class_internal_id(class_name)

        # Make sure that the Class accepts Data Nodes
        if not cls.allows_data_nodes(class_internal_id=class_internal_id):
            raise Exception(f"NeoSchema.add_data_node_merge(): "
                            f"addition of data nodes to Class `{class_name}` is not allowed by the Schema")

        # Generate an Exception if any of the requested properties is not registered with the Schema Class
        cls.allowable_props(class_internal_id=class_internal_id, requested_props=properties,
                            silently_drop=False)


        # From the dictionary of attribute names/values,
        #       create a part of a Cypher query, with its accompanying data dictionary
        properties["_SCHEMA"] = class_name
        (attributes_str, data_dictionary) = CypherUtils.dict_to_cypher(properties)
        # EXAMPLE - if properties is {'cost': 1.99, 'item description': 'the "red" button', '_SCHEMA': 'accessories'} then:
        #       attributes_str = '{`cost`: $par_1, `item description`: $par_2, `item _SCHEMA`: $par_3}'
        #       data_dictionary = {'par_1': 1.99, 'par_2': 'the "red" button', par_3': 'accessories'}

        q = f'''
            MERGE (n :`{class_name}` {attributes_str})       
            RETURN id(n) AS internal_id
            '''

        result = cls.db.update_query(q, data_dictionary)

        internal_id = result["returned_data"][0]["internal_id"]     # The internal database ID
                                                                    # of the node found or just created

        if result.get("nodes_created") == 1:
            return  (internal_id, True)         # A new node was created
        else:
            return  (internal_id, False)        # An existing node was found



    @classmethod
    def add_data_column_merge(cls, class_name :str, property_name: str, value_list: list) -> dict:
        """
        Add a data column (i.e. a set of single-property data nodes).
        Individual nodes are created only if there's no other data node with the same property/value

        :param class_name:      The Class node for the Data Node to locate, or create if not found
        :param property_name:   The name of the data column (i.e. the name of the data field)
        :param value_list:      A list of values that make up the the data column
        :return:                A dictionary with 2 keys - "new_nodes" and "old_nodes";
                                    their values are the respective numbers of nodes (created vs. found)
        """
        # TODO: eventually absorb into create_data_node()
        assert (type(property_name) == str) and (property_name != ""), \
            "NeoSchema.add_data_column_merge(): the `property_name` argument MUST be a string, and cannot be empty"

        assert (type(value_list) == list) and (value_list != []), \
            "NeoSchema.add_data_column_merge(): the `value_list` argument MUST be a list, and cannot be empty"

        class_internal_id = cls.get_class_internal_id(class_name)

        # Make sure that the Class accepts Data Nodes
        if not cls.allows_data_nodes(class_internal_id=class_internal_id):
            raise Exception(f"NeoSchema.add_data_column_merge(): "
                            f"addition of data nodes to Class `{class_name}` is not allowed by the Schema")

        # Generate an Exception if any of the requested properties is not registered with the Schema Class
        cls.allowable_props(class_internal_id=class_internal_id, requested_props={property_name : 0},
                            silently_drop=False)    # TODO: get rid of hack that requires a value for the property

        new_id_list = []
        existing_id_list = []
        for value in value_list:
            properties = {property_name : value, "_SCHEMA": class_name}
            # From the dictionary of attribute names/values,
            #       create a part of a Cypher query, with its accompanying data dictionary
            (attributes_str, data_dictionary) = CypherUtils.dict_to_cypher(properties)
            # EXAMPLE - if properties is {'cost': 65.99, 'item description': 'the "red" button'} then:
            #       attributes_str = '{`cost`: $par_1, `item description`: $par_2}'
            #       data_dictionary = {'par_1': 65.99, 'par_2': 'the "red" button'}

            q = f'''
                MERGE (n :`{class_name}` {attributes_str})     
                RETURN id(n) AS internal_id
                '''

            result = cls.db.update_query(q, data_dictionary)

            internal_id = result["returned_data"][0]["internal_id"]     # The internal database ID
                                                                        # of the node found or just created
            if result.get("nodes_created") == 1:
                new_id_list.append(internal_id)         # A new node was created
            else:
                existing_id_list.append(internal_id)    # An existing node was found
        # END for

        return {"new_nodes": new_id_list, "old_nodes": existing_id_list}
        # TODO: rename "old_nodes" to "present_nodes" (or "existing_nodes", or "found_nodes")



    @classmethod
    def add_data_point_OLD(cls, class_name="", schema_uri=None,
                           data_dict=None, labels=None,
                           connected_to_id=None, connected_to_labels=None, rel_name=None, rel_dir="OUT", rel_prop_key=None, rel_prop_value=None,
                           new_uri=None, return_uri=True) -> Union[int, str]:
        """
        # TODO: eventually absorb into create_data_node()
        TODO: OBSOLETE.  Replace by add_data_node_with_links()
              TO DITCH *AFTER* add_data_node_with_links() gets link validation!

        Add a new data node, of the Class specified by name or ID,
        with the given (possibly none) attributes and label(s),
        optionally linked to another DATA node, already existing.

        The new data node, if successfully created, will be assigned a unique value for its field uri
        If the requested Class doesn't exist, an Exception is raised

        EXAMPLES:   add_data_point(class_name="Cars", data_dict={"make": "Toyota", "color": "white"}, labels="car")
                    add_data_point(schema_uri="123",     data_dict={"make": "Toyota", "color": "white"}, labels="car",
                                   connected_to_id=999, connected_to_labels="salesperson", rel_name="SOLD_BY", rel_dir="OUT")
                    assuming there's an existing class named "Cars" and an existing data point with uri = 999, and label "salesperson"

        TODO: verify the all the passed attributes are indeed properties of the class (if the schema is Strict)
        TODO: verify that required attributes are present
        TODO: invoke special plugin-code, if applicable
        TODO: make the issuance of a new uri optional

        :param class_name:      The name of the Class that this new data point is an instance of
        :param schema_uri:      Alternate way to specify the Class; if both present, class_name prevails

        :param data_dict:       An optional dictionary with the properties of the new data point.
                                TODO: a better name might be "properties"
                                    EXAMPLE: {"make": "Toyota", "color": "white"}
        :param labels:          String or list of strings with label(s) to assign to the new data node;
                                    if not specified, use the Class name.  TODO: the Class name ought to ALWAYS be added

        :param connected_to_id: Int or None.  To optionally specify another (already existing) DATA node
                                        to connect the new node to, specified by its uri.
                                        TODO: --> for efficiency, use the Neo4j ID instead [and ditch the arg "connected_to_labels"]
                                        EXAMPLE: the uri of a data point representing a particular salesperson or dealership

        The following group only applicable if connected_to_id isn't None
        :param connected_to_labels:     EXAMPLE: "salesperson"
        :param rel_name:        Str or None.  EXAMPLE: "SOLD_BY"
        :param rel_dir:         Str or None.  Either "OUT" (default) or "IN"
        :param rel_prop_key:    Str or None.  Ignored if rel_prop_value is missing
        :param rel_prop_value:  Str or None.  Ignored if rel_prop_key is missing

        :param new_uri:         Normally, the Item ID is auto-generated, but it can also be provided (Note: MUST be a unique string)
        :param return_uri:      Default to True.    TODO: change to False
                                If True, the returned value is the auto-increment "uri" value of the node just created;
                                    otherwise, it returns its Neo4j ID

        :return:                EITHER a string with either the auto-increment "uri" value
                                OR or the internal database ID
                                of the node just created (based on the flag "return_uri")
        """
        #print(f"In add_data_point().  rel_name: `{rel_name}` | rel_prop_key: `{rel_prop_key}` | rel_prop_value: {rel_prop_value}")

        # Make sure that at least either class_name or schema_uri is present
        if (not class_name) and (not schema_uri):
            raise Exception("Must specify at least either the `class_name` or the `schema_uri`")

        if not class_name:
            class_name = cls.get_class_name_by_schema_uri(schema_uri)      # Derive the Class name from its ID

        if labels is None:
            # If not specified, use the Class name
            labels = class_name

        if data_dict is None:
            data_dict = {}

        assert type(data_dict) == dict, "The data_dict argument, if provided, MUST be a dictionary"

        cypher_props_dict = data_dict

        if not cls.allows_data_nodes(class_name=class_name):
            raise Exception(f"Addition of data nodes to Class `{class_name}` is not allowed by the Schema")


        # In addition to the passed properties for the new node, data nodes contain a special attributes: "uri";
        # expand cypher_props_dict accordingly
        # TODO: make this part optional
        if not new_uri:
            new_id = cls.reserve_next_uri()      # Obtain (and reserve) the next auto-increment value
        else:
            new_id = new_uri
        #print("New ID assigned to new data node: ", new_id)
        cypher_props_dict["uri"] = new_id               # Expand the dictionary
        cypher_props_dict["_SCHEMA"] = class_name       # Expand the dictionary

        # EXAMPLE of cypher_props_dict at this stage:
        #       {"make": "Toyota", "color": "white", "uri": 123}
        #       where 123 is the next auto-assigned uri

        # Create a new data node, with a "SCHEMA" relationship to its Class node and, if requested, also a relationship to another data node
        if connected_to_id:     # (A) if requesting a relationship to an existing data node
            if rel_prop_key and (rel_prop_value != '' and rel_prop_value is not None):  # Note: cannot just say "and rel_prop_value" or it'll get dropped if zero
                rel_attrs = {rel_prop_key: rel_prop_value}
            else:
                rel_attrs = None

            neo_id = cls.db.create_node_with_relationships(labels, properties=cypher_props_dict,
                                                  connections=[{"labels": connected_to_labels, "key": "uri", "value": connected_to_id,
                                                                "rel_name": rel_name, "rel_dir": rel_dir, "rel_attrs": rel_attrs}
                                                               ]
                                                  )
        else:                   # (B) simpler case : no links need to be created
            neo_id = cls.db.create_node(labels=labels, properties=cypher_props_dict)

        if return_uri:
            return new_id
        else:
            return neo_id



    @classmethod
    def update_data_node(cls, data_node :Union[int, str], set_dict :dict, drop_blanks = True, class_name=None) -> int:
        """
        Update, possibly adding and/or dropping fields, the properties of an existing Data Node

        :param data_node:   Either an integer with the internal database ID, or a string with a URI value
        :param set_dict:    A dictionary of field name/values to create/update the node's attributes
                                (note: blanks ARE allowed within the keys)
                                Blanks at the start/end of string values are zapped
        :param drop_blanks: If True, then any blank field is interpreted as a request to drop that property
                                (as opposed to setting its value to "")
        :param class_name:  [OPTIONAL] The name of the Class to which the given Data Note is part of;
                                if provided, it gets enforced
        :return:            The number of properties set or removed;
                                if the record wasn't found, or an empty set_dict was passed, return 0
                                Important: a property is counted as "set" even if the new value is
                                           identical to the old value!
        """
        #TODO: test the class_name argument
        #TODO: check whether the Schema allows the added/dropped fields, if applicable
        #      Compare the keys of set_dict against the Properties of the Class of the Data Node

        if set_dict == {}:
            return 0            # Nothing to do!

        if type(data_node) == int:
            where_clause =  f'WHERE id(n) = {data_node}'
        elif type(data_node) == str:
            where_clause =  f'WHERE n.uri = "{data_node}"'
        else:
            raise Exception("update_data_node(): the argument `data_node` must be an integer or a string")


        data_binding = {}
        set_list = []
        remove_list = []
        for field_name, field_value in set_dict.items():            # field_name, field_value are key/values in set_dict
            if type(field_value) == str:
                field_value = field_value.strip()                           # Zap all leading and trailing blanks

            if (field_value != "") or (drop_blanks == False):
                field_name_safe = field_name.replace(" ", "_")              # To protect against blanks in name, which could not be used
                                                                            #   in names of data-binding variables.  E.g., "end date" becomes "end_date"
                set_list.append(f"n.`{field_name}` = ${field_name_safe}")   # Example:  "n.`end date` = end_date"

                data_binding[field_name_safe] = field_value                 # Add entry the Cypher data-binding dictionary, of the form {"end_date": some_value}
            else:
                # We get here in case the field value is a blank string AND drop_blanks is True
                remove_list.append(f"n.`{field_name}`")

        # Example of data_binding at the end of the loop: {'color': 'white', 'max_quantity': 7000}

        set_clause = ""
        if set_list:
            set_clause = "SET " + ", ".join(set_list)   # Example:  "SET n.`color` = $color, n.`max quantity` = $max_quantity"

        remove_clause = ""
        if drop_blanks and remove_list:
            remove_clause = "REMOVE " + ", ".join(remove_list)   # Example:  "REMOVE n.`color`, n.`max quantity`

        if class_name:
            match_str = f"MATCH (n {{`_SCHEMA`: '{class_name}'}}) "
        else:
            match_str = f"MATCH (n) "

        q = f'''
            {match_str} 
            {where_clause}
            {set_clause} 
            {remove_clause}            
            '''

        #cls.db.debug_query_print(q, data_binding)

        stats = cls.db.update_query(q, data_binding)
        #print(stats)
        number_properties_set = stats.get("properties_set", 0)
        return number_properties_set



    @classmethod
    def delete_data_nodes(cls, node_id=None, id_key=None, class_name=None) -> int:
        """
        Delete all the Data Nodes that match all the passed conditions

        :param node_id:     [OPTIONAL] Either an internal database ID or a key value,
                                depending on the value of `id_key`
        :param id_key:      [OPTIONAL] Name of a key used to identify the data node(s) with the `node_id` value;
                                for example, "uri".
                                If blank, then the `node_id` is taken to be the internal database ID
        :param class_name:  [OPTIONAL] The name of a Schema Class
        :return:            The number of Data Nodes that were actually deleted (possibly zero)
        """
        label, clause, data_dict = cls.prepare_match_cypher_clause(node_id=node_id, id_key=id_key,
                                                            class_name=class_name)

        q = f'''
            MATCH (dn {label})
            {clause}
            DETACH DELETE dn
            '''

        #cls.db.debug_query_print(q, data_binding=data_dict)
        stats = cls.db.update_query(q, data_binding=data_dict)

        return stats.get("nodes_deleted", 0)        # Number of nodes deleted



    @classmethod
    def register_existing_data_node(cls, class_name="", schema_uri=None,
                                    existing_neo_id=None, new_uri=None) -> int:
        """
        Register (declare to the Schema) an existing data node with the Schema Class specified by its name or ID.
        An uri is generated for the data node and stored on it.
        Return the newly-assigned uri

        EXAMPLES:   register_existing_data_node(class_name="Chemicals", existing_neo_id=123)
                    register_existing_data_node(schema_uri="schema-19", existing_neo_id=456)

        TODO: verify the all the passed attributes are indeed properties of the class (if the schema is Strict)
        TODO: verify that required attributes are present
        TODO: invoke special plugin-code, if applicable

        :param class_name:      The name of the Class that this new data node is an instance of
        :param schema_uri:      Alternate way to specify the Class; if both present, class_name prevails

        :param existing_neo_id: Internal ID to identify the node to register with the above Class.
                                TODO: expand to use the match() structure
        :param new_uri:     OPTIONAL. Normally, the Item ID is auto-generated,
                                but it can also be provided (Note: MUST be unique)

        :return:                If successful, an integer with the auto-increment "uri" value of the node just created;
                                otherwise, an Exception is raised
        """
        if not existing_neo_id:
            raise Exception("register_existing_data_node() - Missing argument: `existing_neo_id`")

        assert type(existing_neo_id) == int, \
            "register_existing_data_node(): The argument `existing_neo_id` MUST be an integer"  # TODO: use validity checker

        # Make sure that at least either class_name or schema_uri is present
        if (not class_name) and (not schema_uri):
            raise Exception("Must specify at least either the 'class_name' or the 'schema_uri'")

        if not class_name:
            class_name = cls.get_class_name_by_schema_uri(schema_uri)      # Derive the Class name from its ID
            if not class_name:
                raise Exception(f"Unable to locate a Class with schema ID {schema_uri}")

        if not cls.allows_data_nodes(class_name=class_name):
            raise Exception(f"Addition of data nodes to Class `{class_name}` is not allowed by the Schema")


        # Verify that the data node doesn't already have a SCHEMA relationship
        q = f'''
            MATCH (n) 
            WHERE id(n)={existing_neo_id} AND n.`_SCHEMA` IS NOT NULL
            RETURN count(n) AS number_found
            '''
        number_found = cls.db.query(q, single_cell="number_found")
        if number_found:
            raise Exception(f"The given data node ALREADY has a SCHEMA relationship")

        if not new_uri:
            new_uri = cls.reserve_next_uri()     # Generate, if not already provided

        #cls.debug_print("register_existing_data_node(). New uri to be assigned to the data node: ", new_uri)

        data_binding = {"class_name": class_name, "new_uri": new_uri, "existing_neo_id": existing_neo_id}

        # EXAMPLE of data_binding at this stage:
        #       {'class_name': 'Chemicals', 'new_uri': 888, 'existing_neo_id': 123, 'schema_code': 'r'}
        #       where 888 is the next auto-assigned uri

        # Link the existing data node, with a "SCHEMA" relationship, to its Class node, and also set some properties on the data node
        q = f'''
            MATCH (existing) WHERE id(existing) = $existing_neo_id
            SET existing.uri = $new_uri , existing.`_SCHEMA` = $class_name
            '''

        #cls.db.debug_query_print(q, data_binding, "register_existing_data_node") # Note: this is the special debug print for NeoAccess
        result = cls.db.update_query(q, data_binding)
        #print(result)

        number_new_rels = result.get('relationships_created')   # This ought to be 1
        if number_new_rels != 1:
            raise Exception("Failed to created the new relationship (`SCHEMA`)")

        return new_uri



    @classmethod
    def add_data_relationship_hub(cls, center_id :int, periphery_ids :[int], periphery_class :str,
                                  rel_name :str, rel_dir = "OUT") -> int:
        """
        Add a group of relationships between a single Data Node ("center")
        and each of the Data Nodes in the given list ("periphery"),
        with the specified relationship name and direction.

        All Data Nodes must already exist.
        All the "periphery" Data Nodes must belong to the same Class
            (whose name is passed by periphery_class)

        :param center_id:       Internal database ID of an existing Data Node
                                    that we wish to connect
                                    to all other Data Nodes specified in the next argument
        :param periphery_ids:   List of internal database IDs of existing Data Nodes,
                                    all belonging to the Class passed by the next argument
        :param periphery_class: The name of the common Class to which all the Data Nodes
                                    specified in periphery_ids belong to
        :param rel_name:        A string with the name to give to all the newly-created relationships
        :param rel_dir:         Either "IN" (towards the "center" node)
                                    or "OUT" (away from it, towards the "periphery" nodes)

        :return:                The number of relationships created
        """
        cls.assert_valid_relationship_name(rel_name)

        center_class = cls.class_of_data_node(node_id=center_id)


        q = f'''
            MATCH (center_node), (periphery_node :{periphery_class}) 
            WHERE id(center_node)= $center_id AND id(periphery_node) IN $periphery_ids   
                   
            '''

        if rel_dir == "OUT":
            assert cls.class_relationship_exists(from_class=center_class, to_class=periphery_class, rel_name=rel_name), \
                f"add_data_relationship_hub(): first, you must update the Schema to register a `{rel_name}` " \
                f"relationship from Class `{center_class}` to Class `{periphery_class}`"

            q += f" MERGE (center_node)-[:`{rel_name}`]->(periphery_node)"
        elif rel_dir == "IN":
            assert cls.class_relationship_exists(from_class=periphery_class, to_class=center_class, rel_name=rel_name), \
                f"add_data_relationship_hub(): first, you must update the Schema to register a `{rel_name}` " \
                f"relationship from Class `{periphery_class}` to Class `{center_class}`"

            q += f" MERGE (center_node)<-[:`{rel_name}`]-(periphery_node)"
        else:
            raise Exception(f"add_data_relationship_hub(): argument `rel_name` "
                            f"must be either 'IN' or 'OUT'; the value passed was {rel_dir}")

        result = cls.db.update_query(q, {"center_id": center_id, "periphery_ids": periphery_ids})
        number_relationships_added = result.get("relationships_created", 0)   # If key isn't present, use a value of 0

        return number_relationships_added



    @classmethod
    def add_data_relationship(cls, from_id, to_id, rel_name :str, rel_props = None, id_type=None) -> None:
        """
        Simpler (and possibly faster) version of add_data_relationship_OLD()

        Add a new relationship with the given name, from one to the other of the 2 given data nodes,
        identified by their Neo4j ID's.

        The requested new relationship MUST be present in the Schema, or an Exception will be raised.


        Note that if a relationship with the same name already exists between the data nodes exists,
        nothing gets created (and an Exception is raised)

        :param from_id: Either an internal database ID or a primary key value
                            of the data node at which the new relationship is to originate
        :param to_id:   Either an internal database ID or a primary key value
                            of the data node at which the new relationship is to end
        :param rel_name:The name to give to the new relationship between the 2 specified data nodes
                            IMPORTANT: it MUST be allowed by the Schema
        :param rel_props:TODO: not currently used.  Unclear what multiple calls would do in this case

        :param id_type: OPTIONAL - name of a primary key used to identify the data nodes; for example, "uri".
                            Leave blank to use the internal database ID's instead

        :return:            None.  If the specified relationship didn't get created (for example,
                                in case the the new relationship doesn't exist in the Schema), raise an Exception
        """
        assert rel_name, f"NeoSchema.add_data_relationship(): no name was provided for the new relationship"

        from_class = cls.class_of_data_node(node_id=from_id, id_key=id_type)
        to_class = cls.class_of_data_node(node_id=to_id, id_key=id_type)

        assert cls.is_link_allowed(link_name=rel_name, from_class=from_class, to_class=to_class), \
            f"add_data_relationship(): The relationship requested to be added `{rel_name}`, " \
            f"from Class `{from_class}` to Class `{to_class}`, " \
            f"must first be registered in the Schema"


        # Create a query that looks for a path
        # from the first to the second data nodes, passing thru their classes
        # and thru a link with the requested new relationship name between those classes;
        # upon finding such a path, join the data nodes with a relationship

        if id_type:
            where_clause = f"from_data_node.{id_type} = $from_id  AND  to_data_node.{id_type} = $to_id"
        else:
            where_clause = "id(from_data_node) = $from_id  AND  id(to_data_node) = $to_id"

        q = f'''
            MATCH (from_data_node :`{from_class}`), (to_data_node :`{to_class}`)
            WHERE {where_clause}
            MERGE (from_data_node)-[:`{rel_name}`]->(to_data_node)
            '''

        result = cls.db.update_query(q, {"from_id": from_id, "to_id": to_id})
        number_relationships_added = result.get("relationships_created", 0)   # If key isn't present, use a value of 0

        if number_relationships_added != 1:
            # TODO: double-check that the following reported problem is indeed what caused the failure
            raise Exception(f"NeoSchema.add_data_relationship(): Failed to add the relationship `{rel_name}` "
                            f"from data node ({from_id}, of Class `{from_class}`), "
                            f"to data node ({to_id}, of Class `{to_class}`)")



    @classmethod
    def remove_data_relationship(cls, from_id :str, to_id :str, rel_name :str, id_type="uri", labels=None) -> None:
        """
        Drop the relationship with the given name, from one to the other of the 2 given DATA nodes.
        Note: the data nodes are left untouched.
        If the specified relationship didn't get deleted, raise an Exception

        :param from_id:     String with the "uri" value of the data node at which the relationship originates
        :param to_id:       String with the "uri" value of the data node at which the relationship ends
        :param rel_name:    The name of the relationship to delete
        :param id_type:     For now, only "uri" (default) is implemented
        :param labels:      OPTIONAL (generally, redundant).  Labels required to be on both nodes

        :return:            None.  If the specified relationship didn't get deleted, raise an Exception
        """
        # TODO: first verify that the relationship is optional in the schema???
        # TODO: migrate from "uri" values to also offer option or internal database ID's, as done in class_of_data_node()

        assert rel_name != "", f"remove_data_relationship(): no name was provided for the relationship"

        assert id_type == "uri", \
                f"remove_data_relationship(): currently, only the 'uri' option is available for the argument `id_type`"

        match_from = cls.db.match(labels=labels, key_name="uri", key_value=from_id,
                                  dummy_node_name="from")

        match_to =   cls.db.match(labels=labels, key_name="uri", key_value=to_id,
                                  dummy_node_name="to")

        cls.db.remove_links(match_from, match_to, rel_name=rel_name)   # This will raise an Exception if no relationship is removed



    @classmethod
    def remove_multiple_data_relationships(cls, node_id: Union[int, str], rel_name: str, rel_dir: str, labels=None) -> None:
        """
        Drop all the relationships with the given name, from or to the given data node.
        Note: the data node is left untouched.

        IMPORTANT: this function cannot be used to remove relationship involving any Schema node

        :param node_id:     The internal database ID (integer) or name (string) of the data node of interest
        :param rel_name:    The name of the relationship(s) to delete
        :param rel_dir:     Either 'IN', 'OUT', or 'BOTH'
        :param labels:      [OPTIONAL]
        :return:            None
        """
        # TODO: test
        assert rel_name, \
                f"remove_data_relationship(): no name was provided for the relationship to be removed"

        assert (rel_name != "SCHEMA") and (rel_name != "HAS_PROPERTY"), \
                f"remove_data_relationship(): cannot use this function to remove Schema relationships"

        if labels is None:
            labels = ""
        else:
            labels = f":`{labels}`"

        if rel_dir == "OUT":
            match = f"MATCH (n) -[r :{rel_name}]->({labels})"
        elif rel_dir == "IN":
            match = f"MATCH (n) <-[r :{rel_name}]-({labels})"
        elif rel_dir == "BOTH":
            match = f"MATCH (n) -[r :{rel_name}]-({labels})"
        else:
            raise Exception("remove_data_relationship(): the argument `rel_dir` must be either 'IN', 'OUT', or 'BOTH'")

        if type(node_id) == int:
            q = f'''
            {match} WHERE labels(n) <> ["CLASS", "PROPERTY" ]
            AND id(n) = {node_id}
            DELETE r
            '''
        else:
            q = f'''
            {match} WHERE labels(n) <> ["CLASS", "PROPERTY" ]
            AND n.name = "{node_id}"
            DELETE r
            '''

        #print(q)
        cls.db.update_query(q)




    #####################################################################################################

    '''                                  ~   BULK DATA IMPORT   ~                                     '''

    def ________BULK_DATA_IMPORT________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################


    @classmethod
    def import_pandas_nodes_NO_BATCH(cls, df :pd.DataFrame, class_name: str, class_node=None,
                                     select=None, drop=None, rename=None,
                                     primary_key=None, duplicate_option="merge",
                                     datetime_cols=None, int_cols=None,
                                     extra_labels=None, uri_namespace=None,
                                     report_frequency=100) -> [int]:
        """
        OLD VERSION of the much-faster import_pandas_nodes(), largely obsoleted by it!

        Import a group of entities (records), from the rows of a Pandas dataframe,
        as Data Nodes in the database.

        Dataframe cells with NaN's and empty strings are dropped - and never make it into the database.

        Note: if you have a CSV file whose first row contains the field names, you can first do imports such as
                    df = pd.read_csv("C:/Users/me/some_name.csv", encoding = "ISO-8859-1")

        :param df:          A Pandas Data Frame with the data to import;
                                each row represents a record - to be turned into a graph-database node.
                                Each column represents a Property of the data node, and it must have been
                                previously declared in the Schema
        :param class_name:  The name of a Class node already present in the Schema
        :param class_node:  OBSOLETED

        :param select:      [OPTIONAL] Name of the field, or list of names, to import; all others will be ignored
                                (Note: original name prior to any rename, if applicable)
        :param drop:        [OPTIONAL] Name of a field, or list of names, to ignore during import
                                (Note: original name prior to any rename, if applicable)
                                If both arguments "select" and "drop" are passed, an Exception gets raised
        :param rename:      [OPTIONAL] dictionary to rename the Pandas dataframe's columns to
                                EXAMPLE {"current_name": "name_we_want"}

        :param primary_key: [OPTIONAL] Name of a field that is to be regarded as a primary key;
                                            any import of a record that is a duplicate in that field,
                                            will result in the modification of the existing record, rather than the creation of new one;
                                            the details of the modification are based on the argument `duplicate_option'
        :param duplicate_option:    Only applicable if primary_key is specified;
                                    if provided, must be "merge" (default) or "replace".
                                    Any field present in both the original (old) and the new (being imported) record will get over-written with the new value;
                                    any field present in the original record but not the new one
                                    will EITHER be left standing ("merge" option)
                                    or ditched ("replace" option)
                                    EXAMPLE: if the database contains the record  {'vehicle ID': 'c2', 'make': 'Toyota', 'year': 2013}
                                             then the import of                   {'vehicle ID': 'c2', 'make': 'BMW',    'color': 'white'}
                                             with a primary_key of 'vehicle ID', will result in NO new record addition;
                                             the existing record will transform into either
                                             (if duplicate_option is "merge"):
                                                    {'vehicle ID': 'c2', 'make': 'BMW', 'color': 'white', 'year':2013}
                                             (if duplicate_option is "replace"):
                                                    {'vehicle ID': 'c2', 'make': 'BMW', 'color': 'white'}
                                            Notice that the only difference between the 2 option
                                            is fields present in the original record but not in the imported one.

        :param datetime_cols:[OPTIONAL] String, or list/tuple of strings, of column name(s)
                                that contain datetime strings such as '2015-08-15 01:02:03'
                                (compatible with the python "datetime" format)
        :param int_cols:    [OPTIONAL] String, or list/tuple of strings, of column name(s)
                                that contain integers, or that are to be converted to integers
                                (typically necessary because numeric Pandas columns with NaN's
                                 are automatically turned into floats;
                                 this argument will cast them to int's, and drop the NaN's)
        :param extra_labels:[OPTIONAL] String, or list/tuple of strings, with label(s) to assign to the new Data nodes,
                                IN ADDITION TO the Class name (which is always used as label)
        :param uri_namespace:[OPTIONAL] String with a namespace to use to auto-assign uri values on the new Data nodes;
                                if that namespace hasn't previously been created with create_namespace() or with reserve_next_uri(),
                                a new one will be created with no prefix nor suffix (i.e. all uri's be numeric strings.)
                                If not passed, no uri values will get set on the new nodes
        :param report_frequency: [OPTIONAL] How often to print the status of the import-in-progress (default 100)

        :return:            A list of the internal database ID's of the newly-created Data nodes
        """
        # TODO: more pytests; in particular for args uri_namespace, drop, rename
        # TODO: bring in more elements from the counterpart  NeoAccess.load_pandas()
        # TODO: maybe return a separate list of internal database ID's of any updated node

        if class_node is not None:
            print("******** OBSOLETED ARGUMENT: the argument name in import_pandas_nodes() is now called 'class_name', not 'class_node'")
            return

        # Do various validations
        cls.assert_valid_class_name(class_name)

        assert (extra_labels is None) or isinstance(extra_labels, (str, list, tuple)), \
            "NeoSchema.import_pandas_nodes(): the argument `extra_labels`, if passed, must be a string, or list/tuple of strings"

        assert (select is None) or (drop is None), \
            "NeoSchema.import_pandas_nodes(): cannot specify both arguments `select` and `drop`"

        if duplicate_option:
            assert duplicate_option in ["merge", "replace"], \
                "NeoSchema.import_pandas_nodes(): argument `extra_labels`, " \
                "if passed, must be either 'merge' or 'replace'"


        # Obtain the internal database ID of the Class node
        class_internal_id = cls.get_class_internal_id(class_name)


        # Make sure that the Class accepts Data Nodes
        if not cls.allows_data_nodes(class_internal_id=class_internal_id):
            raise Exception(f"NeoSchema.import_pandas_nodes(): "
                            f"addition of data nodes to Class `{class_name}` is not allowed by the Schema")


        labels = class_name     # By default, use the Class name as a label

        if (type(extra_labels) == str) and (extra_labels.strip() != class_name):
            labels = [extra_labels, class_name]

        elif isinstance(extra_labels, (list, tuple)):
            # If we get thus far, labels is a list or tuple
            labels = list(extra_labels)
            if class_name not in extra_labels:
                labels += [class_name]

        if type(datetime_cols) == str:
            datetime_cols = [datetime_cols]
        elif datetime_cols is None:
            datetime_cols = []

        if type(int_cols) == str:
            int_cols = [int_cols]
        elif int_cols is None:
            int_cols = []

        if select is not None:
            if type(select) == str:
                df = df[[select]]
            else:
                df = df[select]

        if drop is not None:
            df = df.drop(drop, axis=1)      # Drop a column, or list of columns

        if rename is not None:
            df = df.rename(rename, axis=1)          # Rename the affected columns in the Pandas data frame
            if primary_key in rename:
                primary_key = rename[primary_key]   # Also switch to the new name of the primary key, if applicable


        # Verify whether all properties are allowed
        # TODO: consider using allowable_props()
        cols = list(df.columns)     # List of column names in the Pandas Data Frame
        class_properties = cls.get_class_properties(class_node=class_name, include_ancestors=True)

        # TODO: this assertion should only happen if the Class is strict
        assert set(cols) <= set(class_properties), \
            f"import_pandas(): attempting to import Pandas dataframe columns " \
            f"not declared in the Schema:  {set(cols) - set(class_properties)}"


        # Prepare the properties to add
        recordset = df.to_dict('records')   # Turn the Pandas dataframe into a list of dicts
        #print(recordset)
        print(f"import_pandas_nodes(): getting ready to import {len(recordset)} records...")

        # Import each row ("recordset") in turn
        internal_id_list = []
        imported_count = 0
        for d in recordset:       # d is a dictionary
            d_scrubbed = cls.scrub_dict(d)          # Zap NaN's, blank strings, leading/trailing spaces

            for dt_col in datetime_cols:
                if dt_col in d_scrubbed:
                    dt_str = d_scrubbed[dt_col]     # EXAMPLE: '2015-08-15 01:02:03'
                    dt_python = datetime.fromisoformat(dt_str)  # As a python "datetime" object
                    # EXAMPLE: datetime.datetime(2015, 8, 15, 1, 2, 3)
                    dt_neo = DateTime.from_native(dt_python)    # In Neo4j format; TODO: let NeoAccess handle this
                    # EXAMPLE: neo4j.time.DateTime(2015, 8, 15, 1, 2, 3, 0)
                    d_scrubbed[dt_col] = dt_neo     # Replace the original string value

            for col in int_cols:
                if col in d_scrubbed:
                    val = d_scrubbed[col]           # This might be a float
                    val_int = int(val)
                    d_scrubbed[col] = val_int       # Replace the original value


            #print(d_scrubbed)

            # Perform the actual import
            new_internal_id = cls._create_data_node_helper(class_name=class_name,
                                                           labels=labels, properties_to_set=d_scrubbed,
                                                           uri_namespace=uri_namespace,
                                                           primary_key=primary_key, duplicate_option=duplicate_option)
            #print("new_internal_id", new_internal_id)
            if new_internal_id is not None:     # If a new Data node was created
                internal_id_list.append(new_internal_id)

            imported_count += 1

            if report_frequency  and  (imported_count % report_frequency == 0):
                print(f"    ...imported {imported_count} so far  (and created a total of {len(internal_id_list)} new nodes)")
        # END for

        if report_frequency:
            print(f"    FINISHED importing {imported_count} records, and created {len(internal_id_list)} new nodes in the process")

        return internal_id_list



    @classmethod
    def import_pandas_nodes(cls, df :pd.DataFrame, class_name: str,
                            select=None, drop=None, rename=None,
                            primary_key=None, duplicate_option="merge",
                            datetime_cols=None, int_cols=None,
                            extra_labels=None,
                            report=True, report_frequency=1,
                            max_batch_size=1000) -> dict:
        """
        Import a group of entities (records), from the rows of a Pandas dataframe,
        as Data Nodes in the database.

        Dataframe cells with NaN's and empty strings are dropped - and never make it into the database.

        Note: if you have a CSV file whose first row contains the field names, you can first do imports such as
                    df = pd.read_csv("C:/Users/me/some_name.csv", encoding = "ISO-8859-1")

        :param df:          A Pandas Data Frame with the data to import;
                                each row represents a record - to be turned into a graph-database node.
                                Each column represents a Property of the data node, and it must have been
                                previously declared in the Schema
        :param class_name:  The name of a Class node already present in the Schema

        :param select:      [OPTIONAL] Name of the Pandas field, or list of names, to import; all others will be ignored
                                (Note: original name prior to any rename, if applicable)
        :param drop:        [OPTIONAL] Name of a Pandas field, or list of names, to ignore during import
                                (Note: original name prior to any rename, if applicable)
                                If both arguments "select" and "drop" are passed, an Exception gets raised
        :param rename:      [OPTIONAL] dictionary to rename the Pandas dataframe's column names to
                                EXAMPLE {"current_name": "name_we_want"}

        :param primary_key: [OPTIONAL] Name of a Pandas field that is to be regarded as a primary key;
                                            any import of a record that is a duplicate in that field,
                                            will result in the modification of the existing record, rather than the creation of new one;
                                            the details of the modification are based on the argument `duplicate_option'
                                            (Note: original name prior to any rename, if applicable)

        :param duplicate_option:    Only applicable if primary_key is specified;
                                    if provided, must be "merge" (default) or "replace".
                                    Any field present in both the original (old) and the new (being imported) record will get over-written with the new value;
                                    any field present in the original record but not the new one
                                    will EITHER be left standing ("merge" option)
                                    or ditched ("replace" option)
                                    EXAMPLE: if the database contains the record  {'vehicle ID': 'c2', 'make': 'Toyota', 'year': 2013}
                                             then the import of                   {'vehicle ID': 'c2', 'make': 'BMW',    'color': 'white'}
                                             with a primary_key of 'vehicle ID', will result in NO new record addition;
                                             the existing record will transform into either
                                             (if duplicate_option is "merge"):
                                                    {'vehicle ID': 'c2', 'make': 'BMW', 'color': 'white', 'year':2013}
                                             (if duplicate_option is "replace"):
                                                    {'vehicle ID': 'c2', 'make': 'BMW', 'color': 'white'}
                                            Notice that the only difference between the 2 option
                                            is fields present in the original record but not in the imported one.

        :param datetime_cols:   [OPTIONAL] String, or list/tuple of strings, of column name(s)
                                    that contain datetime strings such as '2015-08-15 01:02:03'
                                    (compatible with the python "datetime" format)
        :param int_cols:        [OPTIONAL] String, or list/tuple of strings, of column name(s)
                                    that contain integers, or that are to be converted to integers
                                    (typically necessary because numeric Pandas columns with NaN's
                                     are automatically turned into floats;
                                     this argument will cast them to int's, and drop the NaN's)
        :param extra_labels:    [OPTIONAL] String, or list/tuple of strings, with label(s) to assign to the new Data nodes,
                                    IN ADDITION TO the Class name (which is always used as label)
        :param report:          [OPTIONAL] If True (default), print the status of the import-in-progress
                                    at the end of each batch round
        :param report_frequency: [OPTIONAL] Only applicable if report is True;
                                    how often (in terms of number of batches)
                                    to print out the status of the import-in-progress

        :param max_batch_size:  To limit the number of Pandas rows loaded into the database at one time

        :return:                A dict with 2 keys:
                                    'number_nodes_created': the number of newly-created nodes
                                    'affected_nodes_ids'    list of the internal database ID's nodes that were created or updated,
                                                            in the import order ("updated" doesn't necessarily mean changed).
                                                            Note that ID's might occur more than once when the "primary_key" arg
                                                            is specified, because imports might then refer to existing,
                                                            or previously-created. nodes.
        """
        # TODO: restore uri_namespace , present in the old version
        # TODO: maybe return a separate list of internal database ID's of any updated node

        # Validations
        cls.assert_valid_class_name(class_name)

        assert (extra_labels is None) or isinstance(extra_labels, (str, list, tuple)), \
            "NeoSchema.import_pandas_nodes(): the argument `extra_labels`, if passed, must be a string, or list/tuple of strings"

        assert (select is None) or (drop is None), \
            "NeoSchema.import_pandas_nodes(): cannot specify both arguments `select` and `drop`"

        if duplicate_option:
            assert duplicate_option in ["merge", "replace"], \
                "NeoSchema.import_pandas_nodes(): argument `extra_labels`, " \
                "if passed, must be either 'merge' or 'replace'"

        if primary_key is not None:
            assert primary_key in list(df.columns), \
                f"NeoSchema.import_pandas_nodes(): the requested primary_key (`{primary_key}`) " \
                f"is not present among the column of the given Pandas dataframe"

            if drop is not None:
                assert (primary_key != drop) and  (primary_key not in drop), \
                    f"NeoSchema.import_pandas_nodes(): the requested primary_key (`{primary_key}`) " \
                    f"cannot be one of the dropped columns ({drop})"


        # Obtain the internal database ID of the Class node
        class_internal_id = cls.get_class_internal_id(class_name)


        # Make sure that the Class accepts Data Nodes
        if not cls.allows_data_nodes(class_internal_id=class_internal_id):
            raise Exception(f"NeoSchema.import_pandas_nodes(): "
                            f"addition of data nodes to Class `{class_name}` is not allowed by the Schema")


        # Prepare the list of labels to use on the new Data Nodes
        labels = cls._prepare_data_node_labels(class_name=class_name, extra_labels=extra_labels)


        if type(datetime_cols) == str:
            datetime_cols = [datetime_cols]
        elif datetime_cols is None:
            datetime_cols = []

        if type(int_cols) == str:
            int_cols = [int_cols]
        elif int_cols is None:
            int_cols = []

        if select is not None:
            if type(select) == str:
                df = df[[select]]
            else:
                df = df[select]

        if drop is not None:
            df = df.drop(drop, axis=1)      # Drop a column, or list of columns

        if rename is not None:
            df = df.rename(rename, axis=1)          # Rename the affected columns in the Pandas data frame
            if primary_key in rename:
                primary_key = rename[primary_key]   # Also switch to the new name of the primary key, if applicable


        # Verify whether all properties are allowed
        # TODO: consider using allowable_props()
        cols = list(df.columns)     # List of column names in the Pandas Data Frame
        class_properties = cls.get_class_properties(class_node=class_name, include_ancestors=True)

        # TODO: this assertion should only happen if the Class is strict
        assert set(cols) <= set(class_properties), \
            f"import_pandas_nodes(): attempting to import Pandas dataframe columns " \
            f"not declared in the Schema:  {set(cols) - set(class_properties)}"


        # Convert Pandas' datetime format to Neo4j's
        #df = cls.db.pd_datetime_to_neo4j_datetime(df)


        internal_id_list = []       # Running list of the internal database ID's of the created or updated nodes
                                    # (noted: "updated" doesn't necessarily entail changed)

        created_node_count = 0      # Running list of the number of new nodes created

        # Determine the number of needed batches (always at least 1)
        number_batches = math.ceil(len(df) / max_batch_size)    # Note that if the max_chunk_size equals the size of df
                                                                # then we'll just use 1 batch
        print(f"import_pandas_nodes(): importing {len(df)} records in {number_batches} batch(es) of max size {max_batch_size}...")

        batch_list = np.array_split(df, number_batches)     # List of Pandas data frames,
                                                            # each resulting from splitting the original data frame
                                                            # into groups of rows

        labels_str = CypherUtils.prepare_labels(labels)    # EXAMPLE:  ":`CAR`:`INVENTORY`"

        # Process the primary keys, if any
        primary_key_s = ''
        if primary_key is not None:
            primary_key_s = ' {' + f'`{primary_key}`:record[\'{primary_key}\']' + '}'
            # EXAMPLE of primary_key_s , assuming that the argument `primary_key` is "patient_id":
            #                           "{patient_id:record['patient_id']}"
            # Note that "record" is a dummy name used in the Cypher query, further down


        # Import each batch of records (Pandas dataframe rows) in turn
        if report:
            print()

        for batch_count, df_chunk in enumerate(batch_list):         # Split the import operation into batches
            # df_chunk is a Pandas data frame, with the same columns, but fewer rows, as the original data frame df
            if report and ((batch_count+1) % report_frequency == 0):
                print(f"   Importing batch # {batch_count+1} : {len(df_chunk)} row(s)")

            record_list = df_chunk.to_dict(orient='records')    # Turn the Pandas dataframe into a list of dicts;
                                                                # each dict contains the data for 1 row, with the properties to import
                                                                # EXAMPLE: [{'col1': 1, 'col2': 0.5}, {'col1': 2, 'col2': 0.75}]

            scrubbed_record_list = []

            for d in record_list:               # d is a dictionary.  EXAMPLE: {'col1': 1, 'col2': 0.5}
                d_scrubbed = cls.scrub_dict(d)          # Zap NaN's, blank strings, leading/trailing spaces

                for dt_col in datetime_cols:
                    if dt_col in d_scrubbed:
                        dt_str = d_scrubbed[dt_col]     # EXAMPLE: '2015-08-15 01:02:03'
                        dt_python = datetime.fromisoformat(dt_str)  # As a python "datetime" object
                        # EXAMPLE: datetime.datetime(2015, 8, 15, 1, 2, 3)
                        # TODO: maybe do a dataframe-wide op such as df = db.pd_datetime_to_neo4j_datetime(df) done in NeoAccess
                        dt_neo = DateTime.from_native(dt_python)    # In Neo4j format; TODO: let NeoAccess handle this
                        # EXAMPLE: neo4j.time.DateTime(2015, 8, 15, 1, 2, 3, 0)
                        d_scrubbed[dt_col] = dt_neo     # Replace the original string value

                for col in int_cols:
                    if col in d_scrubbed:
                        val = d_scrubbed[col]           # This might be a float
                        val_int = int(val)
                        d_scrubbed[col] = val_int       # Replace the original value

                scrubbed_record_list.append(d_scrubbed)


            # PERFORM THE ACTUAL BATCH IMPORT

            if not primary_key:     # Simpler scenario; just creation of new nodes
                q = f'''
                    MATCH (cl :CLASS)
                    WHERE id(cl) = {class_internal_id} 
                    WITH cl, $data AS data 
                    UNWIND data AS record 
                    CREATE (dn {labels_str}) 
                    SET dn = record , dn.`_SCHEMA` = $class_name
                    RETURN id(dn) as internal_id 
                    '''

            else:                   # More complex scenario possibly involving existing nodes
                set_operator = "" if duplicate_option == "replace" else "+"

                q = f'''
                    MATCH (cl :CLASS)
                    WHERE id(cl) = {class_internal_id} 
                    WITH cl, $data AS data 
                    UNWIND data AS record 
                    MERGE (dn {labels_str} {primary_key_s}) 
                    SET dn {set_operator}= record , dn.`_SCHEMA` = $class_name
                    RETURN id(dn) as internal_id 
                    '''


            result = cls.db.update_query(q, data_binding={"data": scrubbed_record_list, "class_name": class_name})
            #cls.db.debug_query_print(q, data_binding={"data": scrubbed_record_list})
            #print("    result of running batch =", result)

            if result.get('nodes_created'):
                created_node_count += result.get('nodes_created')

            import_data = result['returned_data']
            for import_item in import_data:
                internal_id_list.append(import_item['internal_id'])  # The internal database ID of the created or updated nodes

            if report and ((batch_count+1) % report_frequency == 0):
                print(f"     Interim status: at the end of this batch, imported a grand total of {len(internal_id_list)} record(s), and created a grand total of {created_node_count} new node(s)")

        # END for


        print(f"    FINISHED importing {len(internal_id_list)} record(s), and created {created_node_count} new node(s) in the process")

        return {'number_nodes_created': created_node_count, 'affected_nodes_ids': internal_id_list}



    @classmethod
    def import_pandas_links_NO_BATCH(cls, df :pd.DataFrame,
                            class_from :str, class_to :str,
                            col_from :str, col_to :str,
                            link_name :str,
                            col_link_props=None, name_map=None,
                            skip_errors = False, report_frequency=100) -> [int]:
        """
        Expected to become the OLD VERSION of import_pandas_links(), largely obsoleted by it!

        Import a group of relationships between existing database Data Nodes,
        from the rows of a Pandas dataframe, as database links between the existing Data Nodes.

        :param df:          A Pandas Data Frame with the data RELATIONSHIP to import

        :param class_from:  Name of the Class of the data nodes that the links originate from
        :param class_to:    Name of the Class of the data nodes that the links end into
        :param col_from:    Name of the Data Frame column identifying the data nodes from which the relationship starts
                                (the values are expected to be foreign keys)
        :param col_to:      Name of the Data Frame column identifying the data nodes to which the relationship ends
                                (the values are expected to be foreign keys)

        :param link_name:   Name of the new relationship being created
        :param col_link_props: [OPTIONAL] Name of a property to assign to the relationships,
                                as well as name of the Data Frame column containing the values.
                                Any NaN values are ignored (no property set on that relationship.)
        :param name_map:    [OPTIONAL] Dict with mapping from Pandas column names
                                to Property names in the data nodes in the database
        :param skip_errors: [OPTIONAL] If True, the import continues even in the presence of errors;
                                default is False
        :param report_frequency: [OPTIONAL] How often to print out the status of the import-in-progress
                                    (in terms of number of imported links)

        :return:            A list of of the internal database ID's of the created links
        """
        cls.assert_valid_relationship_name(link_name)
        # TODO: verify that the requested relationship between the Classes is allowed by the Schema

        cols = list(df.columns)     # List of column names in the Pandas Data Frame
        assert col_from in cols, \
            f"import_pandas_links(): the given Data Frame doesn't have the column named `{col_from}` " \
            f"requested in the argument 'col_from'"

        assert col_to in cols, \
            f"import_pandas_links(): the given Data Frame doesn't have the column named `{col_to}` " \
            f"requested in the argument 'col_to'"


        # Starting with the column names in the Pandas data frame,
        # determine the name of the field names in the database if they're mapped to a different name
        if name_map and col_from in name_map:
            key_from = name_map[col_from]
        else:
            key_from = col_from

        if name_map and col_to in name_map:
            key_to = name_map[col_to]
        else:
            key_to = col_to

        if name_map and col_link_props in name_map:
            link_prop = name_map[col_link_props]
        else:
            link_prop = col_link_props


        recordset = df.to_dict('records')   # Turn the Pandas dataframe into a list of dicts
        print(f"Getting ready to import {len(recordset)} links...")

        links_imported = []
        for d in recordset:     # d is a dictionary
            # For each row, in the Pandas data frame: prepare a Cypher query to link up the 2 nodes
            # TODO: turn into a whole-dataset query

            rel_cypher = ""     # Portion of the Cypher query for the setting (optional) properties on the new link
            data_dict = {"value_from": d[col_from], "value_to": d[col_to]}
            is_nan = False
            if link_prop:
                rel_prop_value = d[link_prop]
                if pd.isna(rel_prop_value):
                    is_nan = True
                else:
                    rel_cypher = f"{{`{link_prop}`: $rel_prop_value}}"
                    data_dict["rel_prop_value"] = rel_prop_value

            q = f'''
                MATCH (from_node :`{class_from}` {{`{key_from}`: $value_from}}), (to_node :`{class_to}` {{`{key_to}`: $value_to}})
                MERGE (from_node)-[r:`{link_name}` {rel_cypher}]->(to_node)
                RETURN id(r) AS link_id
                '''

            #cls.db.debug_query_print(q, data_dict)
            result = cls.db.update_query(q, data_dict)
            #print(result)

            if result.get('relationships_created') == 1:    # If a new link was created
                returned_data = result.get('returned_data')
                # EXAMPLE of returned_data': [{'link_id': 103}]}
                links_imported.append(returned_data[0]["link_id"])
                if col_link_props and (not is_nan) and (result.get('properties_set') != 1):
                    error_msg = f"import_pandas_links(): failed to set the property value " \
                                f"for the new relationship for Pandas row: {d}"
                    if skip_errors:
                        print(error_msg)
                    else:
                        raise Exception(error_msg)
            else:                                           # If no link was created
                error_msg = f"import_pandas_links(): failed to create a new relationship for Pandas row: {d}"
                if skip_errors:
                    print(error_msg)
                else:
                    raise Exception(error_msg)

            if report_frequency  and  (len(links_imported) % report_frequency == 0):
                print(f"    imported {len(links_imported)} so far")
        # END for

        if report_frequency:
            print(f"    FINISHED importing a total of {len(links_imported)} links")

        return links_imported



    @classmethod
    def import_pandas_links_OLD(cls, df :pd.DataFrame,
                                class_from :str, class_to :str,
                                col_from :str, col_to :str,
                                link_name :str,
                                col_link_props=None, rename=None,
                                skip_errors = False,
                                report=True, report_frequency=100,
                                max_batch_size=1000) -> [int]:
        """
        TODO: Obsolete in favor of the new import_pandas_links()

        Import a group of relationships between existing database Data Nodes,
        from the rows of a Pandas dataframe, as database links between existing Data Nodes.
        All relationships must be between data nodes of two given Classes.

        :param df:          A Pandas Dataframe with the data RELATIONSHIP to import.
                                This dataframe plays the role of a "join table".
                                EXAMPLE - adata frame with 2 columns "City ID" and "State ID",
                                          to link up existing Cities and States with "IS_IN" relationships

        :param class_from:  Name of the Class of the data nodes that the links originate from
        :param class_to:    Name of the Class of the data nodes that the links end into
        :param col_from:    Name of the Dataframe column (prior to any optional renaming) that contains values
                                identifying the data nodes from which the link starts;
                                note that these values play the role of foreign keys
        :param col_to:      Name of the Dataframe column (prior to any optional renaming) that contains values
                                identifying the data nodes to which the link ends;
                                note that these values play the role of foreign keys

        :param link_name:   Name to assign to the new relationships being created
        :param col_link_props: [OPTIONAL] Name of a property to assign to the relationships;
                                it must match up the name of the Dataframe column, which contains the value.
                                Any NaN values are ignored (no property will be set on that relationship)

        :param rename:      [OPTIONAL] Dict with mapping from Pandas column names
                                to the names of Properties in the data nodes and/or in their links
                                
        :param skip_errors: [OPTIONAL] If True, the import continues even in the presence of errors;
                                default is False
        :param report:      [OPTIONAL] If True (default), print the status of the import-in-progress
                                at the end of each batch round
        :param report_frequency: [OPTIONAL] Only applicable if report is True;
                                    how often (in terms of number of batches)
                                    to print out a status of the import-in-progress

        :param max_batch_size:  [OPTIONAL]  To limit the number of Pandas rows loaded into the database at one time

        :return:                A list of the internal database ID's of the created links
        """
        cls.assert_valid_relationship_name(link_name)
        # TODO: verify that the requested relationship between the Classes is allowed by the Schema

        cols = list(df.columns)     # List of column names in the Pandas Data Frame
        assert col_from in cols, \
            f"import_pandas_links(): the given Data Frame doesn't have the column named `{col_from}` " \
            f"requested in the argument 'col_from'"

        assert col_to in cols, \
            f"import_pandas_links(): the given Data Frame doesn't have the column named `{col_to}` " \
            f"requested in the argument 'col_to'"


        # Manage column renaming, if applicable
        if rename is not None:
            df = df.rename(rename, axis=1)          # Rename the affected columns in the Pandas data frame

        # Starting with the column names in the Pandas data frame,
        # determine the name of the field names in the database if they're mapped to a different name
        if rename and col_from in rename:
            key_from = rename[col_from]
        else:
            key_from = col_from

        if rename and col_to in rename:
            key_to = rename[col_to]
        else:
            key_to = col_to

        if rename and col_link_props in rename:
            link_prop = rename[col_link_props]
        else:
            link_prop = col_link_props  # Note that this could be None


        # Determine the number of needed batches (always at least 1)
        number_batches = math.ceil(len(df) / max_batch_size)    # Note that if the max_chunk_size equals the size of recordset
                                                                # then we'll just use 1 batch
        print(f"import_pandas_links(): importing {len(df)} links in {number_batches} batch(es) of max size {max_batch_size}...")

        batch_list = np.array_split(df, number_batches)     # List of Pandas data frames,
                                                            # each resulting from splitting the original data frame
                                                            # into groups of rows
        # EXAMPLE of ONE ELEMENT in the list
        #    State ID  City ID
        # 0         1       18
        # 1         1       19


        # Import each batch of records (Pandas dataframe rows) in turn
        if report:
            print()

        link_id_list = []

        for batch_count, df_chunk in enumerate(batch_list):         # Split the import operation into batches
            # df_chunk is a Pandas data frame, with the same columns, but fewer rows, as the original data frame df
            if report and ((batch_count+1) % report_frequency == 0):
                print(f"   Importing batch # {batch_count+1} : {len(df_chunk)} row(s)")

            link_list = df_chunk.to_dict(orient='records')      # Turn the Pandas dataframe into a list of dicts;
                                                                # each dict (originating from 1 row of the dataframe)
                                                                # contains the data for 1 link
                                                                # EXAMPLE: [{'City ID': 18, 'State ID': 1, 'Rank': 10},
                                                                #           {'City ID': 19, 'State ID': 1, 'Rank': NaN}]
            #print(link_list)

            # PERFORM THE ACTUAL BATCH IMPORT

            # For each element in the list prepare a Cypher query to link up a pairs of nodes
            q = f'''
                UNWIND $link_list AS link_dict
                WITH link_dict
                MATCH (from_node :`{class_from}` {{`{key_from}`: link_dict["{key_from}"]}}), 
                      (to_node :`{class_to}` {{`{key_to}`: link_dict["{key_to}"]}})             
                MERGE (from_node)-[r:`{link_name}`]->(to_node)
                WITH r, link_dict["{link_prop}"] AS prop_value
                SET (CASE WHEN TOSTRING(prop_value) <> 'NaN' THEN r END).`{link_prop}` = prop_value
                RETURN id(r) AS link_id
                '''

            # EXAMPLE of query:
            '''
                UNWIND $link_list AS link_dict
                WITH link_dict
                MATCH (from_node :`City` {`City ID`: link_dict["City ID"]}), 
                      (to_node :`State` {`State ID`: link_dict["State ID"]})
                MERGE (from_node)-[r:`IS_IN`]->(to_node)
                WITH r, link_dict["Rank"] AS prop_value
                SET (CASE WHEN TOSTRING(prop_value) <> 'NaN' THEN r END).`Rank` = prop_value
                RETURN id(r) AS link_id
            '''
            # EXAMPLE of data_binding:  {'link_list': [{'City ID': 18, 'State ID': 1, 'Rank': 10},
            #                                          {'City ID': 19, 'State ID': 1, 'Rank': NaN}
            #                                         ]
            #                            }

            # NOTE -  the line  "SET (CASE WHEN TOSTRING(prop_value) <> 'NaN' THEN r END).`Rank` = prop_value"
            #         has the effect of setting the `Rank` property of the new relationship r *only* if prop_value isn't NaN ;
            #         if not a NaN, then that line simply becomes:  SET r.`Rank` = prop_value
            #         See:  https://neo4j.com/docs/cypher-manual/4.4/clauses/set/#set-set-a-property

            data_binding={"link_list": link_list}
            #cls.db.debug_query_print(q, data_binding)

            result = cls.db.update_query(q, data_binding)
            #print("    Result of running batch : ", result)
            # EXAMPLE :  {'_contains_updates': True, 'relationships_created': 2, 'returned_data': [{'link_id': 89345}, {'link_id': 89346}]}


            if result.get('relationships_created') == len(link_list):   # If the expected number of links was created
                import_data = result.get('returned_data')
                # EXAMPLE of import_data: [{'link_id': 89345}, {'link_id': 89346}]}
                for import_item in import_data:
                    link_id_list.append(import_item['link_id'])  # The internal database ID of the created links

            else:                                                       # If fewer links than expected were created
                error_msg = f"import_pandas_links(): in this batch import, " \
                            f"only created {result.get('relationships_created', 0)} links, instead of the expected {len(link_list)}"
                if skip_errors:
                    print(error_msg)
                else:
                    raise Exception(error_msg)

            if report and ((batch_count+1) % report_frequency == 0):
                print(f"     Interim status: at the end of this batch, imported a grand total of {len(link_id_list)} link(s)")

        # END for

        if report_frequency:
            print(f"    FINISHED importing a total of {len(link_id_list)} links")

        return link_id_list



    @classmethod
    def import_pandas_links(cls, df :pd.DataFrame,
                            class_from :str, class_to :str,
                            col_from :str, col_to :str,
                            link_name :str, cols_link_props=None,
                            skip_errors = False,
                            report=True, report_frequency=5,
                            max_batch_size=1000) -> [int]:
        """
        Import a group of relationships between existing database Data Nodes,
        from the rows of a Pandas dataframe, as database links between existing Data Nodes.
        All relationships must be between data nodes of two given Classes.

        :param df:          A Pandas Dataframe with the data RELATIONSHIP to import.
                                This dataframe plays the role of a "join table".
                                EXAMPLE - a data frame with 2 columns "City ID" and "State ID",
                                          to link up existing Cities and States with "IS_IN" relationships

        :param class_from:  Name of the Class of the data nodes that the links originate from
        :param class_to:    Name of the Class of the data nodes that the links end into
        :param col_from:    Name of the Dataframe column that contains values
                                identifying the data nodes from which the link starts;
                                note that these values play the role of foreign keys
        :param col_to:      Name of the Dataframe column that contains values
                                identifying the data nodes to which the link ends;
                                note that these values play the role of foreign keys

        :param link_name:   Name to assign to the new relationships being created
        :param cols_link_props: [OPTIONAL] Name, or list of names, of properties to assign to the new relationships;
                                it must match up the name(s) of the Dataframe column(s) that contain(s) the value(s).
                                Any NaN values are ignored (no property will be set on that relationship)

        :param skip_errors:     [OPTIONAL] If True, the import continues even in the presence of errors;
                                    default is False
        :param report:          [OPTIONAL, DEPRECATED] If True (default), print the status of the import-in-progress
                                    periodically at the end of a subset of imported batch, as often as specified
                                    by the next argument
        :param report_frequency: [OPTIONAL] Only applicable if report is True;
                                    how often (in terms of number of batches imported)
                                    to print out a status of the import-in-progress

        :param max_batch_size:  [OPTIONAL] To limit the number of Pandas rows loaded into the database at one time

        :return:                A list of the internal database ID's of the created links
        """
        # TODO: obsolete arg "report"
        # TODO: if "report_frequency" isn't specified by the user (None), select a value dynamically based on the import size and max_batch_size

        cls.assert_valid_relationship_name(link_name)
        # TODO: verify that the requested relationship between the Classes is allowed by the Schema

        # Validate the presence of the expected column names in the Pandas Data Frame
        cols = list(df.columns)     # List of column names in the Pandas Data Frame
        assert col_from in cols, \
            f"import_pandas_links(): the given Data Frame doesn't have the column named `{col_from}` " \
            f"requested in the argument 'col_from'"

        assert col_to in cols, \
            f"import_pandas_links(): the given Data Frame doesn't have the column named `{col_to}` " \
            f"requested in the argument 'col_to'"


        key_from = col_from
        key_to = col_to

        if type(cols_link_props) == list:
            link_props = cols_link_props
        else:
            link_props = [cols_link_props]

        # Determine the number of needed batches (always at least 1)
        number_batches = math.ceil(len(df) / max_batch_size)    # Note that if the max_chunk_size equals the size of recordset
                                                                # then we'll just use 1 batch
        print(f"import_pandas_links(): importing {len(df)} links in {number_batches} batch(es) of max size {max_batch_size}...")

        batch_list = np.array_split(df, number_batches)     # List of Pandas data frames,
                                                            # each resulting from splitting the original data frame
                                                            # into groups of rows

        # EXAMPLE of *ONE* ELEMENT in the batch_list (batch_list is a list of them):
        #       a Pandas data frame, with the same columns, but fewer rows, as the original data frame df
        #print("batch_list[0]: \n", batch_list[0])
        '''
            city_id  state_id  rank region
        0        1         1    53  north
        1        3         1     4  north
        '''

        # Import each batch of records (Pandas dataframe rows) in turn
        if report:
            print()

        link_id_list = []

        for batch_count, df_chunk in enumerate(batch_list):         # Split the import operation into batches
            # df_chunk is a Pandas data frame, with the same columns, but fewer rows, as the original data frame df
            '''
                city_id  state_id  rank region
            0        1         1    53  north
            1        3         1     4  north            
            '''
            if report and ((batch_count+1) % report_frequency == 0):
                print(f"   Importing batch # {batch_count+1} : {len(df_chunk)} row(s)")

            link_list = cls._restructure_df(df=df_chunk, col_from=key_from, col_to=key_to, cols_other=link_props)
                                # Turn the Pandas dataframe into a list of dicts;
                                # each dict (originating from 1 row of the dataframe)
                                # contains the data for 1 link
                                # EXAMPLE: [{'FROM': 1, 'TO': 1, 'OTHER_FIELDS': {'rank': 53, 'region': 'north'}},
                                #           {'FROM': 3, 'TO': 1, 'OTHER_FIELDS': {'rank': 4, 'region': 'north'}}]
            #print("link_list:\n", link_list)


            # *** PERFORM THE ACTUAL BATCH IMPORT ***

            # For each element in the list prepare a Cypher query to link up a pairs of nodes
            q = f'''
                UNWIND $link_list AS link_dict
                WITH link_dict
                MATCH (from_node :`{class_from}` {{`{key_from}`: link_dict["FROM"]}}), 
                      (to_node   :`{class_to}`   {{`{key_to}`  : link_dict["TO"]}})             
                MERGE (from_node)-[r:`{link_name}`]->(to_node)
                WITH r, link_dict["OTHER_FIELDS"] AS link_props
                SET r = link_props
                RETURN id(r) AS link_id
                '''

            data_binding={"link_list": link_list}

            # EXAMPLE of query:
            '''
                UNWIND $link_list AS link_dict
                WITH link_dict
                MATCH (from_node :`City`  {`city_id` : link_dict["FROM"]}), 
                      (to_node   :`State` {`state_id`: link_dict["TO"]})             
                MERGE (from_node)-[r:`IS_IN`]->(to_node)
                WITH r, link_dict["OTHER_FIELDS"] AS link_props
                SET r = link_props
                RETURN id(r) AS link_id
            '''
            # EXAMPLE of data_binding:
            '''
                {'link_list': [
                                {'FROM': 1, 'TO': 1, 'OTHER_FIELDS': {'rank': 53, 'region': 'north'}}, 
                                {'FROM': 3, 'TO': 1, 'OTHER_FIELDS': {'rank': 4,  'region': 'north'}}
                              ]
                }
            '''

            #cls.db.debug_query_print(q, data_binding)

            result = cls.db.update_query(q, data_binding)
            #print("    Result of running batch : ", result)
            # EXAMPLE :  {'_contains_updates': True,
            #             'relationships_created': 2, 'properties_set': 4,
            #             'returned_data': [{'link_id': 11}, {'link_id': 12}]}

            if result.get('relationships_created') == len(link_list):   # If the expected number of links was created
                import_data = result.get('returned_data')
                # EXAMPLE of import_data:   [{'link_id': 11}, {'link_id': 12}]}
                for import_item in import_data:
                    link_id_list.append(import_item['link_id'])  # The internal database ID of the created links

            else:                                                       # If fewer links than expected were created
                error_msg = f"import_pandas_links(): in this batch import, " \
                            f"only created {result.get('relationships_created', 0)} links, instead of the expected {len(link_list)}"
                if skip_errors:
                    print(error_msg)
                else:
                    raise Exception(error_msg)

            if report and ((batch_count+1) % report_frequency == 0):
                print(f"     Interim status: at the end of this batch, imported a grand total of {len(link_id_list)} link(s)")

        # END for

        if report_frequency:
            print(f"    FINISHED importing a total of {len(link_id_list)} links")

        return link_id_list



    @classmethod
    def _restructure_df(cls, df, col_from :str, col_to :str, cols_other :[str]) -> [dict]:
        """
        Take a Pandas dataframe with at least 2 columns,
        whose names are respectively given by col_from and col_to,
        and turn it into a list of dicts.

        Each dictionary contains 3 key/value pairs:
            1) "FROM", with the value from the column identified by col_from
            2) "TO", with the value from the column identified by to_from
            3) "OTHER_FIELDS, with a dict with the names/values from all the columns identified by cols_other;
                        Pairs with values that are None, blanks strings and Numpy Nan's are dropped

        EXAMPLE - given the following dataframe df:
               A  B   C    D     E
            0  1  x  10  100  1000
            1  2  y  20  200  2000
        then   _restructure_df(df=df, col_from="A", col_to="B", cols_other=["C","E"]) gives:
                         [{'FROM': 1, 'TO': 'x', 'OTHER_FIELDS': {'C': 10, 'E': 1000}},
                          {'FROM': 2, 'TO': 'y', 'OTHER_FIELDS': {'C': 20, 'E': 2000}}]

        :param df:          A Pandas dataframe with at least 2 columns,
                                whose names are specified in the next 2 fields
        :param col_from:    The name of a column in the above Pandas dataframe
        :param col_to:      The name of another column in the above Pandas dataframe
        :param cols_other:  A (possibly-empty) list of other column names in the dataframe
        :return:            A list of dicts, derived from the rows of the dataframe
        """
        # Transforming the DataFrame
        data_list = [
            {
                "FROM": row[col_from],
                "TO": row[col_to],
                "OTHER_FIELDS": {col: row[col] for col in cols_other
                                                if cls._not_junk(row[col])}     # Strip off "junk" values
            }
            for _, row in df.iterrows()     # iterrows() allows iterating over each row of the DataFrame
        ]

        return data_list



    @classmethod
    def _not_junk(cls, v) -> bool:
        """
        Return True if the value of v is not "junk", or False otherwise.
        "Junk" is defined as None, empty strings and Numpy NaN

        :param v:   A value that we want to establish whether worthy of being stored in database
        :return:    True if the passed value is considered "worthwhile" to store, or False otherwise
        """
        if not v:
            return False        # This covers None and ""

        if (type(v) == float) and np.isnan(v):
            return False       # This covers Numpy NaN

        return True














    @classmethod
    def scrub_dict(cls, d :dict) -> dict:
        """
        Helper function to clean up data during imports.

        Given a dictionary, assemble and return a new dict where string values are trimmed of
        any leading or trailing blanks.
        Entries whose values are blank or NaN get omitted from the new dictionary being returned.

        EXAMPLE:    {"a": 1, "b": 3.5, "c": float("nan"), "d": "some value", "e": "   needs  cleaning!    ",
                     "f": "", "g": "            "}
                gets simplified to:
                    {"a": 1, "b": 3.5, "d": "some value", "e": "needs  cleaning!"  }

        :param d:   A python dictionary with data to "clean up"
        :return:    A python dictionary with the cleaned-up data
        """
        scrubbed_d = {}
        for k,v in d.items():   # Loop over all key/value pairs in the dictionary
            if type(v) == str:
                v = v.strip()       # Zap all leading and trailing blanks
                if v == "":
                    continue        # Blank string values get omitted

            elif type(v) == float and math.isnan(v):
                continue            # NaN's get omitted

            scrubbed_d[k] = v

        return scrubbed_d



    @classmethod
    def import_triplestore(cls, df :pd.DataFrame, class_node :Union[int, str],
                           col_names = None, uri_prefix = None,
                           datetime_cols=None, int_cols=None,
                           extra_labels=None,
                           report_frequency=100
                           ) -> [int]:
        """
        Import "triplestore" data from a Pandas dataframe that contains 3 columns called:
                subject , predicate , object

        The values of the "subject" column are used for identifying entities, and then turned into URI's.
        The values of the "predicate" column are taken to be the names of the Properties (possibly mapped
            by means of the dictionary "col_names"
        The values of the "object" column are taken to be the values (literals) of the Properties

        Note: "subject" and "predicate" is typically an integer or a string

        EXAMPLE -
            Panda's data frame:
             	subject 	 predicate 	  object
            0 	    57 	            1 	  Advanced Graph Databases
            1 	    57 	            2 	  New York University
            2 	    57 	            3 	  Fall 2024

            col_names = {1: "Course Title", 2: "School", 3: "Semester"}
            uri_prefix = "r-"

            The above will result in the import of a node with the following properties:

                {"uri": "r-57",
                "Course Title": "Advanced Graph Databases",
                "School": "New York University",
                "Semester": "Fall 2024"}

        :param df:              A Pandas dataframe that contains 3 columns called:
                                    subject , predicate , object
        :param class_node:      Either an integer with the internal database ID of an existing Class node,
                                    or a string with its name
        :param col_names:       [OPTIONAL] Dict with mapping from values in the "predicate" column of the data frame
                                           and the names of the new nodes' Properties
        :param uri_prefix:      [OPTIONAL] String to prefix to the values in the "subjec" column
        :param datetime_cols:   [SEE import_pandas_nodes()]
        :param int_cols:        [SEE import_pandas_nodes()]
        :param extra_labels:    [SEE import_pandas_nodes()]
        :param report_frequency:[SEE import_pandas_nodes()]

        :return:                A list of the internal database ID's of the newly-created Data nodes
        """
        # Note: an alternate implementation might use df.groupby(['subject']).head(1)
        #       and then directly import the records, rather than be built atop import_pandas_nodes()
        if uri_prefix:
            # Alter the 'subject' column with a prefix
            df['subject'] = uri_prefix + df['subject'].astype(str)


        # Transform the triples ("narrow table") into a wide table with all the properties in separate columns
        # EXAMPLE: predicate    subject                         1                    2          3
        #                  0       r-57  Advanced Graph Databases  New York University  Fall 2024
        df_wide = df.pivot(index='subject', columns='predicate', values='object').reset_index()

        # Rename the columns, based on the passed name mapping, if any
        # EXAMPLE: predicate    subject             Course Title                 School   Semester
        #                 0        r-57   Advanced Graph Databases  New York University  Fall 2024
        if col_names:
            df_wide = df_wide.rename(columns=col_names)

        # Rename the "subject" column to be "uri"
        df_wide = df_wide.rename(columns={"subject": "uri"})

        # Now that the data frame is transformed, do the actual import
        return cls.import_pandas_nodes_NO_BATCH(df=df_wide, class_name=class_node, uri_namespace=None,
                                                datetime_cols=datetime_cols, int_cols=int_cols,
                                                extra_labels=extra_labels,
                                                report_frequency=report_frequency)



    @classmethod
    def import_json_data(cls, json_str: str, class_name: str, parse_only=False, provenance=None) -> Union[None, int, List[int]]:
        """
        Import the data specified by a JSON string into the database -
        but only the data that is described in the existing Schema;
        anything else is silently ignored.

        CAUTION: A "postorder" approach is followed: create subtrees first (with recursive calls), then create the root last;
        as a consequence, in case of failure mid-import, there's no top root, and there could be several fragments.
        A partial import might need to be manually deleted.
        TODO: maintain a list of all created nodes - so as to be able to delete them all in case of failure.

        :param json_str:    A JSON string representing (at the top level) an object or a list to import
        :param class_name:  Name of Schema class to use for the top-level element(s)
        :param parse_only:  Flag indicating whether to stop after the parsing (i.e. no database import)
        :param provenance:  Metadata (such as a file name) to store in the "source" attribute
                                of a special extra node ("Import Data")

        :return:
        """
        cls.debug_print(f"In import_json_data().  class_name: {class_name} | parse_only: {parse_only} | provenance: {provenance}")
        # Try to obtain Python data (which ought to be a dict or list) that corresponds to the passed JSON string
        try:
            python_data_from_json = json.loads(json_str)    # Turn the string (representing JSON data) into its Python counterpart;
                                                            # at the top level, it should be a dict or list
        except Exception as ex:
            raise Exception(f"Incorrectly-formatted JSON string. {ex}")

        #print("Python version of the JSON file:\n", python_data_from_json)     # A dictionary

        if parse_only:
            return      # Nothing else to do

        return cls.create_data_nodes_from_python_data(python_data_from_json, class_name, provenance)



    @classmethod
    def create_data_nodes_from_python_data(cls, data, class_name: str, provenance=None) -> [int]:
        """
        Import the data specified by the "data" python structure into the database -
        but only the data that is described in the existing Schema;
        anything else is silently ignored.
        For additional notes, see import_json_data()

        :param data:        A python dictionary or list, with the data to import
        :param class_name:  The name of the Schema Class for the root node(s) of the imported data
        :param provenance:  Optional string to be stored in a "source" attribute
                                in a special "Import Data" node for metadata about the import

        :return:            List (possibly empty) of internal database ID's of the root node(s) created

        TODO:   * The "Import Data" Class must already be in the Schema; should automatically add it, if not already present
                * DIRECTION OF RELATIONSHIP (cannot be specified by Python dict/JSON)
                * LACK OF "Import Data" node (ought to be automatically created if needed)
                * LACK OF "BA" (or "DATA"?) labels being set
                * INABILITY TO LINK TO EXISTING NODES IN DBASE (try using: "uri": some_int  as the only property in nodes to merge)
                * OFFER AN OPTION TO IGNORE BLANK STRINGS IN ATTRIBUTES
                * INTERCEPT AND BLOCK IMPORTS FROM FILES ALREADY IMPORTED
                * issue some report about any part of the data that doesn't match the Schema, and got silently dropped
        """

        # Create a special `Import Data` node for the metadata of the import
        import_metadata = {}
        if provenance:
            import_metadata["source"] = provenance

        metadata_neo_id = cls.create_data_node(class_node="Import Data", properties=import_metadata)

        # Store the import date in the node with the metadata
        # Note: this is done as a separate step, so that the attribute will be a DATE ("LocalDate") field, not a text one
        q = f'''
            MATCH (n :`Import Data`) WHERE id(n) = {metadata_neo_id}
            SET n.date = date()
            '''
        cls.db.update_query(q)

        # TODO: catch Exceptions, and store the status and error message on the `Import Data` node;
        #       in particular, add "Import Data" to the Schema if not already present

        cache = SchemaCache()        # All needed Schema-related data will be automatically queried and cached here
        cls.debug_print("***************************** cache initialized ***************************** ")

        if type(data) == dict:      # If the top-level Python data structure is a dictionary
            # Create a single tree
            cls.debug_print("Top-level structure of the data to import is a Python dictionary")
            # Perform the import
            root_neo_id = cls.create_tree_from_dict(data, class_name, cache=cache) # This returns a Neo4j ID, or None

            if root_neo_id is None:
                cls.debug_print("None returned by create_tree_from_dict()")
                return []               # Zero new nodes were imported
            else:
                cls.debug_print(f"***Linking import node (Neo4j ID={metadata_neo_id}) with "
                                f"data root node (Neo4j ID={root_neo_id}), thru relationship `imported_data`")
                # Connect the root of the import to the metadata node
                cls.add_data_relationship(from_id=metadata_neo_id, to_id=root_neo_id, rel_name="imported_data")
                return [root_neo_id]

        elif type(data) == list:         # If the top-level Python data structure is a list
            # Create multiple unconnected trees
            cls.debug_print("Top-level structure of the data to import is a list")
            node_id_list = cls.create_trees_from_list(data, class_name, cache=cache)  # This returns a list of Neo4j ID's

            for root_uri in node_id_list:
                cls.debug_print(f"***Linking import node (uri={metadata_neo_id}) with "
                                f"data root node (Neo4j ID={root_uri}), thru relationship `imported_data`")
                # Connect the root of the import to the metadata node
                cls.add_data_relationship(from_id=metadata_neo_id, to_id=root_uri, rel_name="imported_data")

            return node_id_list

        else:                           # If the top-level data structure is neither a list nor a dictionary
            raise Exception(f"The top-level structure is neither a list nor a dictionary; instead, it's {type(data)}")



    @classmethod
    def create_tree_from_dict(cls, d: dict, class_name: str, level=1, cache=None) -> Union[int, None]:
        """
        Add a new data node (which may turn into a tree root) of the specified Class,
        with data from the given dictionary:
            1) literal values in the dictionary are stored as attributes of the node, using the keys as names
            2) other values (such as dictionaries or lists) are recursively turned into subtrees,
               linked from the new data node through outbound relationships using the dictionary keys as names

        Return the Neo4j ID of the newly created root node,
        or None is nothing is created (this typically arises in recursive calls that "skip subtrees")

        IMPORTANT:  any part of the data that doesn't match the Schema,
                    gets silently dropped.  TODO: issue some report about anything that gets dropped

        EXAMPLES:
        (1) {"state": "California", "city": "Berkeley"}
            results in the creation of a new node, with 2 attributes, named "state" and "city"

        (2) {"name": "Julian", "address": {"state": "California", "city": "Berkeley"}}
            results in the creation of 2 nodes, namely the tree root (with a single attribute "name"), with
            an outbound link named "address" to another node (the subtree) that has the "state" and "city" attributes

        (3) {"headquarter_state": [{"state": "CA"}, {"state": "NY"}, {"state": "FL"}]}
            results in the creation of a node (the tree root), with no attributes, and 3 links named "headquarter_state" to,
            respectively, 3 nodes - each of which containing a "state" attribute

        (4) {"headquarter_state": ["CA", "NY", "FL"]}
            similar to (3), above, but the children nodes will use the default attribute name "value"

        :param d:           A dictionary with data from which to create a tree in the database
        :param class_name:  The name of the Schema Class for the root node(s) of the imported data
        :param level:       The level of the recursive call (used for debug printing)
        :param cache:       Object of type SchemaCache
        :return:            The Neo4j ID of the newly created node,
                                or None is nothing is created (this typically arises in recursive calls that "skip subtrees")
        """
        assert cache is not None, "NeoSchema.create_tree_from_dict(): the argument `cache` cannot be None"
        assert type(d) == dict, f"NeoSchema.create_tree_from_dict(): the argument `d` must be a dictionary (instead, it's {type(d)})"

        indent_spaces = level*4
        indent_str = " " * indent_spaces        # For debugging: repeat a blank character the specified number of times
        cls.debug_print(f"{indent_str}{level}. ~~~~~:")

        class_internal_id = cls.get_class_internal_id(class_name=class_name)

        cls.debug_print(f"{indent_str}Importing data dictionary, using class `{class_name}` (with internal id {class_internal_id})")

        # Determine the properties and relationships declared in (allowed by) the Schema
        #cached_data = cache_old.get_class_cached_data(class_name)
        #declared_outlinks = cached_data['out_links']
        out_neighbors_dict = cache.get_cached_class_data(class_internal_id, request="out_neighbors")
        declared_outlinks = list(out_neighbors_dict)        # Extract keys from dict
        cls.debug_print(f"{indent_str}declared_outlinks: {declared_outlinks}")


        #declared_properties = cached_data['properties']
        declared_properties = cache.get_cached_class_data(class_internal_id, request="class_properties")
        cls.debug_print(f"{indent_str}declared_properties: {declared_properties}")

        cls.debug_print(f"{indent_str}Input is a dict with {len(d)} keys: {list(d.keys())}")
        node_properties = {}
        children_info = []          # A list of pairs (Neo4j ID value, relationship name)

        skipped_properties = []
        skipped_relationships = []

        # Loop over all the dictionary entries
        for k, v in d.items():
            debug_info = f"{indent_str}*** KEY-> VALUE: {k} -> {v}"
            cls.debug_print(debug_info, trim=True)      # Abridge the info line if excessively long

            if v is None:
                cls.debug_print(f"{indent_str}Disregarding attribute (`{k}`) that has a None value")
                skipped_properties.append(k)
                continue

            if cls.db.is_literal(v):
                cls.debug_print(f"{indent_str}(key: `{k}`) Processing a literal of type {type(v)} ({v})",
                                trim=True)
                if k not in declared_properties:    # Check if the Property from the data is in the schema
                    cls.debug_print(f"{indent_str}Disregarding this unexpected attribute: `{k}`")
                    skipped_properties.append(k)
                    continue
                else:
                    node_properties[k] = v                  # Save attribute for use when the node gets created
                    cls.debug_print(f"{indent_str}Buffered properties for the new node so far: {node_properties}",
                                    trim=True)

            elif type(v) == dict:
                cls.debug_print(f"{indent_str}(key: `{k}`) Processing a dictionary (with {len(v)} keys)")

                if k not in declared_outlinks:       # Check if the Relationship from the data is in the schema
                    cls.debug_print(f"{indent_str}Disregarding this unexpected relationship: `{k}`")
                    skipped_relationships.append(k)
                    continue

                cls.debug_print(f"{indent_str}Examining the relationship `{k}`...")

                try:
                    # Locate which Class one finds in the Schema when following the relationship name stored in k
                    #subtree_root_class_name = cached_data['out_neighbors'][k]
                    subtree_root_class_name = out_neighbors_dict[k]
                    cls.debug_print(f"{indent_str}...the relationship `{k}` leads to the following Class: {subtree_root_class_name}")
                except Exception as ex:
                    cls.debug_print(f"{indent_str}Disregarding. {ex}")
                    skipped_relationships.append(k)
                    continue

                # Recursive call
                cls.debug_print(f"{indent_str}Making recursive call to process the above dictionary...")
                new_node_neo_id = cls.create_tree_from_dict(d=v, class_name=subtree_root_class_name, level=level + 1, cache=cache)

                if new_node_neo_id is not None:     # If a subtree actually got created
                    children_info.append( (new_node_neo_id, k) )    # Save relationship name (in k) for use when the node gets created
                    cls.debug_print(f"{indent_str}Buffered relationships for the new node so far: {children_info}")
                else:
                    cls.debug_print(f"{indent_str}No subtree was returned; so, skipping over this key (`{k}`)")

            elif type(v) == list:
                cls.debug_print(f"{indent_str}(key: `{k}`) Processing a list (with {len(v)} elements):")

                if k not in declared_outlinks:       # Check if the Relationship from the data is in the schema
                    cls.debug_print(f"{indent_str}Disregarding this unexpected relationship: `{k}`")
                    skipped_relationships.append(k)
                    continue

                if len(v) == 0:
                    cls.debug_print(f"{indent_str}The list is empty; so, ignoring it")
                    continue

                cls.debug_print(f"{indent_str}Examining the relationship `{k}`...")

                try:
                    # Locate which Class one finds in the Schema when following the relationship name stored in k
                    #subtree_root_class_name = cached_data['out_neighbors'][k]
                    subtree_root_class_name = out_neighbors_dict[k]
                    cls.debug_print(f"{indent_str}...the relationship `{k}` leads to the following Class: {subtree_root_class_name}")
                except Exception as ex:
                    cls.debug_print(f"{indent_str}Disregarding. {ex}")
                    skipped_relationships.append(k)
                    continue

                # Recursive call
                cls.debug_print(f"{indent_str}Making recursive call to process the above list...")
                new_node_id_list = cls.create_trees_from_list(l=v, class_name=subtree_root_class_name, level=level + 1, cache=cache)
                for child_id in new_node_id_list:
                    children_info.append( (child_id, k) )

            else:
                raise Exception(f"Unexpected type: {type(v)}")

        # End of loop over all the dictionary entries

        # A "postorder" approach is followed: the subtrees were created first (with recursive calls);
        # now, finally CREATE THE NEW NODE, the ROOT, with its attributes
        # and links to the previously-created children (the roots of all the sub-trees)
        if len(node_properties) == 0 and len(children_info) == 0:
            cls.debug_print(f"{indent_str}Skipping creating node of class `{class_name}` that has no properties and no children")
            return None   # Using None to indicate "skipped node/subtree"
        else:
            links = [{"internal_id": child[0], "rel_name": child[1], "rel_dir": "OUT"}
                            for child in children_info]
            # Note: an internal database ID is returned by the next call
            '''
            return cls.add_data_node_with_links(class_internal_id=class_internal_id,
                                                labels=class_name,
                                                properties=node_properties,
                                                links=links,
                                                assign_uri=False)
            '''
            return cls.create_data_node(class_node=class_internal_id,
                                        properties=node_properties,
                                        links=links)



    @classmethod
    def create_trees_from_list(cls, l: list, class_name: str, level=1, cache=None) -> [int]:
        """
        Add a set of new data nodes (the roots of the trees), all of the specified Class,
        with data from the given list.
        Each list elements MUST be a literal, or dictionary or a list:
            - if a literal, it first gets turned into a dictionary of the form {"value": literal_element};
            - if a dictionary, it gets processed by create_tree_from_dict()
            - if a list, it generates a recursive call

        Return a list of the internale database ID of the newly created nodes.

        IMPORTANT:  any part of the data that doesn't match the Schema,
                    gets silently dropped.  TODO: issue some report about that

        EXAMPLE:
            If the Class is named "address" and has 2 properties, "state" and "city",
            then the data:
                    [{"state": "California", "city": "Berkeley"},
                     {"state": "Texas", "city": "Dallas"}]
            will give rise to 2 new data nodes with label "address", and each of them having a "SCHEMA"
            link to the shared Class node.

        :param l:           A list of data from which to create a set of trees in the database
        :param class_name:  The name of the Schema Class for the root node(s) of the imported data
        :param level:       The level of the recursive call (used for debug printing)
        :param cache:       Object of type SchemaCache

        :return:            A list of the Neo4j values of the newly created nodes (each of which
                                might be a root of a tree)
        """
        assert type(l) == list, f"NeoSchema.create_trees_from_list(): the argument `l` must be a list (instead, it's {type(l)})"
        assert cache is not None, "NeoSchema.create_trees_from_list(): the argument `cache` cannot be None"

        #assert cls.class_name_exists(class_name), \
                #f"The value passed for the argument `class_name` ({class_name}) is not a valid Class name"

        indent_spaces = level*4
        indent_str = " " * indent_spaces        # For debugging: repeat a blank character the specified number of times
        cls.debug_print(f"{indent_str}{level}. ~~~~~:")

        cls.debug_print(f"{indent_str}Input is a list with {len(l)} items")

        list_of_root_neo_ids = []

        # Process each element of the list, in turn
        for i, item in enumerate(l):
            cls.debug_print(f"{indent_str}Processing the {i}-th list element...")
            if cls.db.is_literal(item):
                item_as_dict = {"value": item}
                new_node_id = cls.create_tree_from_dict(d=item_as_dict, class_name=class_name, level=level + 1, cache=cache)
                if new_node_id is not None:                      # If a subtree actually got created
                    list_of_root_neo_ids.append(new_node_id)

            elif type(item) == dict:
                new_node_id = cls.create_tree_from_dict(d=item, class_name=class_name, level=level + 1, cache=cache)
                if new_node_id is not None:                     # If a subtree actually got created
                    list_of_root_neo_ids.append(new_node_id)

            elif type(item) == list:
                cls.debug_print(f"{indent_str}Making recursive call")
                new_node_id_list = cls.create_trees_from_list(l=item, class_name=class_name, level=level + 1, cache=cache)   # Recursive call
                list_of_root_neo_ids += new_node_id_list        # Merge of lists

            else:
                raise Exception(f"NeoSchema.create_trees_from_list(): Unexpected type in list item: {type(item)}")


        return list_of_root_neo_ids





    #####################################################################################################

    '''                               ~   IMPORT/EXPORT SCHEMA   ~                                    '''

    def ________IMPORT_EXPORT_SCHEMA________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################


    @classmethod
    def create_schema_from_sample_data(cls, match):
        """
        Create a Schema from sample data node, for example as created with the Arrow app
        TODO: NOT YET COMPLETED.  NOT FOR PRODUCTION

        :param match:   # Maybe allow a label, or range of ID's, instead
        :return:
        """
        q = '''MATCH (from)-[rel]->(to) 
        RETURN  labels(from) AS from_node, 
                type(rel) AS link_name, 
                properties(rel) AS link_props, 
                labels(to) AS to_node
        '''    # TODO: need to add a clause to this.  Maybe allow a label, or range of ID's (also for the match argument of this method)
    
        res = cls.db.query(q)
    
        all_nodes = cls.db.get_nodes(match, return_labels=True)
        for node in all_nodes:
            labels = node['neo4j_labels']
            class_name = labels[0]
            print(f"ENTITY: `{class_name}`")
            properties = list(node)
            properties.remove('neo4j_labels')
            print("PROPERTIES:", properties)
            print()
            cls.create_class_with_properties(name=class_name, properties=properties, strict=False)
    
    
        for link in res:
            # Unpack
            (from_node, link_name, link_props, to_node) = [link.get(key) for key in ("from_node", "link_name", "link_props", "to_node")]
            from_class = from_node[0]
            to_class = to_node[0]
            link_props_names = list(link_props)
            print(f"\nRelationship from `{from_class} to `{to_class}` named `{link_name}`")
            if link_props:
                print("    with Properties:", link_props_names)
                cls.create_class_relationship(from_class=from_class, to_class=to_class,
                                                    rel_name=link_name, use_link_node=True)  # Will need to pass the link_props_names
            else:
                cls.create_class_relationship(from_class=from_class, to_class=to_class,
                                                    rel_name=link_name, use_link_node=False)



    @classmethod
    def export_schema(cls) -> {}:
        """
        Export all the Schema nodes and relationships as a JSON string.

        IMPORTANT:  APOC must be activated in the database, to use this function.
                    Otherwise it'll raise an Exception

        :return:    A dictionary specifying the number of nodes exported,
                    the number of relationships, and the number of properties,
                    as well as a "data" field with the actual export as a JSON string
        """
        #TODO: unit testing

        # Any Class or Property node
        nodes_query = "MATCH (n) WHERE (n:CLASS OR n:PROPERTY)"

        # Any relationship from a Class to another Class or to a Property
        rels_query = "MATCH (c:CLASS)-[r]->(n) WHERE (n:CLASS OR n:PROPERTY)"

        return cls.db.export_nodes_rels_json(nodes_query, rels_query)





    #####################################################################################################

    '''                                       ~   URI'S   ~                                           '''

    def ________URI________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################


    @classmethod
    def is_valid_uri(cls, uri :str) -> bool:
        """
        Check the validity of the passed uri.
        If the uri belongs to a Schema node, a tighter check can be performed with is_valid_schema_uri()

        :param uri: A string with a value that is expected to be a uri of a node
        :return:    True if the passed uri has a valid value, or False otherwise
        """
        # TODO: also verify that the string isn't just a group of blanks
        if type(uri) == str and uri != "":
            return True

        return False


    @classmethod
    def is_valid_schema_uri(cls, schema_uri :str) -> bool:
        """
        Check the validity of the passed Schema uri.
        It should be of the form "schema-n" for some integer n
        To check the validity of the uri of a Data node rather than a Schema node,
        use is_valid_uri() instead

        :param schema_uri:  A string with a value that is expected to be a uri of a Schema node
        :return:            True if the passed uri has a valid value, or False otherwise
        """
        if type(schema_uri) != str:
            return False

        # Check that the string starts with "schema-"
        if schema_uri[:7] != "schema-":
            return False

        # Check that the portion after "schema-" represents an integer
        try:
            int(schema_uri[7:])
        except:
            return False

        return True



    @classmethod
    def assign_uri(cls, internal_id :int, namespace="data_node") -> str:
        """
        Given an existing Data Node that lacks a URI value, assign one to it (and save it in the database.)
        If a URI value already exists on the node, an Exception is raised

        :param internal_id: Internal database ID to identify a Data Node tha currently lack a URI value
        :param namespace:   A string used to maintain completely separate groups of auto-increment values;
                                leading/trailing blanks are ignored
        :return:            A string with the newly-assigned URI value
        """
        #TODO: pytest

        assert cls.data_node_exists(internal_id), \
            f"assign_uri(): no Data Node with an internal ID of {internal_id} was found"

        new_uri = cls.reserve_next_uri(namespace=namespace)
        q = f'''
            MATCH (n) 
            WHERE id(n) = {internal_id}  AND n.uri IS NULL
            SET n.uri = "{new_uri}" 
            '''
        #cls.db.debug_query_print(q)

        stats = cls.db.update_query(q)
        number_properties_set = stats.get("properties_set", 0)
        assert number_properties_set == 1, \
            f"assign_uri(): unable to set a value for the `uri` property of " \
            f"the Data Node with an internal ID of {internal_id}  (perhaps it already has a uri?)"

        return new_uri



    @classmethod
    def create_namespace(cls, name :str, prefix="", suffix="") -> None:
        """
        Set up a new namespace for URI's.

        :param name:    A string used to maintain completely separate groups of auto-increment values;
                            leading/trailing blanks are ignored
        :param prefix:  (OPTIONAL) String to prefix to the auto-increment number;
                            it will be stored in the database
        :param suffix:  (OPTIONAL) String to suffix to the auto-increment number;
                            it will be stored in the database
        :return:        None
        """
        assert type(name) == str, \
            f"create_namespace(): the argument `name` must be a string.  " \
            f"The value passed was of type {type(name)}"

        assert name != "", \
            f"create_namespace(): the argument `name` cannot be an empty string"

        assert not cls.namespace_exists(name), \
            f"create_namespace(): a namespace called `{name}` already exists"

        properties={"namespace": name, "next_count": 1}
        if prefix:
            properties["prefix"] = prefix
        if suffix:
            properties["suffix"] = suffix

        cls.db.create_node(labels="Schema Autoincrement", properties=properties)



    @classmethod
    def namespace_exists(cls, name :str) -> bool:
        """
        Return True if the specified namespace already exists, or False otherwise

        :param name:
        :return:
        """
        return cls.db.exists_by_key(labels="Schema Autoincrement",
                                    key_name="namespace", key_value=name)



    @classmethod
    def reserve_next_uri(cls, namespace="data_node", prefix="", suffix="") -> str:
        """
        Generate and reserve a URI (or fragment thereof, aka "token"),
        using the given namespace and, optionally the given prefix and/or suffix.

        The middle part of the generated URI is a unique auto-increment value
        (separately maintained for various groups, or "namespaces").

        If the requested namespace is not the default one, make sure to first create it
        with create_namespace()

        If no prefix or suffix is specified, use the values provided when the namespace
        was first created.

        EXAMPLES:   reserve_next_uri("Document", "doc.", ".new") might produce "doc.3.new"
                    reserve_next_uri("Image", prefix="i-") might produce "i-123"

        IMPORTANT: Prefixes and suffixes only need to be passed when first creating a new namespace;
                   if they're passed in here, they over-ride their stored counterparts.

        Note that the returned uri is de-facto "permanently reserved" on behalf of the calling function,
        and can't be used by any other competing thread, thus avoid concurrency problems (racing conditions)

        :param namespace:   A string used to maintain completely separate groups of auto-increment values;
                                leading/trailing blanks are ignored.
                                It must exist, unless the default value is accepted (in which case,
                                it gets created as needed)
        :param prefix:      (OPTIONAL) String to prefix to the auto-increment number.
                                If it's the 1st call for the given namespace, store it in the database;
                                otherwise, if a value is passed, use it to over-ride the stored one
        :param suffix:      (OPTIONAL) String to suffix to the auto-increment number
                                If it's the 1st call for the given namespace, store it in the database;
                                otherwise, if a value is passed, use it to over-ride the stored one

        :return:            A string (with the prefix and suffix from above) that contains an integer
                                that is a unique auto-increment for the specified namespace
                                (starting with 1); it's ready-to-use and "reserved", i.e. could be used
                                at any future time
        """
        # TODO: provide a function reserve_next_uri_GROUP()


        assert (type(prefix) == str) or (prefix is None), \
            f"reserve_next_uri(): the argument `prefix` must be a string or None; " \
            f"value passed was of type {type(prefix)}"
        assert (type(suffix) == str) or (suffix is None), \
            f"reserve_next_uri(): the argument `suffix` must be a string or None;" \
            f" value passed was of type {type(suffix)}"

        if namespace=="data_node":
            if not cls.namespace_exists("data_node"):
                cls.create_namespace("data_node", prefix=prefix, suffix=suffix)

        (autoincrement_to_use, stored_prefix, stored_suffix) = cls.advance_autoincrement(namespace)

        if not prefix:      # Use the database value, if not passed as argument
            prefix = stored_prefix
        if not suffix:      # Use the database value, if not passed as argument
            suffix = stored_suffix

        # Assemble the URI
        uri = f"{prefix}{autoincrement_to_use}{suffix}"
        #print(f"***++ GENERATING NEW URI: `{uri}`")

        return uri



    @classmethod
    def advance_autoincrement(cls, namespace :str, advance=1) -> (int, str, str):
        """
        Utilize an ATOMIC database operation to both read AND advance the autoincrement counter,
        based on a (single) node that:
            1) contains the label `Schema Autoincrement`
            2) and also contains, as an attribute, the desired namespace (group);
        if no such node exists (for example, after a new installation), an Exception is  raised.

        An ATOMIC database operation is utilized to both read AND advance the autoincrement counter,
        based on a (single) node with label `Schema Autoincrement`
        as well as an attribute indicating the desired namespace (group)

        Note that the returned number (or the last of an implied sequence of numbers, if advance > 1)
        is de-facto "permanently reserved" on behalf of the calling function,
        and can't be used by any other competing thread, thus avoid concurrency problems (racing conditions)

        :param namespace:   A string used to maintain completely separate groups of auto-increment values;
                                leading/trailing blanks are ignored
        :param advance:     Normally, auto-increment advances by 1 unit, but a different positive integer
                                may be used to "reserve" a group of numbers in the above namespace

        :return:            An integer that is a unique auto-increment for the specified namespace
                                (starting with 1); it's ready-to-use and "reserved", i.e. could be used
                                at any future time.
                                If advance > 1, the first of the reserved numbers is returned
        """
        assert type(namespace) == str, \
            "advance_autoincrement(): the argument `namespace` is required and must be a string"

        namespace = namespace.strip()   # Zap leading/trailing blanks

        assert namespace != "", \
            "advance_autoincrement(): the argument `namespace` must be a non-empty string"

        assert type(advance) == int, \
            "advance_autoincrement(): the argument `advance` is required and must be an integer"
        assert advance >= 1, \
            "advance_autoincrement(): the argument `advance` must be an integer >= 1"


        # Attempt to retrieve a `Schema Autoincrement` node for our given namespace (it might be absent)
        # Notice the DATA LOCK to protect against multiple concurrent calls
        #   Info: https://neo4j.com/docs/java-reference/4.4/transaction-management/
        q = f'''
            MATCH (n: `Schema Autoincrement` {{namespace: $namespace}})
            SET n._LOCK_ = true
            SET n.next_count = n.next_count + {advance}
            REMOVE n._LOCK_
            RETURN n.next_count AS next_count, n.prefix AS stored_prefix, n.suffix AS stored_suffix
            '''
        result = cls.db.query(q, data_binding={"namespace": namespace}, single_row=True)

        # If no Autoincrement node found, raise an Exception
        assert result, \
            f"reserve_next_uri(): no namespace named '{namespace}' was found.  " \
            f"Make sure to first create the namespace with a call to create_namespace()"

        # Unpack the dictionary of data from the Autoincrement node
        (next_count, stored_prefix, stored_suffix) = [result.get(key) for key in ("next_count", "stored_prefix", "stored_suffix")]
        # Note that stored_prefix and stored_suffix will be None if not found in the database

        if stored_prefix is None:
            stored_prefix = ""

        if stored_suffix is None:
            stored_suffix = ""

        autoincrement_to_use = next_count - advance

        return (autoincrement_to_use, stored_prefix, stored_suffix)



    @classmethod
    def _next_available_schema_uri(cls) -> str:
        """
        Return the next available uri for nodes managed by this class.
        For unique uri's to use on Data Nodes, use reserve_next_uri() instead

        :return:     A string based on unique auto-increment values, used for Schema nodes
        """
        if not cls.namespace_exists("schema_node"):
            cls.create_namespace("schema_node")

        return cls.reserve_next_uri(namespace="schema_node", prefix="schema-")



    @classmethod
    def assign_namespace_to_class(cls, class_name :str, namespace :str) -> None:
        """
        Link up a Class node to the node of a namespace to be used for data nodes of that Class

        :param class_name:
        :param namespace:
        :return:            None
        """
        #TODO: pytest

        #TODO: verify that the match is unique
        q = '''
            MATCH (c:CLASS {name: $class_name}),
            (a:`Schema Autoincrement` {namespace: $namespace})
            MERGE (c)-[:HAS_URI_GENERATOR]->(a) 
            RETURN c, a
            '''

        cls.db.query(q, data_binding={"class_name": class_name, "namespace": namespace})



    @classmethod
    def lookup_class_namespace(cls, class_name :str) -> Union[str, None]:
        """
        Look up the namespace, if any, assigned to the given Class,
        by means of a standard "HAS_URI_GENERATOR" relationship.
        If not found, return None

        :param class_name:  Name of a Schema Class
        :return:
        """
        # TODO: Pytest

        # Check if a namespace has been assigned to the given Class
        class_id = NeoSchema.get_class_internal_id(class_name)
        namespace_links = NeoSchema.follow_links(class_name="CLASS", node_id=class_id, link_name="HAS_URI_GENERATOR",
                                                 properties="namespace")
        #print("lookup_class_namespace() - namespace_links: ", namespace_links)
        if len(namespace_links) == 1:
            return namespace_links[0]
        else:
            return None



    @classmethod
    def generate_uri(cls, class_name :str) -> str:
        """
        Use, as appropriate for the given Class,
        a specific namespace - or the general data node namespace - to generate a URI
        to use on a newly-create Data Node

        :param class_name:  Name of a Schema Class
        :return:
        """
        # TODO: Pytest

        # Check if a specific namespace has been assigned to the given Class
        namespace = cls.lookup_class_namespace(class_name)

        if namespace:
            print(f"generate_uri(): Using namespace '{namespace}'")
            return cls.reserve_next_uri(namespace=namespace)
        else:
            print(f"generate_uri(): Using default datanodes namespace")
            return cls.reserve_next_uri()





    #####################################################################################################

    '''                                   ~   UTILITIES   ~                                           '''

    def ________UTILITIES________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################

    @classmethod
    def debug_print(cls, info: str, trim=False) -> None:
        """
        If the class' property "debug" is set to True,
        print out the passed info string,
        optionally trimming it, if too long

        :param info:
        :param trim:    (OPTIONAL) Flag indicating whether to only print a shortened version
        :return:        None
        """
        if cls.debug:
            if trim:
                info = cls.db.debug_trim(info)

            print(info)



    @classmethod
    def _prepare_data_node_labels(cls, class_name :str, extra_labels=None) -> [str]:
        """
        Return a list of labels to use on a Data Node,
        given its Schema Class (whose name is always used as one of the labels)
        and an optional list of extra labels.

        The given Class name must be valid, but the Class does not need to exist yet.

        Any leading/trailing blanks in the extra labels are removed.  Duplicate names are ignored.

        :param class_name:      The name of a Schema Class
        :param extra_labels:    [OPTIONAL] Either a string, list/tuple of strings
        :return:
        """
        cls.assert_valid_class_name(class_name)

        labels = [class_name]     # Start with the Class name as the first label label

        if extra_labels is None:
            return labels   # The Class name will be used as the only label


        # If we get thus far, a value was provided for extra_labels

        assert isinstance(extra_labels, (str, list, tuple)), \
            "NeoSchema._prepare_labels(): argument `extra_labels`, " \
            "if passed, must be a string, or list/tuple of strings"

        if (t := type(extra_labels)) == str:
            extra_labels = [extra_labels]
        else:
            assert (t == list) or (t == tuple), \
                "NeoSchema._prepare_labels(): argument `extra_labels`, " \
                "if passed, must be a string, or list/tuple of strings"

        # extra_labels is now a list or tuple

        for l in extra_labels:
            clean_l = l.strip()
            if clean_l not in labels:
                labels.append(clean_l)

        return labels



    @classmethod
    def prepare_match_cypher_clause(cls, node_id=None, id_key=None, class_name=None) -> (str, str, dict):
        """
        Given some specs on locating data nodes, prepare a Cypher clause and data-binding dict to match those nodes.

        The dummy name used in the clause is "dn"  (for data node).  The "WHERE" is included.

        At least one of the arguments must be specified.

        An implicit AND is performed, in case of multiple specifications

        :param node_id:     [OPTIONAL] Either an internal database ID or a key value,
                                depending on the value of `id_key`
        :param id_key:      [OPTIONAL] Name of a key used to identify the data node(s) with the `node_id` value;
                                for example, "uri".
                                If blank, then the `node_id` is taken to be the internal database ID
        :param class_name:  [OPTIONAL] The name of a Schema Class

        :return:            A triplet:
                                (1) label to use on the node
                                (2) string with Cypher clause (including the "WHERE") to match the node(s)
                                    with the specified requirements
                                (3) data-binding dictionary to use with the above Cypher
        """

        clause_list = []        # Prepare the clause a part of a Cypher query
        data_binding = {}


        if id_key is None:
            # `node_id` is taken to be the internal database ID
            if node_id is not None:
                # Match by internal database ID
                CypherUtils.assert_valid_internal_id(node_id)
                clause_list.append("id(dn) = $node_id")
                data_binding["node_id"] = node_id
        else:
            assert node_id is not None, \
                    f"_prepare_match_cypher_clause(): if argument `id_key` is provided, then " \
                    f"`node_id` must be present, too"
            assert type(id_key) == str, \
                    f"_prepare_match_cypher_clause(): " \
                    f"argument `id_key` must be None or a string; " \
                    f"instead, it is of type {type(node_id)}"
            data_binding["node_id"] = node_id
            clause_list.append(f"dn.`{id_key}` = $node_id")


        if class_name is not None:
            cls.assert_valid_class_name(class_name)
            clause_list.append("dn.`_SCHEMA` = $class_name")
            data_binding["class_name"] = class_name

        assert clause_list != [], \
            f"_prepare_match_cypher_clause(): at least one of the arguments must be specified"

        clause = "WHERE " + (" AND ").join(clause_list)

        label = "" if class_name is None else f":`{class_name}`"

        return (label, clause, data_binding)







######################################################################################################
######################################################################################################

class SchemaCache:
    """
    Cached by the Classes' internal database ID

    Used to improve the efficiency of methods that heavily interact with the Schema,
    such as JSON imports.

    Maintain a Python dictionary, whose keys are the internal database IDs of Schema Class nodes.
    Generally, it will be a subset of interest from all the Classes in the database.

    Note: this class gets instantiated, so that it's a local variable and won't cause
          trouble with multi-threading

    TODO:   add a "schema" argument to some NeoSchema methods that interact with the Schema,
            to provide an alternate manner of querying the Schema
            - as currently done by several method
    """
    def __init__(self):
        self._schema = {}   # The KEYS are the internal database IDs of the Schema Class nodes;
                            # the VALUES are dicts that contain the following keys:
                            #       1) "class_attributes"
                            #               EXAMPLE:  {'name': 'MY CLASS', 'schema_uri': '123', 'strict': False}

                            #       2) "class_properties"
                            #               EXAMPLE:  ["age", "gender", "weight"]

                            #       3) "out_neighbors"   [Note: "in_neighbors" not done for now]
                            #               EXAMPLE:  {'IS_ATTENDED_BY': 'doctor', 'HAS_RESULT': 'result'}


    def get_all_cached_class_data(self, class_id: int) -> dict:
        """
        Return all existed cached data for the specified Class

        :param class_id:    An integer with the database internal ID of the desired Class node
        :return:            A (possibly empty) dict with keys that may include
                                "class_attributes", "class_properties", "out_neighbors"
        """
        if class_id not in self._schema:
            # No cached data info already exists for this Class... so, create it
            self._schema[class_id] = {}

        return self._schema[class_id]



    def get_cached_class_data(self, class_id: int, request: str) -> Union[dict, List[str]]:
        """
        Return the requested data for the specified Class.

        If cached values are available, they get used;
        otherwise, they get queried, then cached and returned.

        If request == "class_attributes":
            return the attributes of the requested Class,
            i.e. a dictionary of all the Class node's attributes
            EXAMPLE:  {'name': 'MY CLASS', 'schema_uri': '123', 'strict': False}

        If request == "class_properties":
            return the properties of the requested Class,
            i.e. the  list of all the names of the Properties associated with the given Class
            EXAMPLE:  ["age", "gender", "weight"]

        If request == "out_neighbors":
            return a dictionary where the keys are the names of the outbound relationships from with the given Class,
            and the values are the names of the Classes on the other side of those relationships
            EXAMPLE:  {'IS_ATTENDED_BY': 'doctor', 'HAS_RESULT': 'result'}

        :param class_id:    An integer with the internal database ID of the desired Class node
        :param request:     A way to specify what to look up.
                                Permissible values: "class_attributes", "class_properties", "out_neighbors"
        :return:
        """
        assert request in ["class_attributes", "class_properties", "out_neighbors"], \
                "get_cached_class_data(): bad value for `request` argument.  Allowed values: " \
                "'class_attributes', 'class_properties', 'out_neighbors'"

        cached_data = self.get_all_cached_class_data(class_id)      # A dict

        if request == "class_attributes":
            if "class_attributes" not in cached_data:
                # The Class attributes hadn't been cached; so, retrieve them
                class_attributes = NeoSchema.get_class_attributes(class_id)
                cached_data["class_attributes"] = class_attributes

            return cached_data["class_attributes"]


        if request == "class_properties":
            if "class_properties" not in cached_data:
                # The Class properties hadn't been cached; so, retrieve them
                class_properties = NeoSchema.get_class_properties(class_node=class_id, include_ancestors=False)
                cached_data["class_properties"] = class_properties

            return cached_data["class_properties"]


        if request == "out_neighbors":
            if "out_neighbors" not in cached_data:
                # The outbound links haven't been cached; so, retrieve them
                cached_data["out_neighbors"] = NeoSchema.get_class_outbound_data(class_id, omit_instance=True)
                '''
                    A (possibly empty) dictionary,where the keys are the name of outbound relationships,
                    and the values are the names of the Class nodes on the other side of those links.
                    EXAMPLE: {'IS_ATTENDED_BY': 'doctor', 'HAS_RESULT': 'result'}
                '''

            return cached_data["out_neighbors"]
