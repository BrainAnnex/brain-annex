from neo4j.time import DateTime                             # To convert datetimes (and dates) between neo4j.time.DateTime and python
                                                            # TODO: all Neo4j-specific parts are being migrated to the InterGraph libraries
import neo4j.graph                                          # To check returned data types
from brainannex.cypher_utils import CypherUtils, CypherBuilder  # Helper classes
from brainannex import InterGraph                           # One of a family of classes, for different (versions) of graph databases;
                                                            #   make sure to pick the one for your database, in the "brainannex/__init__.py" file!
import math
import numpy as np
import pandas as pd
import pandas.core.dtypes.common
import json
import time
from typing import Union, List, Tuple


'''        
    ----------------------------------------------------------------------------------
    HISTORY and AUTHORS:
    
        GraphAccess was created, and is being maintained, primarily by Julian West,
        in the context of the BrainAnnex.org open-source project.
        For change log, see the "LIBRARIES" entries in https://brainannex.org/history
                
        Reverse chronological order:
               
        - Name changed to GraphAccess, from NeoAccess, in 2025, 
                to emphasize potential use with other graph databases besides Neo4j.
                The database-specific portions were extracted and separated 
                into a family of parent classes ("InterGraph"), one per supported database:
                currently supported are versions 4 and 5 of the Neo4j database
        
        - NeoAccess is a fork of NeoInterface; it started out in late 2021.
                This library was released independently on PyPI for a period of time, but
                eventually got re-incorporated into the broader library `brainannex`

        - NeoInterface (the parent library)
                was co-authored by Alexey Kuznetsov and Julian West in 2021,
                and is maintained by GSK pharmaceuticals
                with an Apache License 2.0 (https://github.com/GSK-Biostatistics/neointerface).
                NeoInterface is in part based on the earlier library Neo4jLiaison,
                as well as on a library developed by Alexey Kuznetsov.

        - Neo4jLiaison, an ancestor library now obsoleted, was authored by Julian West in 2020
                (https://github.com/BrainAnnex/neo4j-liaison)

    ----------------------------------------------------------------------------------
	MIT License

        Copyright (c) 2021-2025 Julian A. West

        This file is part of the "Brain Annex" project (https://BrainAnnex.org),
        though it's released independently.
        See "AUTHORS", above, for full credits.
	----------------------------------------------------------------------------------
'''


class GraphAccess(InterGraph):
    """
    IMPORTANT : this works with various versions of the Neo4j database (and, possibly,
                other graph databases), depending on the version of the underlying InterGraph library)

    High-level class to interface with the underlying graph database from Python.

    This class is a layer above its base class "InterGraph" (which is database-specific)
        and it provides a higher-level functionality for common database operations,
        such as lookup, creation, deletion, modification, import, etc.

    It makes use of separate helper classes (NOT meant for the end user) in the file cypher_utils.py
    """



    #####################################################################################################

    '''                                      ~   RETRIEVE DATA   ~                                            '''

    def ________RETRIEVE_DATA________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################


    def match(self, labels=None, internal_id=None,
              key_name=None, key_value=None, properties=None,
              clause=None, clause_binding=None,
              dummy_node_name="n") -> CypherBuilder:
        """
        Return a "CypherBuilder" object storing all the passed specifications;
        that object is expected as argument in various other functions in this library,
        in order to identify a node or group of nodes.

        IMPORTANT:  if internal_id is provided, all other conditions are DISREGARDED;
                    otherwise, an implicit AND applies to all the specified conditions.

        Note:   NO database operation is actually performed by this function.

        [Other names explored: identify(), preserve(), define_match(), locate(), choose() or identify()]

        ALL THE ARGUMENTS ARE OPTIONAL (no arguments at all means "match everything in the database")
        :param labels:      A string (or list/tuple of strings) specifying one or more Neo4j labels.
                                (Note: blank spaces ARE allowed in the strings)
                                EXAMPLES:  "cars"
                                            ("cars", "powered vehicles")
                            Note that if multiple labels are given, then only nodes with ALL of them will be matched;
                            at present, there's no way to request an "OR" operation

        :param internal_id: An integer with the node's internal database ID.
                                If specified, it OVER-RIDES all the remaining arguments [except for the labels (TODO: revisit this)]

        :param key_name:    A string with the name of a node attribute; if provided, key_value must be present, too
        :param key_value:   The required value for the above key; if provided, key_name must be present, too
                                Note: no requirement for the key to be primary

        :param properties:  A (possibly-empty) dictionary of property key/values pairs, indicating a condition to match.
                                EXAMPLE: {"gender": "F", "age": 22}

        :param clause:      Either None, OR a (possibly empty) string containing a Cypher subquery,
                            OR a pair/list (string, dict) containing a Cypher subquery and the data-binding dictionary for it.
                            The Cypher subquery should refer to the node using the assigned dummy_node_name (by default, "n")
                                IMPORTANT:  in the dictionary, don't use keys of the form "n_par_i",
                                            where n is the dummy node name and i is an integer,
                                            or an Exception will be raised - those names are for internal use only
                                EXAMPLES:   "n.age < 25 AND n.income > 100000"

        :param clause_binding:  EXAMPLE {"max_weight": 100} , if the clause is "n.weight < $max_weight"

        :param dummy_node_name: A string with a name by which to refer to the node (by default, "n");
                                only used if a `clause` argument is passed

        :return:            A python data dictionary, to preserve together all the passed arguments
        """
        #TODO: limitations include inability to do partial, or case-insensitive, matches for key_value.
        #      Maybe instead of specifying all arguments at once, it might be better to have individual methods
        #      for a "Cypher query builder"?
        return CypherBuilder(internal_id=internal_id,
                             labels=labels, key_name=key_name, key_value=key_value,
                             properties=properties,
                             clause=clause, clause_binding=clause_binding,
                             dummy_name=dummy_node_name)



    def get_nodes(self, match :int|str|CypherBuilder,
                  return_internal_id=False, return_labels=False, order_by=None, limit=None,
                  single_row=False, single_cell=""):
        """
        By default, it returns a list of the records (as dictionaries of ALL the key/value node properties)
        corresponding to all the Neo4j nodes specified by the given match data.
        However, if the flags "single_row" or "single_cell" are set, simpler data structures are returned

        :param match:           EITHER an integer or string with an internal database node id,
                                    OR a "CypherBuilder" object, as returned by match(), with data to identify a node or set of nodes

        :param return_internal_id:  Flag indicating whether to also include the internal database node ID in the returned data
                                    (using "internal_id" as its key in the returned dictionary)
        :param return_labels:   Flag indicating whether to also include the database label names in the returned data
                                    (using "node_labels" as its key in the returned dictionary)

        :param order_by:        (OPTIONAL) String with the key (field) name to order by, in ascending order
                                    Caution: lower and uppercase names are treated differently in the sort order
                                    TODO: standardize the case; provide support for DESC and for multiple fields

        :param limit:           (OPTIONAL) Integer to specify the maximum number of nodes returned
                                    TODO: provide support for SKIP

        :param single_row:      Meant in situations where only 1 node (record) is expected, or perhaps one wants to sample the 1st one.
                                    If True and a record or records were found, a dict will be returned instead of a list (containing the 1st record);
                                    if nothing was found, None will be returned [to distinguish it from a found record with no fields!]

        :param single_cell:     Meant in situations where only 1 node (record) is expected, and one wants only 1 specific field of that record.
                                If single_cell is specified, return the value of the field by that name in the first node
                                Note: this will be None if there are no results, or if the first (0-th) result row lacks a key with this name
                                TODO: test and give examples.  single_cell="name" will return result[0].get("name")

        :return:                If single_cell is specified, return the value of the field by that name in the first node.
                                If single_row is True, return a dictionary with the information of the first record (or None if no record exists)
                                Otherwise, return a (possibly-empty) list whose entries are dictionaries with each record's information
                                    (the node's attribute names are the keys)
                                    EXAMPLE: [  {"gender": "M", "age": 42, "condition_id": 3},
                                                {"gender": "M", "age": 76, "location": "Berkeley"}
                                             ]
                                    Note that ALL the attributes of each node are returned - and that they may vary across records.
                                    If the flag return_nodeid is set to True, then an extra key/value pair is included in the dictionaries,
                                            of the form     "internal_id": some integer with the Neo4j internal node ID
                                    If the flag return_labels is set to True, then an extra key/value pair is included in the dictionaries,
                                            of the form     "node_labels": [list of Neo4j label(s) attached to that node]
                                    EXAMPLE using both of the above flags:
                                        [  {"internal_id": 145, "node_labels": ["person", "client"], "gender": "M", "condition_id": 3},
                                           {"internal_id": 222, "node_labels": ["person"], "gender": "M", "location": "Berkeley"}
                                        ]
        """
        # TODO: provide an option to specify the desired fields

        # Unpack needed values from the Cypher builder
        (node, where, data_binding, dummy_node_name) = CypherUtils.assemble_cypher_blocks(match, caller_method="get_nodes")
        #print(node, where, data_binding, dummy_node_name)
        cypher = f"MATCH {node} {CypherUtils.prepare_where(where)} RETURN {dummy_node_name}"

        if order_by:
            cypher += f" ORDER BY n.{order_by}"

        if limit:
            cypher += f" LIMIT {limit}"


        # Note: the flatten=True takes care of returning just the fields of the matched node "n",
        #       rather than dictionaries indexes by "n"
        if return_internal_id and return_labels:
            result_list = self.query_extended(cypher, data_binding, flatten=True)
            # Note: query_extended() provides both 'internal_id' and 'node_labels'
        elif return_internal_id:    # but not return_labels
            result_list = self.query_extended(cypher, data_binding, flatten=True, fields_to_exclude=['node_labels'])
        elif return_labels:         # but not return_internal_id
            result_list = self.query_extended(cypher, data_binding, flatten=True, fields_to_exclude=['internal_id'])
        else:
            result_list = self.query_extended(cypher, data_binding, flatten=True, fields_to_exclude=['internal_id', 'node_labels'])

        # Deal with empty result lists
        if len(result_list) == 0:   # If no results were produced
            if single_row:
                return None             # representing a record not found (different from a record with no fields, which will be {})
            if single_cell:
                return None             # representing a field not found
            return []

        # Note: we already checked that result_list isn't empty
        if single_row:
            return result_list[0]

        if single_cell:
            return result_list[0].get(single_cell)

        return result_list



    def get_df(self, match: Union[int, CypherBuilder], order_by=None, limit=None) -> pd.DataFrame:
        """
        Similar to get_nodes(), but with fewer arguments - and the result is returned as a Pandas dataframe

        [See get_nodes() for more information about the arguments]

        :param match:       EITHER an integer with an internal database node id,
                                OR a "CypherBuilder" object, as returned by match(), with data to identify a node or set of nodes
        :param order_by:    Optional string with the key (field) name to order by, in ascending order
                                Note: lower and uppercase names are treated differently in the sort order
        :param limit:       Optional integer to specify the maximum number of nodes returned

        :return:            A Pandas dataframe
        """
        result_list = self.get_nodes(match=match, order_by=order_by, limit=limit)
        return pd.DataFrame(result_list)



    def get_node_internal_id(self, match :CypherBuilder) -> int|str:
        """
        Return the internal database ID of a SINGLE node identified by the "match" data
        created by a call to match().

        If not found, or if more than 1 found, an Exception is raised

        :param match:   A "CypherBuilder" object, as returned by match(), with data to identify a node or set of nodes
        :return:        An integer or string with the internal database ID of the located node,
                        if exactly 1 node is found; otherwise, raise an Exception
        """
        # Unpack needed values from the match dictionary
        (node, where, data_binding, _) = CypherUtils.assemble_cypher_blocks(match, caller_method="get_node_internal_id")

        q = f"MATCH {node} {CypherUtils.prepare_where(where)} RETURN id(n) AS INTERNAL_ID"

        result = self.query(q, data_binding, single_column="INTERNAL_ID")

        assert len(result) != 0, "get_node_internal_id(): node NOT found"

        assert len(result) <= 1, f"get_node_internal_id(): node NOT uniquely identified ({len(result)} matches found)"

        return result[0]



    def get_record_by_primary_key(self, labels: str, primary_key_name: str, primary_key_value,
                                  return_internal_id=False) -> Union[dict, None]:
        """
        Return the first (and it ought to be only one) record with the given primary key, and the optional label(s),
        as a dictionary of all its attributes.

        If more than one record is found, an Exception is raised.
        If no record is found, return None.

        :param labels:              A string or list/tuple of strings.  Use None if not to be included in search
        :param primary_key_name:    The name of the primary key by which to look the record up
        :param primary_key_value:   The desired value of the primary key
        :param return_internal_id:  If True, an extra entry is present in the dictionary, with the key "internal_id"

        :return:                    A dictionary, if a unique record was found; or None if not found
        """
        assert primary_key_name, \
            f"GraphAccess.get_record_by_primary_key(): the primary key name cannot be absent or empty (value: {primary_key_name})"

        assert primary_key_value is not None, \
            "GraphAccess.get_record_by_primary_key(): the primary key value cannot be None" # Note: 0 or "" could be legit

        match = self.match(labels=labels, key_name=primary_key_name, key_value=primary_key_value)
        #print(match)
        result = self.get_nodes(match=match, return_internal_id=return_internal_id)
        #print(result)
        if len(result) == 0:
            return None
        if len(result) > 1:
            raise Exception(f"GraphAccess.get_record_by_primary_key(): multiple records ({len(result)}) share the value (`{primary_key_value}`) in the primary key ({primary_key_name})")

        return result[0]



    def exists_by_key(self, labels: str, key_name: str, key_value) -> bool:
        """
        Return True if a node with the given labels and key_name/key_value exists, or False otherwise

        :param labels:      A string or list/tuple of strings
        :param key_name:    A string with the name of a node attribute
        :param key_value:   The desired value of the key_name attribute
        :return:            True if a node with the given labels and key_name/key_value exists,
                                or False otherwise
        """
        # TODO: test for multiple labels
        record = self.get_record_by_primary_key(labels, key_name, key_value)

        if record is None:
            return False
        else:
            return True



    def exists_by_internal_id(self, internal_id) -> bool:
        """
        Return True if a node with the given internal database ID exists, or False otherwise

        :param internal_id: An integer with a node's internal database ID
        :return:            True if a node with the given internal Neo4j exists, or False otherwise
        """
        q = f'''
        MATCH (n) 
        WHERE id(n) = {internal_id} 
        RETURN count(n) AS number_of_nodes
        '''

        result = self.query(q, single_cell="number_of_nodes")

        return result > 0



    def count_nodes(self, labels=None) -> int:
        """
        Compute and return the total number of nodes in the database, optionally matching the specified labels

        :param labels:  [OPTIONAL] String, or list/tuple of strings, with the desired node label(s)
        :return:        The number of nodes in the database (matching the labels, if specified)
        """
        #  TODO: test

        labels_str = CypherUtils.prepare_labels(labels)     # EXAMPLE: ":`my label`:`my other label`"

        q = f"MATCH (n {labels_str}) RETURN COUNT(n) AS number_nodes"

        return self.query(q, single_cell="number_nodes")



    def get_single_field(self, match: Union[int, CypherBuilder], field_name: str, order_by=None, limit=None) -> list:
        """
        For situations where one is fetching just 1 field,
        and one desires a list of the values of that field, rather than a dictionary of records.
        In other respects, similar to the more general get_nodes()

        :param match:       EITHER an integer with an internal database node id,
                                OR a "CypherBuilder" object, as returned by match(), with data to identify a node or set of nodes
        :param field_name:  A string with the name of the desired field (attribute)
        :param order_by:    see get_nodes()
        :param limit:       see get_nodes()

        :return:  A list of the values of the field_name attribute in the nodes that match the specified conditions
        """

        record_list = self.get_nodes(match=match, order_by=order_by, limit=limit)

        single_field_list = [record.get(field_name) for record in record_list]

        return single_field_list



    def get_node_labels(self, internal_id: int) -> [str]:
        """
        Return a list whose elements are the label(s) of the node specified by its Neo4j internal ID

        TODO: maybe also accept a "match" structure as argument

        :param internal_id: An integer with a Neo4j node id
        :return:            A list of strings with the names of all the labels of the given node
        """
        CypherUtils.assert_valid_internal_id(internal_id)

        q = "MATCH (n) WHERE id(n)=$internal_id RETURN labels(n) AS all_labels"

        return self.query(q, data_binding={"internal_id": internal_id}, single_cell="all_labels")



    def find_first_duplicate(self, labels :str, property_name :str) -> Union[dict, None]:
        """
        Search the database for node duplicates based on the given labels/property_name pairing;
        return the first duplicate, or None if not found

        :param labels:          For now, just 1 label
        :param property_name:   A string with the name of the node property of interest
        :return:                If no duplicates are present, return None;
                                otherwise return a dict such as
                                {'FIRST_INTERNAL_ID': 123, 'SECOND_INTERNAL_ID': 999, 'my_property_name': "I'm a duplicate"}
        """
        #TODO: generalize labels; pytest
        q = f'''
            MATCH (n1 :{labels}), (n2 :{labels})
            WHERE n1.`{property_name}` = n2.`{property_name}`
            AND id(n1) <> id(n2)
            RETURN id(n1) AS FIRST_INTERNAL_ID, id(n2) AS SECOND_INTERNAL_ID, 
            n1.`{property_name}` AS {property_name}
            '''

        return self.query(q, single_row=True)



    def sample_properties(self, label :str, sample_size=10) -> {str}:
        """
        Take a sample of the given size of the database nodes with the given label,
        and assemble the set of ALL the properties that are present on any of those nodes.

        Meant as an estimate of the properties (typically) used, in current usage of the database,
        for nodes of a given label.

        CAUTION: In a graph database, any node may freely deviate - and have, or not have, any Properties
                 it wishes.  If any type of standardization is desired, make use of the GraphSchema layer

        :param label:       Name of the database label of interest
        :param sample_size: Number of nodes to use as a representative sampler
        :return:            Set of property (aka field) names
        """
        # TODO: Pytest
        m = self.match(labels=label)

        result = self.get_nodes(match=m, limit=sample_size) # A list of dicts

        # Note: outer loop in set comprehension, below, is "for d in result" (for each dict in list);
        #       inner loop, "for k in d" (for each key in dict)
        all_keys = {k for d in result for k in d}   # Set of all the key that occur in ANY of the dicts in result

        return all_keys





    #####################################################################################################

    '''                                 ~   CREATE NODES   ~                                          '''

    def ________CREATE_NODES________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################


    def create_node(self, labels, properties=None) -> int|str:
        """
        Create a new node with the given label(s),
        and with the attributes/values specified in the properties dictionary.
        Return the internal database ID of the node just created.

        :param labels:      A string, or list/tuple of strings, specifying Neo4j labels (ok to have blank spaces);
                                it's acceptable to be None
        :param properties:  OPTIONAL (possibly empty or None) dictionary of properties to set for the new node.
                                EXAMPLE: {'age': 22, 'gender': 'F'}

        :return:            The value of the internal database ID of the node just created
        """

        if properties is None:
            properties = {}

        # From the dictionary of attribute names/values,
        #       create a part of a Cypher query, with its accompanying data dictionary
        (attributes_str, data_dictionary) = CypherUtils.dict_to_cypher(properties)
        # EXAMPLE:
        #       attributes_str = '{`cost`: $par_1, `item description`: $par_2}'
        #       data_dictionary = {'par_1': 65.99, 'par_2': 'the "red" button'}

        # Turn labels (string or list/tuple of labels) into a string suitable for inclusion into Cypher
        cypher_labels = CypherUtils.prepare_labels(labels)

        # Assemble the complete Cypher query
        q = f"CREATE (n {cypher_labels} {attributes_str}) RETURN n"

        result_list = self.query_extended(q, data_dictionary, flatten=True)  # TODO: switch to update_query(), and verify the creation
        if len(result_list) != 1:
            raise Exception("GraphAccess.create_node(): failed to create the requested new node")

        return result_list[0]['internal_id']           # Return the Neo4j internal ID of the node just created



    def merge_node(self, labels, properties=None) -> dict:
        """
        The node gets created only if no other node with same labels and properties exists.

        Create a new node with the given label(s) and with the attributes/values specified in the properties dictionary.

        :param labels:      A string, or list/tuple of strings, specifying Neo4j labels (ok to have blank spaces)
        :param properties:  An optional (possibly empty or None) dictionary of properties
                                to try to match in an existing node, or - if not found - to set in a new node.
                                EXAMPLE: {'age': 22, 'gender': 'F'}

        :return:            A dict with 2 keys: "created" (True if a new node was created, or False otherwise)
                                                and "internal_id"
        """
        # TODO: test

        if properties is None:
            properties = {}

        # From the dictionary of attribute names/values,
        #       create a part of a Cypher query, with its accompanying data dictionary
        (attributes_str, data_dictionary) = CypherUtils.dict_to_cypher(properties)
        # EXAMPLE:
        #       attributes_str = '{`cost`: $par_1, `item description`: $par_2}'
        #       data_dictionary = {'par_1': 65.99, 'par_2': 'the "red" button'}

        # Turn labels (string or list/tuple of labels) into a string suitable for inclusion into Cypher
        cypher_labels = CypherUtils.prepare_labels(labels)

        # Assemble the complete Cypher query
        q = f"MERGE (n {cypher_labels} {attributes_str}) RETURN id(n) AS internal_id"


        result = self.update_query(q, data_dictionary)

        internal_id = result["returned_data"][0]["internal_id"]     # The internal database ID of the node found or just created

        if result.get("nodes_created", 0) == 1:
            return {"created": True, "internal_id": internal_id}
        else:
            return {"created": False, "internal_id": internal_id}



    def create_attached_node(self, labels, properties = None,
                             attached_to = None, rel_name = None, rel_dir = "OUT",
                             merge=True) -> int:
        """
        Create a new node (or possibly re-use an existing one),
        with the given labels and optional specified properties,
        and attached all the EXISTING nodes specified in the (possibly empty) list of nodes attached_to,
        using the given relationship name.
        All the relationships are OUTbound or INbound from the newly-created node,
        depending on the value of rel_dir.

        If merge=True, if an existing node is already present with the same labels and properties,
        it will be re-used rather than created (in that case, only the relationships will be created)

        Note: this is a simpler version of create_node_with_links()

        If any of the requested link nodes isn't found,
        then no new node is created, and an Exception is raised.

        Note: under unusual circumstances, the new node may be created even in situations where Exceptions are raised;
              for example, if attempting to create two identical relationships to the same existing node.

        EXAMPLE:
            create_attached_node(
                                    labels="COMPANY",
                                    properties={"name": "Acme Gadgets", "city": "Berkeley"},
                                    attached_to=[123, 456],
                                    rel_name="EMPLOYS"
            )

        :param labels:      Labels to assign to the newly-created node (a string, possibly empty, or list of strings)
        :param properties:  (OPTIONAL) A dictionary of optional properties to assign to the newly-created node
        :param attached_to: (OPTIONAL) An integer, or list/tuple of integers,
                                with internal database ID's to identify the existing nodes;
                                use None, or an empty list, to indicate if there aren't any
        :param rel_name:    (OPTIONAL) Name of the newly created relationships.
                                This is required, if an attached_to list was provided
        :param rel_dir:     (OPTIONAL) Either "OUT"(default), "IN" or "BOTH".  Direction(s) of the relationships to create
        :param merge:       (OPTIONAL) If True (default), a new node gets created only if there's no existing node
                                with the same properties and labels

        :return:            An integer with the internal database ID of the newly-created node
        """
        if type(attached_to) == int:
            attached_to = [attached_to]
        else:
            assert (attached_to is None) or (type(attached_to) == list) or (type(attached_to) == tuple), \
                f"create_attached_node(): the argument `attached_to` must be a list or tuple or None; instead, it's {type(attached_to)}"

        assert (rel_dir is None) or (rel_dir == "IN") or (rel_dir == "OUT"), \
            f"create_attached_node(): the argument `rel_dir` must be either 'IN' or 'OUT' or None; instead, it's `{rel_dir}`"

        if attached_to is not None:
            assert (rel_name is not None) and (rel_name != ""), \
                f"create_attached_node(): when the the argument `attached_to` is present, a non-empty `rel_name` must be passed"

        if attached_to is None:
            links = None
        else:
            links = [{"internal_id": existing_node_id, "rel_name": rel_name, "rel_dir": rel_dir}
                     for existing_node_id in attached_to]

        return self.create_node_with_links(labels=labels, properties=properties, links=links, merge=merge)



    def create_node_with_links(self, labels :str|list|tuple, properties=None, links=None, merge=False) -> int|str:
        """
        Create a new node, with the given labels and optional properties,
        and link it up to all the EXISTING nodes that are specified
        in the (possibly empty) list of link nodes, identified by their Neo4j internal ID's.

        The list of link nodes also contains the names to give to each link,
        as well as their directions (by default OUT-bound from the newly-created node)
        and, optionally, properties on the links.

        If any of the requested link nodes isn't found,
        then no new node is created, and an Exception is raised.

        Note: the new node may be created even in situations where Exceptions are raised;
              for example, if attempting to create two identical relationships to the same existing node.

        EXAMPLE (assuming the nodes with the specified internal database IDs already exist):
            create_node_with_links(
                                labels="PERSON",
                                properties={"name": "Julian", "city": "Berkeley"},
                                links=[ {"internal_id": 123, "rel_name": "LIVES IN"},
                                        {"internal_id": 456, "rel_name": "EMPLOYS", "rel_dir": "IN"},
                                        {"internal_id": 789, "rel_name": "OWNS", "rel_attrs": {"since": 2022}}
                                      ]
            )

        :param labels:      Labels to assign to the newly-created node (optional but recommended):
                                a string or list/tuple of strings; blanks allowed inside strings
        :param properties:  A dictionary of optional properties to assign to the newly-created node
        :param links:       Optional list of dicts identifying existing nodes,
                                and specifying the name, direction and optional properties
                                to give to the links connecting to them;
                                use None, or an empty list, to indicate if there aren't any.
                                Each dict contains the following keys:
                                    "internal_id"   REQUIRED - to identify an existing node
                                    "rel_name"      REQUIRED - the name to give to the link
                                    "rel_dir"       OPTIONAL (default "OUT") - either "IN" or "OUT" from the new node
                                    "rel_attrs"     OPTIONAL - A dictionary of relationship attributes
        :param merge:       (OPTIONAL; default False) If True, a new node gets created only if there's no existing node
                                with the same properties and labels

        :return:            An integer or string with the internal database ID of the newly-created node
        """
        # TODO:  test more the `merge` arg

        assert properties is None or type(properties) == dict, \
            f"GraphAccess.create_node_with_links(): The argument `properties` must be a dictionary or None; instead, it's of type {type(properties)}"

        assert links is None or type(links) == list, \
            f"GraphAccess.create_node_with_links(): The argument `links` must be a list or None; instead, it's of type {type(links)}"


        # Prepare strings and a data-binding dictionary suitable for inclusion in a Cypher query,
        #   to define the new node to be created
        labels_str = CypherUtils.prepare_labels(labels)    # EXAMPLE:  ":`CAR`:`INVENTORY`"
        (cypher_props_str, data_binding) = CypherUtils.dict_to_cypher(properties)
        # EXAMPLE:
        #   cypher_props_str = "{`name`: $par_1, `city`: $par_2}"
        #   data_binding = {'par_1': 'Julian', 'par_2': 'Berkeley'}

        # Define the portion of the Cypher query to create the new node
        if merge:
            q_CREATE = f"MERGE (n {labels_str} {cypher_props_str})"
        else:
            q_CREATE = f"CREATE (n {labels_str} {cypher_props_str})"
            # EXAMPLE:  "CREATE (n :`PERSON` {`name`: $par_1, `city`: $par_2})"


        if links:
            q_MATCH, q_WHERE, q_MERGE, additional_data_binding = self._assemble_query_for_linking(links)
            # Put all the parts of the Cypher query together (*except* for a RETURN statement)
            q = q_MATCH + "\n" + q_WHERE + "\n" + q_CREATE + "\n" + q_MERGE

            # Merge additional_data_binding into the data_binding dict
            data_binding.update(additional_data_binding)
        else:
            links = []      # To avoid problems with the None value, further down
            q = q_CREATE


        # Put all the parts of the Cypher query together (*except* for a RETURN statement)
        q += "\nRETURN id(n) AS internal_id"
        # EXAMPLE of q:
        '''
        MATCH (ex0), (ex1)
        WHERE id(ex0) = 4 AND id(ex1) = 3
        CREATE (n :`PERSON` {`name`: $par_1, `city`: $par_2})
        MERGE (n)<-[:`EMPLOYS` ]-(ex0)
        MERGE (n)-[:`OWNS` {`since`: $EDGE1_1}]->(ex1)
        RETURN id(n) AS internal_id       
        '''
        # EXAMPLE of data_binding : {'par_1': 'Julian', 'par_2': 'Berkeley', 'EDGE1_1': 2021}

        result = self.update_query(q, data_binding)
        #self.debug_print(f"Result of update_query in create_node_with_links():\n{result}")
        # EXAMPLE: {'labels_added': 1, 'relationships_created': 2, 'nodes_created': 1, 'properties_set': 3, 'returned_data': [{'internal_id': 604}]}


        # Assert that the query produced the expected actions
        if not merge:
            if result.get("nodes_created", 0) != 1:
                raise Exception("GraphAccess.create_node_with_links(): failed to create the new node "
                                "(check whether the requested link-to nodes exist)")

            if not labels:
                expected_number_labels = 0
            elif type(labels) == str:
                expected_number_labels = 1
            else:
                expected_number_labels = len(labels)

            if result.get("labels_added", 0) != expected_number_labels:
                raise Exception(f"GraphAccess.create_node_with_links(): failed to set the {expected_number_labels} label(s) expected on the new node")


        if result.get("relationships_created", 0) != len(links):
            raise Exception(f"GraphAccess.create_node_with_links(): failed to create all the {len(links)} requested relationships")

        # Determine the number of entries in the data_binding dict, where the value isn't None
        expected_number_properties = sum(1 for v in data_binding.values() if v is not None)
        if result.get("properties_set", 0) != expected_number_properties:
            raise Exception(f"GraphAccess.create_node_with_links(): Was expecting to set {expected_number_properties} properties on the new node and its relationships; "
                            f"instead, {result.get('properties_set')} got set")

        returned_data = result.get("returned_data")
        #print("returned_data", returned_data)
        if len(returned_data) == 0:
            raise Exception("GraphAccess.create_node_with_links(): Unable to extract internal ID of the newly-created node")

        internal_id = returned_data[0].get("internal_id", None)
        if internal_id is None:    # Note: internal_id might be zero
            raise Exception("GraphAccess.create_node_with_links(): Unable to extract internal ID of the newly-created node")

        return internal_id    # Return the Neo4j ID of the new node



    def _assemble_query_for_linking(self, links: list) -> tuple:
        """
        Helper function for create_node_with_links(), and perhaps future methods.

        Given a list of existing nodes, and info on links to create to/from them,
        define the portions of the Cypher query to locate the existing nodes,
        and to link up to them.
        No query is actually run.

        :param links:   A list: SEE explanation in create_node_with_links()
        :return:        A 4-tuple with the parts of the query, as well as the needed data binding
                            1) q_MATCH
                            2) q_WHERE
                            3) q_MERGE
                            4) data_binding
        """

        assert links and type(links) == list and len(links) > 0, \
            f"GraphAccess._assemble_query_for_linking(): the argument must be a non-empty list"

        # Define the portion of the Cypher query to locate the existing nodes
        q_MATCH = "MATCH"
        q_WHERE = "WHERE"

        # Define the portion of the Cypher query to link up to any of the existing nodes
        q_MERGE = ""

        data_binding = {}
        for i, edge in enumerate(links):
            match_internal_id = edge.get("internal_id")
            if match_internal_id is None:    # Caution: it might be zero
                raise Exception(f"GraphAccess._assemble_query_for_linking(): Missing 'internal_id' key for the node to link to (in list element {edge})")

            assert type(match_internal_id) == int, \
                f"GraphAccess._assemble_query_for_linking(): The value of the 'internal_id' key must be an integer. The type was {type(match_internal_id)}"

            rel_name = edge.get("rel_name")
            if not rel_name:
                raise Exception(f"GraphAccess._assemble_query_for_linking(): Missing name ('rel_name' key) for the new relationship (in list element {edge})")

            node_dummy_name = f"ex{i}"  # EXAMPLE: "ex3".   The "ex" stands for "existing node"
            q_MATCH += f" (ex{i})"      # EXAMPLE: " (ex3)"

            q_WHERE += f" id({node_dummy_name}) = {match_internal_id}"   # EXAMPLE: " id(ex3) = 123"


            rel_dir = edge.get("rel_dir", "OUT")        # "OUT" is the default value
            rel_attrs = edge.get("rel_attrs", None)     # By default, no relationship attributes

            # Process the optional relationship properties
            (rel_attrs_str, cypher_dict_for_edge) = CypherUtils.dict_to_cypher(rel_attrs, prefix=f"EDGE{i}_")
            # EXAMPLE of rel_attrs_str:         '{since: $EDGE1_par_1}'  (possibly a blank string)
            # EXAMPLE of cypher_dict_for_edge:  {'EDGE1_par_1': 2021}    (possibly an empty dict)

            data_binding.update(cypher_dict_for_edge)           # Merge cypher_dict_for_edge into the data_binding dictionary

            if rel_dir == "OUT":
                q_MERGE += f"MERGE (n)-[:`{rel_name}` {rel_attrs_str}]->({node_dummy_name})"  # Form an OUT-bound connection
                # EXAMPLE of term:  "MERGE (n)-[:`OWNS` {since: $EDGE1_par_1}]->(ex1)"
            else:
                q_MERGE += f"MERGE (n)<-[:`{rel_name}` {rel_attrs_str}]-({node_dummy_name})"  # Form an IN-bound connection
                # EXAMPLE of term:  "MERGE (n)<-[:`EMPLOYS` ]-(ex0)"

            if i+1 < len(links):
                q_MATCH += ","          # Comma separator, except at the end
                q_WHERE += " AND"
                q_MERGE += "\n"
            # END for

        # EXAMPLE of q_MATCH at this stage; note that (ex0), etc, refer to EXisting nodes:
        # "MATCH (ex0), (ex1)"

        # EXAMPLE of q_MERGE:
        '''
        MERGE (n)<-[:`EMPLOYS` ]-(ex0)
        MERGE (n)-[:`OWNS` {since: $EDGE1_par_1}]->(ex1)
        '''

        # EXAMPLE of q_WHERE:
        # "WHERE id(ex0) = 123 AND id(ex1) = 456"

        return q_MATCH, q_WHERE, q_MERGE, data_binding



    def create_node_with_relationships(self, labels, properties=None, connections=None) -> int:
        """
        TODO: this method may no longer be needed, given the new method create_node_with_links()
              Maybe ditch, or extract the Neo4j ID's from the connections,
              and call create_node_with_links()

        Create a new node with relationships to zero or more PRE-EXISTING nodes
        (identified by their labels and key/value pairs).

        If the specified pre-existing nodes aren't found, then no new node is created,
        and an Exception is raised.

        On success, return the Neo4j internal ID of the new node just created.

        Note: if all connections are in one direction, and with same (property-less) relationship name,
              and to nodes with known Neo4j internal IDs, then
              the simpler method create_attached_node() may be used instead

        EXAMPLE:
            create_node_with_relationships(
                                            labels="PERSON",
                                            properties={"name": "Julian", "city": "Berkeley"},
                                            connections=[
                                                        {"labels": "DEPARTMENT",
                                                         "key": "dept_name", "value": "IT",
                                                         "rel_name": "EMPLOYS", "rel_dir": "IN"},

                                                        {"labels": ["CAR", "INVENTORY"],
                                                         "key": "vehicle_id", "value": 12345,
                                                         "rel_name": "OWNS", "rel_attrs": {"since": 2021} }
                                            ]
            )

        :param labels:      A string, or list of strings, with label(s) to assign to the new node
        :param properties:  A dictionary of properties to assign to the new node
        :param connections: A (possibly empty) list of dictionaries with the following keys
                            (all optional unless otherwise specified):
                                --- Keys to locate an existing node ---
                                    "labels"        RECOMMENDED
                                    "key"           REQUIRED
                                    "value"         REQUIRED
                                --- Keys to define a relationship to it ---
                                    "rel_name"      REQUIRED.  The name to give to the new relationship
                                    "rel_dir"       Either "OUT" or "IN", relative to the new node (by default, "OUT")
                                    "rel_attrs"     A dictionary of relationship attributes

        :return:            If successful, an integer with the Neo4j internal ID of the node just created;
                                otherwise, an Exception is raised
        """
        #print(f"In create_node_with_relationships().  connections: {connections}")

        # Prepare strings suitable for inclusion in a Cypher query, to define the new node to be created
        labels_str = CypherUtils.prepare_labels(labels)    # EXAMPLE:  ":`CAR`:`INVENTORY`"
        (cypher_props_str, data_binding) = CypherUtils.dict_to_cypher(properties)
        # EXAMPLE:
        #   cypher_props_str = "{`name`: $par_1, `city`: $par_2}"
        #   data_binding = {'par_1': 'Julian', 'par_2': 'Berkeley'}

        # Define the portion of the Cypher query to create the new node
        q_CREATE = f"CREATE (n {labels_str} {cypher_props_str})"
        # EXAMPLE:  "CREATE (n :`PERSON` {`name`: $par_1, `city`: $par_2})"
        #print("\n", q_CREATE)

        # Define the portion of the Cypher query to look up the requested existing nodes
        if connections is None or connections == []:
            q_MATCH = ""        # There will no need for a match, if there are no connections to be made
        else:
            q_MATCH = "MATCH"

        # Define the portion of the Cypher query to link up the new node to any of the existing ones
        q_MERGE = ""

        if properties is None:
            properties = []

        number_props_to_set = len(properties)   # Start building the total number of properties to set on the new node and on the relationships
        # (used to verify that the query ran as expected)

        for i, conn in enumerate(connections):
            #print(f"    i: {i}, conn: {conn}")
            match_labels = conn.get("labels")
            match_labels_str = CypherUtils.prepare_labels(match_labels)
            match_key = conn.get("key")
            if not match_key:
                raise Exception("create_node_with_relationships(): Missing key name for the node to link to")
            match_value = conn.get("value")
            if not match_value:
                raise Exception("create_node_with_relationships(): Missing key value for the node to link to")

            node_dummy_name = f"ex{i}"  # EXAMPLE: "ex3".   The "ex" stands for "existing node"
            data_binding_dummy = f"NODE{i}_VAL"
            q_MATCH += f" (ex{i} {match_labels_str} {{ {match_key}: ${data_binding_dummy} }})"
            # EXAMPLE of the incremental strings contributing to q_MATCH:
            #       "(ex0 :`DEPARTMENT` { dept_name: $NODE_0_VAL })"

            if i+1 < len(connections):
                q_MATCH += ","          # Comma separator, except at the end

            data_binding[data_binding_dummy] = match_value

            rel_name = conn.get("rel_name")
            if not rel_name:
                raise Exception("create_node_with_relationships(): Missing name for the new relationship")

            rel_dir = conn.get("rel_dir", "OUT")        # "OUT" is the default value
            rel_attrs = conn.get("rel_attrs", None)     # By default, no relationship attributes

            #print("        rel_attrs: ", rel_attrs)
            (rel_attrs_str, cypher_dict_for_node) = CypherUtils.dict_to_cypher(rel_attrs, prefix=f"NODE{i}_")  # Process the optional relationship properties
            #print(f"rel_attrs_str: `{rel_attrs_str}` | cypher_dict_for_node: {cypher_dict_for_node}")
            # EXAMPLE of rel_attrs_str:        '{since: $NODE1_par_1}'  (possibly a blank string)
            # EXAMPLE of cypher_dict_for_node: {'NODE1_par_1': 2021}    (possibly an empty dict)

            data_binding.update(cypher_dict_for_node)           # Merge cypher_dict_for_node into the data_binding dictionary
            number_props_to_set += len(cypher_dict_for_node)    # This will be part of the summary count returned by Neo4j

            if rel_dir == "OUT":
                q_MERGE += f"MERGE (n)-[:{rel_name} {rel_attrs_str}]->({node_dummy_name})\n"  # Form an OUT-bound connection
                # EXAMPLE of term:  "MERGE (n)-[:OWNS {since: $NODE1_par_1}]->(ex1)"
            else:
                q_MERGE += f"MERGE (n)<-[:{rel_name} {rel_attrs_str}]-({node_dummy_name})\n"  # Form an IN-bound connection
                # EXAMPLE of term:  "MERGE (n)<-[:EMPLOYS ]-(ex0)"


        #print("q_MATCH:\n", q_MATCH)
        # EXAMPLE of q_MATCH:
        #   "MATCH (ex0 :`DEPARTMENT` { dept_name: $NODE_0_VAL }), (ex1 :`CAR`:`INVENTORY` { vehicle_id: $NODE_1_VAL })"

        #print("q_MERGE:\n", q_MERGE)
        # EXAMPLE of q_MERGE:
        '''(n)<-[:EMPLOYS ]-(ex0)
        (n)-[:OWNS {since: $NODE1_par_1}]->(ex1)'''

        # Put all the parts of the Cypher query together
        q = q_MATCH + "\n" + q_CREATE + "\n" + q_MERGE + "RETURN id(n) AS internal_id"
        #print("\n", q)
        #print("\n", data_binding)
        # EXAMPLE of q:
        '''MATCH (ex0 :`DEPARTMENT` { dept_name: $NODE0_VAL }), (ex1 :`CAR`:`INVENTORY` { vehicle_id: $NODE1_VAL })
        CREATE (n :`PERSON` {`name`: $par_1, `city`: $par_2})
        MERGE (n)<-[:EMPLOYS ]-(ex0)
        MERGE (n)-[:OWNS {`since`: $NODE1_par_1}]->(ex1)
        RETURN id(n) AS internal_id
        '''
        # EXAMPLE of data_binding : {'par_1': 'Julian', 'par_2': 'Berkeley', 'NODE0_VAL': 'IT', 'NODE1_VAL': 12345, 'NODE1_par_1': 2021}

        result = self.update_query(q, data_binding)
        #print("Result of update_query in create_node_with_relationships(): ", result)
        # EXAMPLE: {'labels_added': 1, 'relationships_created': 2, 'nodes_created': 1, 'properties_set': 3, 'returned_data': [{'internal_id': 604}]}


        # Assert that the query produced the expected actions
        if result.get("nodes_created") != 1:
            raise Exception("create_node_with_relationships(): Failed to create 1 new node")

        if result.get("relationships_created") != len(connections):
            raise Exception(f"create_node_with_relationships(): "
                            f"New node created as expected, but failed to create all the {len(connections)} expected relationships")

        expected_number_labels = (1 if type(labels) == str else len(labels))
        if result.get("labels_added") != expected_number_labels:
            raise Exception(f"create_node_with_relationships(): Failed to set the {expected_number_labels} label(s) expected on the new node")

        if result.get("properties_set") != number_props_to_set:
            raise Exception(f"create_node_with_relationships(): Failed to set all the {number_props_to_set} properties on the new node and its relationships")

        returned_data = result.get("returned_data")
        #print("returned_data", returned_data)
        if len(returned_data) == 0:
            raise Exception("create_node_with_relationships(): Unable to extract internal ID of the newly-created node")

        internal_id = returned_data[0].get("internal_id", None)
        if internal_id is None:    # Note: internal_id might be zero
            raise Exception("create_node_with_relationships(): Unable to extract internal ID of the newly-created node")

        return internal_id    # Return the Neo4j ID of the new node




    #####################################################################################################

    '''                                      ~   DELETE NODES   ~                                     '''

    def ________DELETE_NODES________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################


    def delete_nodes(self, match :int|str|CypherBuilder) -> int:
        """
        Delete the node or nodes specified by the match argument.
        Return the number of nodes deleted.

        :param match:   EITHER an integer or string with an internal database node id,
                            OR a "CypherBuilder" object, as returned by match(), with data to identify a node or set of nodes
        :return:        The number of nodes deleted (possibly zero)
        """
        # Unpack needed values from the match object
        (node, where, data_binding, _) = CypherUtils.assemble_cypher_blocks(match, caller_method="delete_nodes")

        q = f"MATCH {node} {CypherUtils.prepare_where(where)} DETACH DELETE n"

        stats = self.update_query(q, data_binding)
        number_nodes_deleted = stats.get("nodes_deleted", 0)
        return number_nodes_deleted





    #####################################################################################################

    '''                                      ~   MODIFY FIELDS   ~                                          '''

    def ________MODIFY_FIELDS________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################


    def set_fields(self, match: Union[int, str, CypherBuilder], set_dict: dict, drop_blanks=True) -> int:
        """
        Update, possibly adding and/or dropping fields, the properties of an existing node or group of nodes.

        EXAMPLE - locate the "car" node with `vehicle id` 123 and set its color to "white" and price to 7000
            m = match(labels = "car", properties = {"vehicle id": 123})     # Object of type "CypherBuilder"
            set_fields(match=m, set_dict = {"color": "white", "price": 7000})

        NOTE: other fields are left un-disturbed

        Return the number of properties set.

        :param match:       EITHER a valid internal database ID (int or string),
                                OR a "CypherBuilder" object, as returned by match(),
                                    that contains data to identify a node or set of nodes

        :param set_dict:    A dictionary of field name/values to create/update the node's attributes
                                (note: blanks ARE allowed in the keys)
                                Blanks at the start/end of string values are zapped.
                                Any None value leads to that attribute being dropped from the nodes.
        :param drop_blanks: [OPTIONAL] If True (default), then any blank field is interpreted as a request to drop that property
                                (as opposed to setting its value to "")
                                Note that attributes set to None values are always dropped, regardless of this flag.

        :return:            The number of properties set or removed;
                                if the record wasn't found, or an empty `set_dict` was passed, return 0
                                Important: a property is counted as being "set" even if the new value is
                                           identical to the old value!
        """

        if set_dict == {}:
            return 0             # There's nothing to do


        # Unpack the parts needed to put together a Cypher query
        (node, where, data_binding, dummy_node_name) = CypherUtils.assemble_cypher_blocks(match, caller_method="set_fields")

        # Start forming the Cypher query
        cypher_match = f"MATCH {node} {CypherUtils.prepare_where(where)} "

        set_list = []
        remove_list = []
        for field_name, field_value in set_dict.items():    # field_name, field_value are key/values in set_dict
            if type(field_value) == str:
                field_value = field_value.strip()               # Zap all leading and trailing blanks

            if (field_value == "") and drop_blanks:
                remove_list.append(f"{dummy_node_name}.`{field_name}`")
            else:
                field_name_safe = field_name.replace(" ", "_")      # To protect against blanks in name, which could not be used
                                                                    #   in names of data-binding variables.  E.g., "end date" becomes "end_date"
                set_list.append(f"{dummy_node_name}.`{field_name}` = ${field_name_safe}")    # Example:  "n.`field1` = $field1"
                data_binding[field_name_safe] = field_value                                  # EXTEND the Cypher data-binding dictionary

        # Example of data_binding at the end of the loop: {'n_par_1': 123, 'n_par_2': 7500, 'color': 'white', 'price': 7000}
        #       in this example, the first 2 keys arise from the match (find) operation to locate the node,
        #       while the last 2 are for the use of the SET operation


        set_clause = ""
        if set_list:
            set_clause = " SET " + ", ".join(set_list)   # Example:  "SET n.`color` = $color, n.`price` = $price"

        remove_clause = ""
        if drop_blanks and remove_list:
            remove_clause = " REMOVE " + ", ".join(remove_list)   # Example:  "REMOVE n.`color`, n.`max quantity`


        cypher = cypher_match + set_clause + remove_clause

        # Example of cypher:
        # "MATCH (n :`car` {`vehicle id`: $n_par_1, `price`: $n_par_2})  SET n.`color` = $color, n.`price` = $price"
        # Example of data binding:
        #       {'n_par_1': 123, 'n_par_2': 7500, 'color': 'white', 'price': 7000}

        #self.debug_query_print(cypher, data_binding)
        stats = self.update_query(cypher, data_binding)

        number_properties_set = stats.get("properties_set", 0)
        return number_properties_set





    #####################################################################################################

    '''                                    ~   RELATIONSHIPS   ~                                      '''

    def ________RELATIONSHIPS________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################


    def get_relationship_types(self) -> [str]:
        """
        Extract and return a list of all the Neo4j relationship names (i.e. types of relationships)
        present in the entire database, in no particular order

        :return:    A list of strings
        """
        results = self.query("call db.relationshipTypes() yield relationshipType return relationshipType")
        return [x['relationshipType'] for x in results]



    def add_links(self, match_from :int|str|CypherBuilder, match_to :int|str|CypherBuilder,
                  rel_name :str) -> int:
        """
        Add one or more links (aka graph edges/relationships), with the specified rel_name,
        originating in each of the nodes specified by the match_from specifications,
        and terminating in each of the nodes specified by the match_to specifications

        Return the number of links added; if none were added, or in case of error, raise an Exception.

        Notes:  - if a relationship with the same name already exists, nothing gets created (and an Exception is raised)
                - more than 1 node could be present in either of the matches

        :param match_from:  EITHER an integer or string with an internal database node id,
                                OR a "CypherBuilder" object, as returned by match(), with data to identify a node or set of nodes
        :param match_to:    EITHER an integer or string with an internal database node id,
                                OR a "CypherBuilder" object, as returned by match(), with data to identify a node or set of nodes
                            Note: match_to could be the same as match_from (to add a link from a node to itself)
                            Note: match_from and match_to, if created by calls to match(),
                                  in scenarios where a clause dummy name is actually used,
                                  MUST use different clause dummy names.

        :param rel_name:    The name to give to all the new relationships between the 2 specified nodes, or sets or nodes.
                                Blanks allowed.

        :return:            The number of edges added.  If none got added, or in case of error, an Exception is raised
        """
        #         TODO: add a `rel_props` argument - see approach done in add_links_fast()
        #               (Unclear what multiple calls would do in this case: update the props or create a new relationship??)

        (nodes_from, where_from, data_binding_from, _) = \
                CypherUtils.assemble_cypher_blocks(handle=match_from, dummy_node_name="from", caller_method="add_links")

        (nodes_to, where_to, data_binding_to, _) = \
                CypherUtils.assemble_cypher_blocks(handle=match_to, dummy_node_name="to", caller_method="add_links")

        where_clause = CypherUtils.prepare_where([where_from, where_to])

        # Prepare the query to add the requested links between the given nodes (possibly, sets of nodes)
        q = f'''
            MATCH {nodes_from}, {nodes_to}
            {where_clause}
            MERGE (from) -[:`{rel_name}`]-> (to)           
            '''

        # Merge the data-binding dict's
        combined_data_binding = CypherUtils.prepare_data_binding(data_binding_from, data_binding_to)

        result = self.update_query(q, combined_data_binding)

        number_relationships_added = result.get("relationships_created", 0)   # If field isn't present, return a 0
        if number_relationships_added == 0:       # This could be more than 1: see notes above
            raise Exception(f"add_links(): the requested relationship ({rel_name}) was NOT added")

        return number_relationships_added



    def add_links_fast(self, match_from :int|str, match_to :int|str, rel_name :str, rel_props=None) -> int:
        """
        Method optimized for speed.  Only internal database ID's are used.

        Add a links (aka graph edges/relationships), with the specified rel_name,
        originating in the node identified by match_from,
        and terminating in the node identified by match_to

        :param match_from:  Internal database node id of the node from where the new link originates
        :param match_to:    Internal database node id of the node into which the new link terminates
        :param rel_name:    The name to give to the new relationship between the 2 specified nodes.  Blanks allowed
        :param rel_props:   [OPTIONAL] A dict with properties to store on the newly-created link.
                                Currently, no double quotes are allowed in the values.
                                Any entry with None for a value are disregarded.

        :return:            The number of links added.  If none got added, or in case of error, an Exception is raised
        """
        # TODO: merge with add_links()
        # TODO: (Unclear what multiple calls would do in this case: update the props or create a new relationship??)

        # Prepare the query to add the requested links between the given nodes (possibly, sets of nodes)
        if rel_props:
            # Convert the dict into a string suitable for inclusion into Cypher; e.g. {"since": 2025, "from": "John"}
            # will be turned into the string '{since: 2025, from: "John"}'
            # TODO: this will fail with datetime values, as well as with values with double quotes;
            #       use data binding instead
            #       EXAMPLE:   rel_props_converted = "{bought: $par_1}"
            #                  MERGE (from) -[:`OWNS` {rel_props_converted}]-> (to)
            #                  data_binding = {"par_1": neo4j.time.DateTime(2025, 11, 13, 13, 29, 15)}
            #       Should be able to do:
            #           rel_props_converted, data_binding = CypherUtils.dict_to_cypher(data_dict=rel_props)
            entries = []
            for k, v in rel_props.items():
                if v is None:
                    continue        # Disregard dictionary entries with None values

                if type(v) == str:
                    v_str = f'"{v}"'
                else:
                    v_str = str(v)

                entries.append(f"{k}: {v_str}")

            rel_props_cypher = "{" + ", ".join(entries) + "}"
            #print(f"rel_props_cypher: {rel_props_cypher}")
        else:
            rel_props_cypher = ""

        q = f'''
            MATCH (from), (to)
            WHERE id(from) = {match_from} AND id(to) = {match_to}
            MERGE (from) -[:`{rel_name}` {rel_props_cypher}]-> (to)           
            '''

        result = self.update_query(q)

        number_relationships_added = result.get("relationships_created", 0)   # If field isn't present, return a 0
        if number_relationships_added == 0:       # This could be more than 1: see notes above
            raise Exception(f"add_links_fast(): the requested relationship ({rel_name}) was NOT added")

        return number_relationships_added



    def remove_links(self, match_from :int|CypherBuilder, match_to :int|CypherBuilder, rel_name) -> int:
        """
        Remove one or more links (aka relationships/edges)
        originating in any of the nodes specified by the match_from specifications,
        and terminating in any of the nodes specified by the match_to specifications,
        optionally matching the given relationship name (will remove all edges if the name is blank or None)

        Return the number of edges removed; if none found, or in case of error, raise an Exception.

        Notes: - the nodes themselves are left untouched
               - more than 1 node could be present in either of the matches
               - the number of relationships deleted could be more than 1 even with a single "from" node and a single "to" node;
                        Neo4j allows multiple relationships with the same name between the same two nodes,
                        as long as the relationships differ in their properties

        :param match_from:  EITHER an integer with an internal database node id,
                                OR a "CypherBuilder" object, as returned by match(), with data to identify a node or set of nodes
        :param match_to:    EITHER an integer with an internal database node id,
                                OR a "CypherBuilder" object, as returned by match(), with data to identify a node or set of nodes
                            Note: match_from and match_to, if created by calls to match(),
                                  in scenarios where a clause dummy name is actually used,
                                  MUST use different clause dummy names.

        :param rel_name:    (OPTIONAL) The name of the relationship to delete between the 2 specified nodes;
                                if None or a blank string, all relationships between those 2 nodes will get deleted.
                                Blanks allowed.

        :return:            The number of edges removed, if edges were found.
                                If none got deleted, an Exception is raised
        """
        # TODO: add a method to remove all links of a given name emanating to or from a given node
        #       - as done for Schema.remove_all_data_relationship()
        # TODO: add a rename_link() method

        (nodes_from, where_from, data_binding_from, _) = \
                CypherUtils.assemble_cypher_blocks(handle=match_from, dummy_node_name="from", caller_method="remove_links")

        (nodes_to, where_to, data_binding_to, _) = \
                CypherUtils.assemble_cypher_blocks(handle=match_to, dummy_node_name="to", caller_method="remove_links")


        # Combine the two WHERE clauses from each of the matches,
        # and also prefix (if appropriate) the WHERE keyword
        where_clause = CypherUtils.prepare_where([where_from, where_to])

        # Prepare the query
        if rel_name is None or rel_name == "":  # Delete ALL relationships
            q = f'''
                MATCH {nodes_from} -[r]-> {nodes_to}
                {where_clause}
                DELETE r           
                '''
        else:                                   # Delete a SPECIFIC relationship
            q = f'''
                MATCH {nodes_from} -[r :`{rel_name}`]-> {nodes_to}
                {where_clause}
                DELETE r           
                '''

        # Merge the data-binding dict's
        combined_data_binding = CypherUtils.prepare_data_binding(data_binding_from, data_binding_to)


        result = self.update_query(q, combined_data_binding)


        number_relationships_deleted = result.get("relationships_deleted", 0)   # If field isn't present, return a 0
        if number_relationships_deleted == 0:       # This could be more than 1: see notes above
            raise Exception(f"remove_links(): no relationship named `{rel_name}` could be deleted")

        return number_relationships_deleted



    def links_exist(self, match_from: Union[int, CypherBuilder], match_to: Union[int, CypherBuilder], rel_name: str) -> bool:
        """
        Return True if one or more edges (relationships) with the specified name exist in the direction
        from and to the nodes (individual nodes or set of nodes) specified in the first two arguments.
        Typically used to find whether 2 given nodes have a direct link between them.

        :param match_from:  EITHER an integer with an internal database node id,
                                OR a "CypherBuilder" object, as returned by match(), with data to identify a node or set of nodes
        :param match_to:    EITHER an integer with an internal database node id,
                                OR a "CypherBuilder" object, as returned by match(), with data to identify a node or set of nodes
                            Note: match_from and match_to, if created by calls to match(),
                                  in scenarios where a clause dummy name is actually used,
                                  MUST use different clause dummy names.

        :param rel_name:    The name of the relationship to look for between the 2 specified nodes.
                                Blanks are allowed inside the string

        :return:            True if one or more relationships were found, or False if not
        """
        # TODO: maybe rename arguments from_match and to_match, for consistency with GraphSchema
        return self.number_of_links(match_from=match_from, match_to=match_to, rel_name=rel_name) >= 1   # True if at least 1



    def number_of_links(self, match_from: Union[int, CypherBuilder], match_to: Union[int, CypherBuilder], rel_name: str) -> int:
        """
        Return the number of links (aka edges or relationships) with the given name
        that exist in the direction from and to the nodes (individual nodes or set of nodes)
        that are specified in the first two arguments.

        :param match_from:  EITHER an integer with an internal database node id,
                                OR a "CypherBuilder" object, as returned by match(), with data to identify a node or set of nodes
        :param match_to:    EITHER an integer with an internal database node id,
                                OR a "CypherBuilder" object, as returned by match(), with data to identify a node or set of nodes
                            Note: match_from and match_to, if created by calls to match(),
                                  in scenarios where a clause dummy name is actually used,
                                  MUST use different clause dummy names.

        :param rel_name:    The name of the relationship to look for between the 2 specified nodes or groups of nodes.
                                Blanks are allowed inside the string

        :return:            The number of links (relationships) that were found
        """
        # TODO: maybe rename arguments from_match and to_match, for consistency with GraphSchema
        # TODO: allow unspecified relationship names
        # TODO: allow specifying properties that must be in the relationship
        (nodes_from, where_from, data_binding_from, _) = \
                CypherUtils.assemble_cypher_blocks(handle=match_from, dummy_node_name="from", caller_method="number_of_links")

        (nodes_to, where_to, data_binding_to, _) = \
                CypherUtils.assemble_cypher_blocks(handle=match_to, dummy_node_name="to", caller_method="number_of_links")

        # Combine the two WHERE clauses from each of the matches,
        # Combine the two WHERE clauses from each of the matches,
        # and also prefix (if appropriate) the WHERE keyword
        where_clause = CypherUtils.prepare_where([where_from, where_to])

        # Prepare the query.   TODO: to be more efficient, do something like p=MATCH ....  RETURN COUNT(p) AS link_number
        q = f'''
            MATCH {nodes_from} -[r :`{rel_name}`]-> {nodes_to}
            {where_clause} 
            RETURN r          
            '''

        # Merge the data-binding dict's
        combined_data_binding = CypherUtils.prepare_data_binding(data_binding_from, data_binding_to)

        result = self.query(q, combined_data_binding)

        return len(result)



    def reattach_node(self, node, old_attachment, new_attachment, rel_name:str, rel_name_new=None) -> None:
        """
        Sever the relationship with the given name from the given node to the node old_attachment,
        and re-create it to the node new_attachment (optionally under a different relationship name).

        Note: relationship properties, if present, will NOT be transferred

        :param node:            An integer with the internal database ID of the node to detach and reattach
        :param old_attachment:  An integer with the internal database ID of the other node currently connected to
        :param new_attachment:  An integer with the internal database ID of the new node to connect to
        :param rel_name:        Name of the old relationship name
        :param rel_name_new:    (OPTIONAL) Name of the new relationship name (by default the same as the old one)

        :return:                None.  If unsuccessful, an Exception is raised
        """
        assert CypherUtils.valid_internal_id(node), \
            f"reattach_node(): not a valid internal database ID ({node})"
        assert CypherUtils.valid_internal_id(old_attachment), \
            f"reattach_node(): not a valid internal database ID ({old_attachment})"
        assert CypherUtils.valid_internal_id(new_attachment), \
            f"reattach_node(): not a valid internal database ID ({new_attachment})"

        if rel_name_new is None:
            rel_name_new = rel_name     # Use the default value, if not provided

        q = f'''
            MATCH (node_start) -[rel :{rel_name}]-> (node_old), (node_new)
            WHERE id(node_start) = {node} and id(node_old) = {old_attachment} and id(node_new) = {new_attachment}
            MERGE (node_start) -[:{rel_name_new}]-> (node_new)
            DELETE rel         
            '''

        result = self.update_query(q)
        #print("result of update_query in reattach_node(): ", result)

        assert (result.get("relationships_deleted") == 1), \
            "reattach_node(): failed to delete the old relationship (" \
            "probably means it doesn't exist, or the other node doesn't exist; check if they all exist)"

        assert (result.get("relationships_created") == 1), \
            "reattach_node(): it deleted the old relationship but failed to create a new one"   # This should not occur



    def link_nodes_by_ids(self, node_id1:int, node_id2:int, rel:str, rel_props = None) -> None:
        """
        Locate the pair of Neo4j nodes with the given Neo4j internal ID's.
        If they are found, add a relationship - with the name specified in the rel argument,
        and with the specified optional properties - from the 1st to 2nd node - unless already present.

        EXAMPLE:    link_nodes_by_ids(123, 88, "AVAILABLE_FROM", {'cost': 1000})

        :param node_id1:    An integer with the internal database ID to locate the 1st node
        :param node_id2:    An integer with the internal database ID to locate the 2nd node
        :param rel:         A string specifying a relationship name
        :param rel_props:   Optional dictionary with the relationship properties.
                                EXAMPLE: {'since': 2003, 'code': 'xyz'}
        :return:            None
        """
        #TODO: maybe return a status, or the internal database ID of the relationship just created

        cypher_rel_props, cypher_dict = CypherUtils.dict_to_cypher(rel_props)  # Process the optional relationship properties
        # EXAMPLE of cypher_rel_props: '{cost: $par_1, code: $par_2}'   (possibly blank)
        # EXAMPLE of cypher_dict: {'par_1': 65.99, 'par_2': 'xyz'}      (possibly empty)

        q = f"""
        MATCH (x), (y) 
        WHERE id(x) = $node_id1 AND id(y) = $node_id2
        MERGE (x)-[:`{rel}` {cypher_rel_props}]->(y)
        """

        # Extend the (possibly empty) Cypher data dictionary,
        # to also include a value for the keys "node_id1" and "node_id2"
        cypher_dict["node_id1"] = node_id1
        cypher_dict["node_id2"] = node_id2

        self.query(q, cypher_dict)



    def link_nodes_on_matching_property(self, label1:str, label2:str, property1:str, rel:str, property2=None) -> None:
        """
        Locate any pair of Neo4j nodes where all of the following hold:
                            1) the first one has label1
                            2) the second one has label2
                            3) the two nodes agree in the value of property1 (if property2 is None),
                                        or in the values of property1 in the 1st node and property2 in the 2nd node
        For any such pair found, add a relationship - with the name specified in the rel argument - from the 1st to 2nd node,
        unless already present.

        This operation is akin to a "JOIN" in a relational database; in pseudo-code:
                "WHERE label1.value(property1) = label2.value(property1)"       # if property2 is None
                    or
                "WHERE label1.value(property1) = label2.value(property2)"

        :param label1:      A string against which the label of the 1st node must match
        :param label2:      A string against which the label of the 2nd node must match
        :param property1:   Name of property that must be present in the 1st node (and also in 2nd node, if property2 is None)
        :param property2:   Name of property that must be present in the 2nd node (may be None)
        :param rel:         Name to give to all relationships that get created
        :return:            None
        """
        if not property2:
            property2 = property1

        q = f'''MATCH (x:`{label1}`), (y:`{label2}`) WHERE x.`{property1}` = y.`{property2}` 
                MERGE (x)-[:{rel}]->(y)'''

        self.query(q)





    #####################################################################################################

    '''                                    ~   FOLLOW LINKS   ~                                        '''

    def ________FOLLOW_LINKS________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################


    def follow_links(self, match: Union[int, CypherBuilder], rel_name :str, rel_dir ="OUT",
                           neighbor_labels=None, include_id=False, include_labels=False, limit=100) -> [dict]:
        """
        From the given starting node(s), follow all the relationships that have the specified name,
        from/into neighbor nodes (optionally requiring those nodes to have the given labels),
        and return all the properties of the located neighbor nodes, optionally also including their internal database ID's.

        :param match:           EITHER an integer with an internal database node id,
                                    OR a "CypherBuilder" object, as returned by match(),
                                    with data to identify a node or set of nodes
        :param rel_name:        A string with the name of relationship to follow.
                                    (Note: any other relationships are ignored)
        :param rel_dir:         Either "OUT"(default), "IN" or "BOTH".  Direction(s) of the relationship to follow
        :param neighbor_labels: [OPTIONAL] label(s) required on the neighbor nodes; nodes that don't match are ignored.
                                    If used, provide either a string or list of strings

        :param include_id:      [OPTIONAL] If True, also return an extra field named "internal_id",
                                    with the internal database ID value; by default, False
        :param include_labels:  [OPTIONAL] If True, also return an extra field named "node_labels",
                                    with a list of the node labels; by default, False
        :param limit:           [OPTIONAL] The max number of neighbors to visit (not in any particular order);
                                    by default 100

        :return:                A list of dictionaries with all the properties of the neighbor nodes.
                                    If `include_id` is True, then each dict also contains a key named "internal_id",
                                    with the internal database ID value.
                                    Any datetime, etc, value in the database are first converted to python strings
        """
        # TODO: add an option to only retrieve SOME of the properties
        # TODO: add an option to also retrieve some or all the properties of the relationships

        #match_structure = CypherUtils.process_match_structure(match, caller_method="follow_links")

        if limit is not None:
            assert (type(limit) == int) and (limit >= 1), \
                f"follow_links(): the argument `limit`, if passed, must be an integer >= 1 (value passed: {limit})"

        # Unpack needed values from the match dictionary
        (node, where, data_binding, _) = CypherUtils.assemble_cypher_blocks(match, caller_method="follow_links")

        neighbor_labels_str = CypherUtils.prepare_labels(neighbor_labels)     # EXAMPLE:  ":`CAR`:`INVENTORY`"

        if rel_dir == "OUT":    # Follow outbound links
            q =  f"MATCH {node} - [:{rel_name}] -> (neighbor {neighbor_labels_str})"
        elif rel_dir == "IN":   # Follow inbound links
            q =  f"MATCH {node} <- [:{rel_name}] - (neighbor {neighbor_labels_str})"
        else:                   # Follow links in BOTH directions
            q =  f"MATCH {node}  - [:{rel_name}] - (neighbor {neighbor_labels_str})"


        q += CypherUtils.prepare_where(where) + " RETURN neighbor"

        if include_id:
            q += " , id(neighbor) AS internal_id"

        if include_labels:
            q += " , labels(neighbor) AS node_labels"

        if limit is not None:
            q += f" LIMIT {limit}"

        result = self.query(q, data_binding)        # , single_column='neighbor'

        return self.standardize_recordset(recordset=result, dummy_name="neighbor")



    def count_links(self, match: Union[int, CypherBuilder], rel_name: str, rel_dir="OUT", neighbor_labels = None) -> int:
        """
        From the given starting node(s), count all the relationships OF THE GIVEN NAME to and/or from it,
        into/from neighbor nodes (optionally having the given labels)

        :param match:           EITHER an integer with an internal database node id,
                                    OR a "CypherBuilder" object, as returned by match(), with data to identify a node or set of nodes
        :param rel_name:        A string with the name of relationship to follow.  (Note: any other relationships are ignored)
        :param rel_dir:         Either "OUT"(default), "IN" or "BOTH".  Direction(s) of the relationship to follow
        :param neighbor_labels: Optional label(s) required on the neighbors.  If present, either a string or list of strings

        :return:                The total number of inbound and/or outbound relationships to the given node(s)
        """
        #TODO: change default of `rel_dir` to "BOTH"
        #match_structure = CypherUtils.process_match_structure(match, caller_method="count_links")

        # Unpack needed values from the match dictionary
        (node, where, data_binding, _) = CypherUtils.assemble_cypher_blocks(match, caller_method="count_links")

        neighbor_labels_str = CypherUtils.prepare_labels(neighbor_labels)     # EXAMPLE:  ":`CAR`:`INVENTORY`"

        if rel_dir == "OUT":            # Follow outbound links
            q =  f"MATCH {node} - [:{rel_name}] -> (neighbor {neighbor_labels_str})"
        elif rel_dir == "IN":           # Follow inbound links
            q =  f"MATCH {node} <- [:{rel_name}] - (neighbor {neighbor_labels_str})"
        elif rel_dir == "BOTH":         # Follow links in BOTH directions
            q =  f"MATCH {node}  - [:{rel_name}] - (neighbor {neighbor_labels_str})"
        else:
            raise Exception(f"count_links(): argument `rel_dir` must be one of: 'IN', 'OUT', 'BOTH'; value passed was `{rel_dir}`")

        q += CypherUtils.prepare_where(where) + " RETURN count(neighbor) AS link_count"

        return self.query(q, data_binding, single_cell="link_count")



    def get_parents_and_children(self, internal_id: int) -> ():
        """
        Fetch all the nodes connected to the given one by INbound relationships to it (its "parents"),
        as well as by OUTbound relationships to it (its "children")
        TODO: allow specifying a relationship name to follow

        :param internal_id: An integer with a Neo4j internal node ID
        :return:            A dictionary with 2 keys: 'parent_list' and 'child_list'
                                The values are lists of dictionaries with 3 keys: "internal_id", "label", "rel"
                                EXAMPLE of individual items in either parent_list or child_list:
                                {'internal_id': 163, 'labels': ['Subject'], 'rel': 'HAS_TREATMENT'}
        """

        # Fetch the parents
        cypher = f"MATCH (parent)-[inbound]->(n) WHERE id(n) = {internal_id} " \
                 "RETURN id(parent) AS internal_id, labels(parent) AS labels, type(inbound) AS rel"

        parent_list = self.query(cypher)
        # EXAMPLE of parent_list:
        #       [{'internal_id': 163, 'labels': ['Subject'], 'rel': 'HAS_TREATMENT'},
        #        {'internal_id': 150, 'labels': ['Subject'], 'rel': 'HAS_TREATMENT'}]


        # Fetch the children
        cypher = f"MATCH (n)-[outbound]->(child) WHERE id(n) = {internal_id} " \
                 "RETURN id(child) AS internal_id, labels(child) AS labels, type(outbound) AS rel"

        child_list = self.query(cypher)
        # EXAMPLE of child_list:
        #       [{'internal_id': 107, 'labels': ['Source Data Row'], 'rel': 'FROM_DATA'},
        #        {'internal_id': 103, 'labels': ['Source Data Row'], 'rel': 'FROM_DATA'}]


        return (parent_list, child_list)



    def get_siblings(self, internal_id: int, rel_name: str, rel_dir="OUT", order_by=None) -> [int]:
        """
        Return the data of all the "sibling" nodes of the given one.
        By "sibling", we mean: "sharing a link (by default outbound) of the specified name,
        to a common other node".

        EXAMPLE: 2 nodes, "French" and "German",
                 each with a outbound link named "subcategory_of" to a third node,
                 will be considered "siblings" under rel_name="subcategory_of" and rel_dir="OUT

        :param internal_id: Integer with the internal database ID of the node of interest
        :param rel_name:    The name of the relationship used to establish a "siblings" connection
        :param rel_dir:     (OPTIONAL) Either "OUT" (default) or "IN".  The link direction that is expected from the
                                start node to its "parents" - and then IN REVERSE to the parent's children
        :param order_by:    (OPTIONAL) If specified, it must be the name of a field in
                                the sibling nodes, to order the results by; capitalization is ignored
        :return:            A list of dictionaries, with one element for each "sibling";
                                each element contains the 'internal_id' and 'node_labels' keys,
                                plus whatever attributes are stored on that node.
                                EXAMPLE of single element:
                                {'name': 'French', 'internal_id': 123, 'node_labels': ['Categories']}
        """
        #TODO: test order_by
        #TODO: test scenarios that are affected by the DISTINCT ; eg: 2 siblings that share the same 2 parent,
        #      to avoid over-counting
        #TODO: also accept a "CypherBuilder" object for internal_id

        CypherUtils.assert_valid_internal_id(internal_id)

        assert type(rel_name) == str, \
            f"get_siblings(): argument `rel_name` must be a string; " \
            f"the given value ({rel_name}) is of type {type(rel_name)}"

        # Follow the links with the specified name, in the indicated direction from the given link,
        # and then in the reverse direction
        if rel_dir == "OUT":
            q = f"""
                MATCH (n) - [:{rel_name}] -> (parent) <- [:{rel_name}] - (sibling)
                WHERE id(n) = $internal_id
                RETURN DISTINCT sibling
                """
        elif rel_dir == "IN":
            q = f"""
                MATCH (n) <- [:{rel_name}] - (parent) - [:{rel_name}] -> (sibling)
                WHERE id(n) = $internal_id
                RETURN DISTINCT sibling
                """
        else:
            raise Exception(f"get_siblings(): unknown value for the `rel_dir` argument ({rel_dir}); "
                            f"allowed values are 'IN' and 'OUT'")

        if order_by:
            q += f'''
                ORDER BY toLower(sibling.{order_by}])
                '''

        result = self.query_extended(q, data_binding={"internal_id": internal_id}, flatten=True)
        return result



    def get_link_summary(self, internal_id, omit_names = None) -> dict:
        """
        Return a dictionary structure identifying the names and counts of all
        inbound and outbound links to and from the given node.

        :param internal_id: The internal database ID of the node of interest
        :param omit_names:  [OPTIONAL] List of relationship names to disregard

        :return:            A dictionary with the names and counts of the inbound and outbound links.
                            This dictionary has two keys, "in" and "out";
                            their respective values are (possibly empty) lists.
                            Each list entry is a pair of the form (link_name, count)
                            EXAMPLE:
                                {
                                    "in": [
                                        ("served_at", 1)
                                    ],
                                    "out": [
                                        ("located_in", 1),
                                        ("cuisine_type", 2)
                                    ]
                                }
        """
        # TODO: generalize to accept a match structure instead of just internal_id

        id_clause = f"id(n) = {internal_id}"

        if omit_names:
            assert type(omit_names) == list, "If the `omit_names` argument is specified, it MUST be a LIST"
            where_clause = f"WHERE NOT type(r) IN {omit_names} AND {id_clause}"
        else:
            where_clause = f"WHERE {id_clause}"

        # Get outbound links (names and counts)
        q_out = f'''
                MATCH (n)-[r]->(n2)
                {where_clause}
                RETURN type(r) AS rel_name, count(n2) AS rel_count
                '''

        result = self.query(q_out)
        rel_out = [ ( l["rel_name"], l["rel_count"] ) for l in result ]


        # Get inbound links (names and counts)
        q_in = f'''
                MATCH (n)<-[r]-(n2)
                {where_clause}
                RETURN type(r) AS rel_name, count(n2) AS rel_count
                '''

        result = self.query(q_in)
        rel_in = [ ( l["rel_name"], l["rel_count"] ) for l in result ]

        return  {"in": rel_in, "out": rel_out}



    def explore_neighborhood(self, start_id :int|str, max_hops=2,
                             avoid_links=None, follow_links=None,
                             avoid_label=None,
                             include_start_node=False) -> [dict]:
        """
        Return distinct "nearby" database nodes, from a given start node, by following a max number of links,
        and optionally avoiding traversing links with some specified names,
        and optionally avoiding traversing nodes that include the specified label.
        Optionally, include the start node as well.
        Included nodes will only appear once in the result, even if there might be multiple paths to get to them

        :param start_id:        The value of the internal database ID of the starting node
        :param max_hops:        [OPTIONAL] Integer >= 1 with the maximum number of links to follow in the graph traversal;
                                    i.e. the max distance to travel away from the starting node
        :param avoid_links:     [OPTIONAL] Name, or list/tuple of names, of links to avoid in the graph traversal
        :param follow_links:    [OPTIONAL] Name, or list/tuple of names, of the links that we're allowed to follow in the traversal
        :param avoid_label:     [OPTIONAL] Name of a node label to be avoided on any of the nodes in the graph traversal
        :param include_start_node: [OPTIONAL] If True, include the start node as well in the returned result

        :return:                A (possibly empty) list of dict's, with the properties of all the located nodes,
                                    plus the 2 special keys "internal_id" and "node_labels".
                                    EXAMPLE: [ {'color': 'red', 'internal_id': 123, 'node_labels': ['Car']} ]
        """
        CypherUtils.assert_valid_internal_id(start_id)

        assert max_hops >= 1, \
            f"explore_neighborhood(): argument `max_hops` " \
            f"must be an integer >= 1 (passed value was {max_hops})"

        if avoid_links and follow_links:
            raise Exception(f"explore_neighborhood(): cannot pass both arguments `avoid_links` and `follow_links`")


        path_clause = CypherUtils.avoid_links_in_path(avoid_links=avoid_links, avoid_label=avoid_label, prefix_and=True)

        cypher_rel_str = ""
        if follow_links:
            if type(follow_links) == str:
                follow_links = follow_links.strip()
                assert follow_links != "", \
                    "explore_neighborhood(): argument `follow_links`, if provided as a string, cannot be empty"
                cypher_rel_str = f":`{follow_links}`"             # EXAMPLE: ":`rel_1`"
            else:
                assert type(follow_links) == list or type(follow_links) == tuple, \
                    "explore_neighborhood(): argument `follow_links`, if provided, must be a string or list/tuple of strings"

                cypher_rel_str = ":`" + "`|`".join(follow_links) + "`"  # EXAMPLE: ":`rel_1`|`rel_2`"


        # Locate graph paths from the given start node (s) to end nodes (e)
        q = f'''
            MATCH  p=(s)-[{cypher_rel_str}*1..{max_hops}]-(e)
            WHERE id(s) = $start_id
            {path_clause}
            RETURN DISTINCT e, id(e) AS internal_id, labels(e) AS node_labels
        '''

        if include_start_node:
            q += '''
                UNION MATCH (e)
                WHERE id(e) = $start_id
                RETURN DISTINCT e, id(e) AS internal_id, labels(e) AS node_labels
                '''

        data_dict={"start_id": start_id}

        #self.debug_query_print(q=q, data_binding=data_dict)

        result = self.query(q, data_binding=data_dict)

        #print(f"{len(result)} neighbor node(s) found")

        return self.standardize_recordset(recordset=result, dummy_name="e")





    #####################################################################################################

    '''                              ~   READ IN from PANDAS   ~                                      '''

    def ________READ_IN_PANDAS________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################

    def load_pandas(self,
            df :Union[pd.DataFrame, pd.Series], labels :Union[str, List[str], Tuple[str]],
            merge_primary_key=None, merge_overwrite=False,
            rename=None, ignore_nan=True, max_chunk_size=10000) -> [int]:
        """
        Load a Pandas Data Frame (or Series) into Neo4j.
        Each row is loaded as a separate node.

        Columns whose dtype is integer will appear as integer data types in the Neo4j nodes
            (however, if a NaN is present in a Pandas column, it'll automatically be transformed to float)

        Any Pandas' datetime values get converted to Neo4j's format.

        Database indexes are added as needed, if the "merge_primary_key" argument is used.

        TODO: maybe save the Panda data frame's row number as an attribute of the Neo4j nodes, to ALWAYS have a primary key
              maybe allow a bulk auto-increment field
              maybe allow to link all nodes to a given existing one

        :param df:              A Pandas Data Frame (or Series) to import into Neo4j.
                                    If it's a Series, it's treated as a single column (named "value", if it lacks a name)

        :param labels:          A string, or list/tuple of strings - representing one or more Neo4j labels
                                    to use on all the newly-created nodes

        :param merge_primary_key: (OPTIONAL) A string with the name of the field that serves as a primary key
                                    If provided, new records will be merged (rather than added) if they already exist,
                                    as determined by that primary key
                                    TODO: to allow for list of primary_keys
        :param merge_overwrite: (OPTIONAL) Only applicable if "merge_primary_key" is set.
                                    If True then on merge the existing nodes will be completely overwritten with the new data,
                                    otherwise they will be updated with new information (keys that are not present
                                    in the df argument will be left unaltered)
                                    TODO: offer an option to completely ignore the duplicate node

        :param rename:          Optional dictionary to rename the Pandas dataframe's columns to
                                    EXAMPLE {"current_name": "name_we_want"}
        :param ignore_nan       If True, node properties created from columns of dtype float
                                    will only be set if they are not NaN.
                                    (Note: the moment a NaN is present, columns of integers in a dataframe
                                           will automatically become floats)
        :param max_chunk_size:  To limit the number of Pandas rows loaded into the database at one time

        :return:                A (possibly-empty) list of the internal database ID's of the created nodes
        """
        # TODO: ditch empty strings; trim leading/trailing blanks from strings
        #       Consider using the approach from GraphSchema.import_pandas_nodes()

        if isinstance(df, pd.Series):
            # Convert a Pandas Series into a Data Frame
            if df.name is None:
                df = pd.DataFrame(df, columns = ["value"])
            else:
                df = pd.DataFrame(df)


        if rename is not None:
            df = df.rename(rename, axis=1)  # Rename the columns in the Pandas data frame


        # Convert Pandas' datetime format to Neo4j's
        df = self.pd_datetime_to_neo4j_datetime(df)


        # Process the primary keys, if any
        primary_key_s = ''
        if merge_primary_key is not None:
            neo_indexes = self.get_indexes()
            if f"{labels}.{merge_primary_key}" not in list(neo_indexes['name']):
                # Create a new database index
                if type(labels) == str:
                    index_label = labels
                else:
                    index_label = labels[0]     # In case of multiple labels, take the first

                self.create_index(index_label, merge_primary_key)
                time.sleep(1)   # Used to give Neo4j time to populate the index

            primary_key_s = ' {' + f'`{merge_primary_key}`:record[\'{merge_primary_key}\']' + '}'
            # EXAMPLE of primary_key_s , assuming that the argument `merge_primary_key` is "patient_id":
            #                           "{patient_id:record['patient_id']}"
            # Note that "record" is a dummy name used in the Cypher query, further down


        numeric_columns = []
        # Numeric columns are handled differently if the ignore_nan flag is set
        if ignore_nan:
            for col, dtype in df.dtypes.items():        # Loop over all columns and their types
                #if dtype in ['float64', 'float32']:
                if pd.api.types.is_float_dtype(dtype):  # This will cover all floats
                                                        # Note: a column with a NaN is automatically a float even if all values are int
                    numeric_columns.append(col)         # We're making a note of this column being numeric

        if merge_primary_key in numeric_columns:
            assert not (df[merge_primary_key].isna().any()), \
                    f"Cannot merge nodes on NULL values in column `{merge_primary_key}`. " \
                    "Eliminate missing values"


        op = 'MERGE' if merge_primary_key else 'CREATE'   # A "MERGE" or "CREATE" operation, as needed
        if (not merge_primary_key) or merge_overwrite:
            set_operator = ""
        else:
            set_operator = "+"

        cypher_labels = CypherUtils.prepare_labels(labels)


        res = []                                                # Running list of the internal database ID's of the created nodes

        # Determine the number of needed batches (always at least 1)
        number_batches = math.ceil(len(df) / max_chunk_size)    # Note that if the max_chunk_size equals the size of df
                                                                # then we'll just use 1 batch

        batch_list = np.array_split(df, number_batches)         # List of Pandas Data Frames, each resulting from split of original Data Frame
                                                                # from groups of rows

        for df_chunk in batch_list:         # Split the import operation into batches
            # df_chunk is a Pandas Data Frame, with the same columns, but fewer rows, as the original df
            record_list = df_chunk.to_dict(orient='records')    # List of dicts; each dict contains the data for 1 row
                                                                # EXAMPLE: [{'col1': 1, 'col2': 0.5}, {'col1': 2, 'col2': 0.75}]

            if numeric_columns:
                q = f'''
                    WITH $data AS data 
                    UNWIND data AS record 
                    WITH record, [key in $numeric_columns WHERE toString(record[key]) = 'NaN'] as exclude_keys
                    {op} (n {cypher_labels}{primary_key_s}) 
                    SET n {set_operator}= apoc.map.removeKeys(record, exclude_keys)
                    RETURN id(n) as node_id 
                    '''
                cypher_dict = {'data': record_list, 'numeric_columns': numeric_columns}
            else:
                q = f'''
                    WITH $data AS data 
                    UNWIND data AS record 
                    {op} (n {cypher_labels}{primary_key_s}) 
                    SET n {set_operator}= record 
                    RETURN id(n) as node_id 
                    '''
                cypher_dict = {'data':record_list}


            res_chunk = self.query(q, cypher_dict, single_column="node_id")     # A (possibly empty) list of internal ID's
            res += res_chunk
        # END for loop

        return res



    def pd_datetime_to_neo4j_datetime(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        If any column in the given Pandas DataFrame is of dtype datetime or timedelta,
        clone the Data Frame and replace its entries with a Neo4j-friendly datetime type.

        If any change is needed, return a modified COPY of the dataframe;
        otherwise, return the original dataframe (no cloning done)

        Note: one must be vigilant against STRING columns with values that look like datetimes,
              but are not of that type!

        EXAMPLE: an entry such as pd.Timestamp('2023-01-01 00:00:00')
                 will become an object neo4j.time.DateTime(2023, 1, 1, 0, 0, 0, 0)

        :param df:  A Pandas data frame
        :return:    Either the same data frame, or a modified version of a clone of it
        """
        df_copy = None
        found_cols = False

        for col in df.columns:
            if pd.core.dtypes.common.is_datetime_or_timedelta_dtype(df[col]):
                if not found_cols:
                    df_copy = df.copy()     # First time we see this type of columns

                found_cols = True

                df_copy[col] = df_copy[col].map(
                    lambda x: None if pd.isna(x) else neo4j.time.DateTime.from_native(x)
                )

        if found_cols:
            return df_copy
        else:
            return df





    #####################################################################################################

    '''                                      ~   CSV IMPORT   ~                                       '''

    def ________CSV_IMPORT________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################

    def import_csv_nodes_IN_PROGRESS(self, filename :str, labels :Union[str, List[str], Tuple[str]], os="linux",
                               headers=True, rename_fields=None, field_types=None,
                               import_line_number=False, start_line_number=1, line_number_name="line number",
                               link_to_node=None) -> dict:
        """
        TODO: In-progress.  DO NOT USE.   Use load_pandas() instead

        Import data from a CSV file located on the same file system as the Neo4j database,
        and the records represent nodes to be created in the database.

        IMPORTANT:  the file to import MUST be located in the special folder NEO4J_HOME/import,
                    unless the Neo4j configuration file is first modified - and the database restarted!
                    A typical default location, when Neo4j is installed on Linux, is:  /var/lib/neo4j/import

        :param filename:    EXAMPLE in Linux:   "test.csv"
                            EXAMPLE in Windows: "C:/test.csv"
        :param labels:      A string, or list/tuple of strings, representing one or multiple Neo4j labels;
                                it's acceptable to be None
        :param os:          Either "linux" or "win"
        :param headers:     TODO: implement
        :param rename:      TODO: implement
                                Example: {"name": "Product Name", "n_parts": "Number of Parts"}
        :param field_types: (OPTIONAL) if not specified, all values get imported as STRINGS
                                TODO: implement
                                    Example: {"product_id": "int", "cost": "float"}
        :param import_line_number:
        :param start_line_number:
        :param line_number_name:
        :param link_to_node:    (OPTIONAL) If provided, all the newly-created nodes
                                    get linked to the specified existing node.
                                    Example: {"internal_id": 123, "name": "employed_by", "dir": "out"}

        :return:        A dictionary of statistics about the import
        """
        if os == "linux":
            full_filename = f"/{filename}"
        else:
            full_filename = f"///{filename}"

        labels = CypherUtils.prepare_labels(labels)

        q = f'''
            LOAD CSV WITH HEADERS FROM "file:{full_filename}" AS row
            UNWIND row as properties
            CREATE (n {labels}) SET n = properties
            '''

        if import_line_number:
            offset = start_line_number - 2      # Subtracting 2 because the first line of the file contains the field headers
                                                # (i.e. the count would start with 2, in absence of offset)
            q += f", n.{line_number_name} = linenumber() + {offset}"


        if link_to_node:
            # All the newly-created nodes will get linked to an existing node specified by its internal database ID
            if link_to_node["dir"] == "out":
                link = f"MERGE (n)-[:{link_to_node['name']}]->(l)"
            else:
                link = f"MERGE (n)<-[:{link_to_node['name']}]-(l)"

            q = f'''MATCH (l:CLASS)
                    WHERE id(l) = {link_to_node["internal_id"]}
                    WITH l
                    {q}
                    {link}
                '''


        status = self.update_query(q)
        #print(status)
        return status





    #####################################################################################################

    '''                              ~   JSON IMPORT/EXPORT   ~                                       '''

    def ________JSON_IMPORT_EXPORT________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################


    def export_dbase_json(self) -> dict:
        """
        Export the entire Neo4j database as a JSON string.

        IMPORTANT: APOC must be activated in the database, to use this function.
                   Otherwise it'll raise an Exception.
                   Different versions of the Neo4j 4.4 database return different values for the dicts with type "relationship" !!!
                        In the dicts for the "start" and "end" nodes, sometime the "properties" are included, and sometimes not!!!

        EXAMPLE:
        { 'nodes': 2,
          'relationships': 1,
          'properties': 6,
          'data': '[{"type":"node","id":"3","labels":["User"],"properties":{"name":"Adam","age":32,"male":true}},\n
                    {"type":"node","id":"4","labels":["User"],"properties":{"name":"Eve","age":18}},\n
                    {"type":"relationship","id":"1","label":"KNOWS","properties":{"since":2003},"start":{"id":"3","labels":["User"],"properties":{"name":"Eve"}},"end": {"id":"4","labels":["User"],"properties":{"name":"Adam","age":30}}}\n
                   ]'
        }

        SIDE NOTE: the Neo4j *Browser* uses a slightly different format for NODES:
                {
                  "identity": 4,
                  "labels": [
                    "User"
                  ],
                  "properties": {
                    "name": "Eve",
                    "age": 18
                  }
                }
              and a substantially more different format for RELATIONSHIPS:
                {
                  "identity": 1,
                  "start": 3,
                  "end": 4,
                  "type": "KNOWS",
                  "properties": {
                    "since": 2003
                  }
                }

        :return:    A dictionary with the following entries:
                        "nodes":            the number of nodes exported
                        "relationships":    the number of relationships exported
                        "properties":       the number of properties exported
                        "data":             the actual export as a JSON string that encodes a list of dict's
        """
        # TODO: possibly more InterGraph
        #       simplify and standardize the returned values

        cypher = '''
            CALL apoc.export.json.all(null, {useTypes: true, stream: true, jsonFormat: "JSON_LINES"})
            YIELD nodes, relationships, properties, data
            RETURN nodes, relationships, properties, data
            '''
        # TODO: unclear if the part "useTypes: true" is needed
        # TODO: export in batches

        result = self.query(cypher)     # It returns a list with a single element
        export_dict = result[0]         # This will be a dictionary with 4 keys: "nodes", "relationships", "properties", "data"
        #   "nodes", "relationships" and "properties" contain their respective counts

        json_lines = export_dict["data"]
        # Tweak the "JSON_LINES" format to make it a valid JSON string, and more readable.
        # See https://neo4j.com/labs/apoc/4.4/export/json/
        json_str = "[" + json_lines.replace("\n", ",\n ") + "\n]"   # The newlines \n make the JSON much more human-readable
        export_dict["data"] = json_str                              # Replace the "data" value

        #print("export_dict = ", export_dict)

        return export_dict



    def export_nodes_rels_json(self, nodes_query="", rels_query="") -> {}:
        """
        Export the specified nodes, plus the specified relationships, as a JSON string.
        The default empty strings are taken to mean (respectively) ALL nodes/relationships.

        For details on the formats, see export_dbase_json()

        IMPORTANT:  APOC must be activated in the database for this function.
                    Otherwise it'll raise an Exception

        :param nodes_query: A Cypher query to identify the desired nodes (exclusive of RETURN statements)
                                    The dummy variable for the nodes must be "n"
                                    Use "" to request all nodes
                                    EXAMPLE: "MATCH (n) WHERE (n:CLASS OR n:PROPERTY)"
        :param rels_query:   A Cypher query to identify the desired relationships (exclusive of RETURN statements)
                                    The dummy variable for the relationships must be "r"
                                    Use "" to request all relationships (whether or not their end nodes are also exported)
                                    EXAMPLE: "MATCH ()-[r:HAS_PROPERTY]->()"

        :return:    A dictionary specifying the number of nodes exported,
                    the number of relationships, and the number of properties,
                    as well as a "data" field with the actual export as a JSON string

        """
        if nodes_query == "":
            nodes_query = "MATCH (n)"           # All nodes by default

        if rels_query == "":
            rels_query = "MATCH ()-[r]->()"     # All relationships by default

        cypher = f'''
            {nodes_query}
            WITH collect(n) as nds
            OPTIONAL {rels_query}
            WITH nds, collect(r) AS rels
            CALL apoc.export.json.data(nds, rels, null, {{stream: true, jsonFormat: "JSON_LINES"}})
            YIELD nodes, relationships, properties, data
            RETURN nodes, relationships, properties, data
            '''
        # The "OPTIONAL" keyword is necessary in cases where there are no relationships

        # Example of complete Cypher query
        '''
            MATCH (s) WHERE (s:CLASS OR s:PROPERTY) 
            WITH collect(s) as nds
            OPTIONAL MATCH ()-[r:HAS_PROPERTY]->()
            WITH nds, collect(r) AS rels 
            CALL apoc.export.json.data(nds, rels, null, {stream: true, jsonFormat: "ARRAY_JSON"})
            YIELD nodes, relationships, properties, data
            RETURN nodes, relationships, properties, data
        '''

        result = self.query(cypher)     # It returns a list with a single element
        #print("In export_nodes_rels_json(): result = ", result)

        export_dict = result[0]         # This will be a dictionary with 4 keys: "nodes", "relationships", "properties", "data"
                                        #   "nodes", "relationships" and "properties" contain their respective counts

        json_lines = export_dict["data"]
        # Tweak the "JSON_LINES" format to make it a valid JSON string, and more readable.
        # See https://neo4j.com/labs/apoc/4.3/export/json/#export-nodes-relationships-json
        json_str = "[" + json_lines.replace("\n", ",\n ") + "\n]"       # The newlines \n make the JSON much more human-readable
        export_dict["data"] = json_str                                  # Replace the "data" value

        #print("export_dict = ", export_dict)

        return export_dict




    def is_literal(self, value) -> bool:
        """
        Return True if the given value represents a literal (in terms of database storage)

        :param value:
        :return:
        """
        if type(value) == int or type(value) == float or type(value) == str or type(value) == bool:
            return True
        else:
            return False



    def import_json(self, json_str: str, root_labels="import_root_label", parse_only=False, provenance=None) -> List[int]:
        """
        Import the data specified by a JSON string into the database.

        CAUTION: A "postorder" approach is followed: create subtrees first (with recursive calls), then create root last;
        as a consequence, in case of failure mid-import, there's no top root, and there could be several fragments.
        A partial import might need to be manually deleted.

        :param json_str:    A JSON string representing the data to import
        :param root_labels: String, or list of strings, to be used as Neo4j labels for the root node(s)
        :param parse_only:  If True, the parsed data will NOT be added to the database
        :param provenance:  Optional string to store in a "source" attribute in the root node
                                (only used if the top-level JSON structure is an object, i.e. if there's a single root node)

        :return:            List of integer ID's (possibly empty), of the root node(s) created
        """
        #T ODO: maintain a list of all created nodes - so as to be able to delete them all in case of failure.
        # Try to obtain Python data (which ought to be a dict or list) that corresponds to the passed JSON string
        try:
            json_data = json.loads(json_str)    # Turn the string (representing JSON data) into its Python counterpart;
            # at the top level, it should be a dict or list
        except Exception as ex:
            raise Exception(f"Incorrectly-formatted JSON string. {ex}")

        #print("Python version of the JSON file:\n"
        #self.debug_trim_print(json_data, max_len = 250)

        if parse_only:
            return []      # Nothing else to do

        # Import the structure into Neo4j
        result = self.create_nodes_from_python_data(json_data, root_labels)

        # TODO: implement a mechanism whereby, if the above call results in error, the partial database structure created gets erased

        if provenance and type(json_data) == dict:       # If provenance is specified, and the top-level JSON structure is a dictionary
            self.debug_print("Stamping the root node of the import with provenance information in the `source` attribute")
            node_id = result[0]
            self.set_fields(node_id, set_dict={"source": provenance})

        return result




    def create_nodes_from_python_data(self, python_data, root_labels: Union[str, List[str]], level=1) -> List[int]:
        """
        Recursive function to add data from a JSON structure to the database, to create a tree:
        either a single node, or a root node with children.
        A "postorder" approach is followed: create subtrees first (with recursive calls), then create root last.

        If the data is a literal, first turn it into a dictionary using a key named "value".

        Return the Neo4j ID's of the root node(s)

        :param python_data: Python data to import.
                                The data can be a literal, or list, or dictionary
                                - and lists/dictionaries may be nested
        :param root_labels: String, or list of strings, to be used as Neo4j labels for the root node(s)
        :param level:       Recursion level (also used for debugging, to make the indentation more readable)
        :return:            List of integer Neo4j internal ID's (possibly empty), of the root node(s) created
        """
        indent_str = self.indent_chooser(level)
        self.debug_print(f"{indent_str}{level}. ~~~~~:")

        if python_data is None:
            self.debug_print(f"{indent_str}Handling a None.  Returning an empty list")
            return []

        # If the data is a literal, first turn it into a dictionary using a key named "value"
        if self.is_literal(python_data):
            # The data is a literal
            original_data = python_data             # Only used for debug-printing, below
            python_data = {"value": python_data}    # Turn the literal data into a dictionary
            self.debug_print(f"{indent_str}Turning literal ({self.debug_trim(original_data, max_len=200)}) into dict, "
                             f"using `value` as key, as follows: {self.debug_trim(python_data)}")

        if type(python_data) == dict:
            self.debug_print(f"{indent_str}Input is a dict with {len(python_data)} key(s): {list(python_data.keys())}")
            new_root_id = self.dict_importer(d=python_data, labels=root_labels, level=level)
            self.debug_print(f"{indent_str}dict_importer returned new_root_id: {new_root_id}")
            return [new_root_id]

        elif type(python_data) == list:
            self.debug_print(f"{indent_str}Input is a list with {len(python_data)} items")
            children_info = self.list_importer(l=python_data, labels=root_labels, level=level)
            if self.debug:
                print(f"{indent_str}children_info: {children_info}")

            if level == 1:
                return children_info    # Top-level lists require a special treatment (no grouping)
            else:
                # Lists that aren't top-level result in element nodes (or subtree roots)
                # that are all attached to a special parent node that has no attributes
                children_list = []
                for child_id in children_info:
                    #children_list.append( (child_id, root_labels) )
                    children_list.append( {"internal_id": child_id, "rel_name":root_labels} )
                self.debug_print(f"{indent_str}Attaching the root nodes of the list elements to a common parent")
                return [self.create_node_with_links(labels=root_labels, properties=None, links=children_list)]

        else:
            raise Exception(f"Unexpected data type: {type(python_data)}")



    def dict_importer(self, d: dict, labels, level: int) -> int:
        """
        Import data from a Python dictionary.
        If the data is nested, it uses a recursive call to create_nodes_from_python_data()

        :param d:       A Python dictionary with data to import
        :param labels:  String, or list of strings, to be used as Neo4j labels for the node
        :param level:   Integer with recursion level (used just to format debugging output)
        :return:        Integer with the internal database id of the newly-created (top-level) node
        """
        # TODO: pytest

        indent_str = self.indent_chooser(level)

        node_properties = {}    # Dictionary to be filled in with all the properties of the new node
        children_info = []      # A list of pairs (Neo4j ID, relationship name)

        # Loop over all the dictionary entries
        for k, v in d.items():
            self.debug_trim_print(f"{indent_str}*** KEY-> VALUE: {k} -> {v}")

            if self.is_literal(v):
                node_properties[k] = v      # Add the key/value to the running list of properties of the new node
                if self.debug:
                    print(f"{indent_str}The value (`{v}`) is a literal of type {type(v)}. Node properties so far: {node_properties}")
                else:
                    print(f"{indent_str}The value (`{self.debug_trim(v)}`) is a literal of type {type(v)}")      # Concise version

            elif type(v) == dict:
                self.debug_print(f"{indent_str}Processing a dictionary (with {len(v)} keys), using a recursive call:")
                # Recursive call
                new_node_id_list = self.create_nodes_from_python_data(python_data=v, root_labels=k, level=level + 1)
                if len(new_node_id_list) > 1:
                    raise Exception("Internal error: processing a dictionary is returning more than 1 root node")
                elif len(new_node_id_list) == 1:
                    new_node_id = new_node_id_list[0]
                    children_info.append( {"internal_id": new_node_id, "rel_name": k} )  # Append dict entry to the running list
                # Note: if the list is empty, do nothing

            elif type(v) == list:
                self.debug_print(f"{indent_str}Processing a list (with {len(v)} elements):")
                new_children = self.list_importer(l=v, labels=k, level=level)
                for child_id in new_children:
                    children_info.append( {"internal_id": child_id, "rel_name": k} )     # Append dict entry to the running list

            # Note: if v is None, no action is taken.  Dictionary entries with values of None are disregarded


        self.debug_print(f"{indent_str}dict_importer assembled node_properties: {node_properties} | children_info: {children_info}")
        return self.create_node_with_links(labels=labels, properties=node_properties, links=children_info)



    def list_importer(self, l: list, labels, level) -> [int]:
        """
        Import data from a list.
        If the data is nested, it uses a recursive call to create_nodes_from_python_data()

        :param l:       A list with data to import
        :param labels:  String, or list of strings, to be used as Neo4j labels for the node
        :param level:   Integer with recursion level (just used to format debugging output)
        :return:        List (possibly empty) of internal database id's of the newly-created nodes
        """
        # TODO: pytest

        indent_str = self.indent_chooser(level)
        if len(l) == 0:
            self.debug_print(f"{indent_str}The list is empty; so, ignoring it (Returning an empty list)")
            return []

        list_of_child_ids = []
        # Process each element of the list, in turn
        for item in l:
            self.debug_print(f"{indent_str}Making recursive call to process list element...")
            new_node_id_list = self.create_nodes_from_python_data(python_data=item, root_labels=labels, level=level + 1)  # Recursive call
            list_of_child_ids += new_node_id_list   # List concatenation

        if self.debug:
            print(f"{indent_str}list_importer() is returning: {list_of_child_ids}")

        return list_of_child_ids



    def import_json_dump(self, json_str: str, extended_validation = True) -> str:
        """
        Used to import data from a database dump that was done with export_dbase_json() or export_nodes_rels_json().

        Import nodes and relationships into the database, as specified in the JSON code
        that was created by the earlier data dump.

        IMPORTANT: the internal id's of the nodes need to be shifted,
              because one cannot force the Neo4j internal id's to be any particular value...
              and, besides (if one is importing into an existing database), particular id's may already be taken.

        :param json_str:            A JSON string with the format specified under export_dbase_json()
        :param extended_validation: If True, an attempt is made to try to avoid partial imports,
                                        by running extended validations prior to importing
                                        (it will make a first pass thru the data, and hence take longer)

        :return:                    A status message with import details if successful;
                                        or raise an Exception if not.
                                        If an error does occur during import then the import is aborted -
                                        and the number of imported nodes & relationships is returned in the Exception raised.
        """

        try:
            json_list = json.loads(json_str)    # Turn the string (which represents a JSON list) into a list
        except Exception as ex:
            raise Exception(f"import_json_dump(): incorrectly-formatted JSON string. {ex}")

        if self.debug:
            print("json_list: ", json_list)

        assert type(json_list) == list, \
            "import_json_dump(): the JSON string does not represent a list"


        id_shifting = {}    # To map the Neo4j internal ID's specified in the JSON data dump
        #       into the ID's of newly-created nodes

        if extended_validation:
            # Do an initial pass for correctness, to help avoid partial imports.
            # TODO: maybe also check the validity of the start and end nodes of relationships
            for i, item in enumerate(json_list):
                assert type(item) == dict, \
                    f"import_json_dump(): Item in list index {i} should be a dict, but instead it's of type {type(item)}.  Nothing imported.  Item: {item}"
                # We use item.get(key_name) to handle without error situation where the key is missing
                if (item.get("type") != "node") and (item.get("type") != "relationship"):
                    raise Exception(f"import_json_dump(): Item in list index {i} must be a dict with a 'type' key, "
                                    f"whose value is either 'node' or 'relationship'.  Nothing imported.  Item: {item}")

                if item["type"] == "node":
                    if "id" not in item:
                        raise Exception(f"import_json_dump(): Item in list index {i} is marked as 'node' but it lacks an 'id'.  Nothing imported.  Item: {item}")
                    try:
                        int(item["id"])
                    except ValueError:
                        raise Exception(f"import_json_dump(): Item in list index {i} has an 'id' key whose value ({item['id']}) doesn't correspond to an integer.  "
                                        f"Nothing imported.  Item: {item}")

                elif item["type"] == "relationship":
                    if "label" not in item:
                        raise Exception(f"import_json_dump(): Item in list index {i} is marked as 'relationship' but lacks a 'label'.  Nothing imported.  Item: {item}")
                    if "start" not in item:
                        raise Exception(f"import_json_dump(): Item in list index {i} is marked as 'relationship' but lacks a 'start' value.  Nothing imported.  Item: {item}")
                    if "end" not in item:
                        raise Exception(f"import_json_dump(): Item in list index {i} is marked as 'relationship' but lacks a 'end' value.  Nothing imported.  Item: {item}")
                    if "id" not in item["start"]:
                        raise Exception(f"import_json_dump(): Item in list index {i} is marked as 'relationship' but its 'start' value lacks an 'id'.  Nothing imported.  Item: {item}")
                    if "id" not in item["end"]:
                        raise Exception(f"import_json_dump(): Item in list index {i} is marked as 'relationship' but its 'end' value lacks an 'id'.  Nothing imported.  Item: {item}")


        # First, process all the node data, and create the nodes; while doing that, generate the id_shifting map
        num_nodes_imported = 0
        try:
            for item in json_list:
                if item["type"] == "node":
                    #print("ADDING NODE: ", item)
                    #print(f'     Creating node with labels `{item["labels"]}` and properties {item["properties"]}')
                    old_id = int(item["id"])
                    new_id = self.create_node(labels=item.get("labels"), properties=item.get("properties")) # Note: any number of labels can be imported
                                                                                                            #       if item has no labels/properties, None will be passed
                    id_shifting[old_id] = new_id
                    num_nodes_imported += 1
        except Exception as ex:
            raise Exception(f"import_json_dump(): the import process was INTERRUPTED "
                            f"after importing {num_nodes_imported} node(s) and 0 relationship(s). Reason: " + str(ex))


        #print("id_shifting map:", id_shifting)

        # Then process all the relationships, linking to the correct (newly-created) nodes by using the id_shifting map
        # (node: item types that aren't either "node" nor "relationship" are currently being ignored during the import)
        num_rels_imported = 0
        try:
            for item in json_list:
                if item["type"] == "relationship":
                    #print("ADDING RELATIONSHIP: ", item)
                    rel_name = item["label"]
                    #rel_props = item["properties"]
                    rel_props = item.get("properties")      # Also works if no "properties" is present (relationships may lack it)

                    start_id_original = int(item["start"]["id"])
                    end_id_original = int(item["end"]["id"])

                    if start_id_original not in id_shifting:
                        raise Exception(f"cannot add a relationship `{rel_name}` starting at node with id {start_id_original}, because no node with that id was imported")
                    if end_id_original not in id_shifting:
                        raise Exception(f"cannot add a relationship `{rel_name}` ending at node with id {start_id_original}, because no node with that id was imported")

                    start_id_shifted = id_shifting[start_id_original]
                    end_id_shifted = id_shifting[end_id_original]

                    #print(f'     Creating relationship named `{rel_name}` from node {start_id_shifted} to node {end_id_shifted},  with properties {rel_props}')
                    self.link_nodes_by_ids(start_id_shifted, end_id_shifted, rel_name, rel_props)
                    num_rels_imported += 1
        except Exception as ex:
            raise Exception(f"import_json_dump(): the import process was INTERRUPTED "
                            f"after importing {num_nodes_imported} node(s) and {num_rels_imported} relationship(s). Reason: " + str(ex))


        return f"Successful import of {num_nodes_imported} node(s) and {num_rels_imported} relationship(s)"





    #####################################################################################################

    '''                                   ~   VISUALIZATION   ~                                   '''

    def ________VISUALIZATION________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################


    def node_tabular_display(self, node_list :list, fields=None, dummy_name=None, limit=15) -> pd.DataFrame|None:
        """
        Tabular display of the requested fields from the given list of nodes data,
        typically as returned from get_nodes()
        or from the queries such as "MATCH (x:Person) RETURN x, id(x) AS internal_id"

        Node labels and their internal ID's are included in the table *if* they are part of the passed data

        :param node_list:   A list whose elements represent data from nodes;
                                the following EXAMPLES show the different formats can be used for the list elements:

                                {"field_1": 3, "field_2": "hello"}                          # Simple dict of node properties
                                {"field_1": 3, "field_2": "hello",
                                    "internal_id": 123, "node_labels": ["Car", "Vehicle"]}  # Optionally include "internal_id" and/or "node_labels"
                                { "n":  {"field_1": 3, "field_2": "hello"} }                # Outer dict with dummy name
                                { "internal_id": 123, "node_labels": ["Car", "Vehicle"] ,
                                        "n":  {"field_1": 3, "field_2": "hello"} }          # Optionally include "internal_id" and/or "node_labels" in outer list


        :param fields:      A string, or list/tuple of strings, with the name(s) of the desired field(s) to include.
                                If None, ALL fields are included (plus the node labels and internal ID's, if present);
                                if the fields don't match across all records, NaN's will be inserted into the dataframe
        :param dummy_name:  A string to identify where the node data resides in the elements of `node_list`, if not at top level
        :param limit:       Max number of records (nodes) to include

        :return:            If the list of node is empty, None is returned;
                                otherwise, a Panda's DataFrame with a tabular view of the specified fields (properties),
                                with columns in the following order: "node_labels" (if present), all the fields in the order of
                                the `fields` list, "internal_id" (if present)
                                Note: "internal_id" might not show up at the far right if `fields` is None, and different records
                                      have variable field lists
        """
        if (n_nodes := len(node_list)) == 0:
            print("node_tabular_display(): EMPTY list of nodes.")
            return

        feedback = "" if n_nodes <= limit  else  f"  Showing the first {limit}"    # Give feedback about omission of results, if applicable
        print(f"node_tabular_display(): {n_nodes} node(s).  {feedback}\n")


        row_list = []   # Running list of records (dict's with node data of interest)

        if type(fields) == str:
            fields = [fields]       # Turn into list

        for i, node in enumerate(node_list):
            if i >= limit:
                break               # Exceeded the max

            d_simple = {}

            if dummy_name:  # If there is an outer dict
                d = node[dummy_name]    # A dictionary of node properties
                outer = node
            else:
                d = node
                outer = d

            #  Include "node_labels" and/or "internal_id", if present
            if "internal_id" in outer:
                d_simple["internal_id"] = outer["internal_id"]  # Placed first; later will be moved to last column
            if "node_labels" in outer:
                d_simple["node_labels"] = outer["node_labels"]


            if fields is not None:
                # Copy over the requested fields
                for f in fields:
                    d_simple[f] = d.get(f)
            else:
                # Copy over ALL fields, except "node_labels" and "internal_id" (which are handled separately)
                 for k, v in d.items():
                    if (k != "node_labels") and (k != "internal_id"):
                        d_simple[k] = v

            #print(d_simple)
            row_list.append(d_simple)


        df = pd.DataFrame(row_list)   # Turn a list of dict's into a Pandas dataframe

        # Re-oder the columns, to place "internal_id" (if present) last
        if ("internal_id" in df.columns) and (df.columns[0] == "internal_id"):
            col_data = df["internal_id"]          # save the "internal_id" column
            del df["internal_id"]                 # remove it from the DataFrame
            df["internal_id"] = col_data          # reinsert it as the last column

        return df





    #####################################################################################################

    '''                                       ~   UTILS   ~                                           '''

    def ________UTILS________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################


    def sanitize_date_times(self, record :dict, drop_time=False,
                            date_format="%Y/%m/%d", time_format="%H:%M:%S") -> dict:
        """

        :param record:      A python dictionary whose values might include Neo4j "Date" or "DateTime" data types;
                                this dictionary does NOT get altered
        :param drop_time:   [OPTIONAL] If True, any time part in datetime fields will get dropped
        :param date_format: [OPTIONAL] String with format information for dates,
                                as used by the python function strftime().
                                See https://strftime.org/
        :param time_format: [OPTIONAL] String with format information for times

        :return:            A new dictionary, based on `record` but will all the Date/DateTime values converted to strings.
                                By default, a format of the type "2019/01/31 , 18:59:35" is used for datetimes.
        """
        # TODO: this (database-specific) method belongs to the InterGraph class
        # TODO: possibly sanitize other Neo4j data types

        assert type(record) == dict, \
            "sanitize_dates(): argument `record` must be a python dictionary"

        converted_dict = {}

        # Convert any DateTime or Date values to strings
        for key, val in record.items():
            if  type(val) == neo4j.time.DateTime:
                conv = neo4j.time.DateTime.to_native(val)       # This will be of python type datetime.datetime
                if drop_time:
                    converted_dict[key] = conv.strftime(date_format)                        # EXAMPLE: "2000/01/31"
                else:
                    converted_dict[key] = conv.strftime(f"{date_format} , {time_format}")   # EXAMPLE: "2019/01/31 , 18:59:35"

            elif  type(val) == neo4j.time.Date:
                conv = neo4j.time.Date.to_native(val)           # This will be of python type datetime.datetime
                converted_dict[key] = conv.strftime(date_format)                            # EXAMPLE: "2000/01/31"

            else:                                               # NOT a date/time type
                converted_dict[key] = val

        return converted_dict



    def flatten_recordset(self, recordset :[dict], dummy_name=None) -> [dict]:
        """
        Transform a list such as  [{"n": {"name": "Julian", "city": "Berkeley"}},
                                   {"n": {"name": "Val",   "city": "Emeryville"}}]
        (as typically returned by Cypher queries that match entire nodes, in this example with a dummy name of "n")

        into the flattened list (without the outermost layer) such as:
                         [ {"name": "Julian", "city": "Berkeley"} , {"name": "Val", "city": "Emeryville"} ]

        :param recordset:   A list whose elements are python dictionaries
        :param dummy_name:  [OPTIONAL] If not specified, ANY key name will be matched
        :return:            A flattened list where individual items are no longer "indexed" by "dummy variables"
        """
        assert type(recordset) == list, \
            "flatten_recordset(): argument `recordset` must be a list"

        flattened = []

        for record in recordset:
            assert type(record) == dict, \
                "flatten_recordset(): each element in the list passed by `recordset` must be a dictionary"

            if dummy_name:
                assert dummy_name in record, \
                    f'flatten_recordset(): each element in the list passed by `recordset` must have a key named "{dummy_name}"'
                value = record[dummy_name]
            else:
                assert len(record) == 1, \
                    f'flatten_recordset(): each element in the list passed by `recordset` must be a dictionary with exactly 1 key'
                value = next(iter(record.values()))     # Extract the single value in the `record` dict

            flattened.append(value)


        return flattened



    def standardize_recordset(self, recordset :[dict], dummy_name="n"):
        """
        Sanitize and standardize the given recordset, typically as returned by a call to query(),
        obtained from a Cypher query that returned a group of nodes (using the dummy name "n"),
        and optionally also the internal database ID (returned as "internal_id").

        The sanitizing is done by transforming any database-specific date and datetime format to suitable python counterparts.
        The time parts get dropped, and the date is returned in the format yyyy_mm_dd

        If applicable, insert into the records the values of the internal database ID (using the key "internal_id"),
        and/or of the node labels (using the key "node_labels")

        EXAMPLES of queries that generate recordsets in the expected formats, when passed to query():
                "MATCH (n) RETURN n"
                "MATCH (n) RETURN n, id(n) AS internal_id"

        :param recordset:   A list of dict's that contain the key "n" and optionally the key "internal_id".
                                EXAMPLE: [ {"n: {"field1": 1, "field2": "x"}, "internal_id": 88, "node_labels": ["Car", "Vehicle"]},
                                           {"n": {"PatientID": 123, "DOB": neo4j.time.DateTime(2000, 01, 31, 0, 0, 0)}, "internal_id": 4},
                                           {"n: {"timestamp": neo4j.time.DateTime(2003, 7, 15, 18, 59, 35)}, "internal_id": 53},
                                         ]
        :param dummy_name:  [OPTIONAL] If not present, a flattened data structure is assumed - and this function
                                will just sanitize the date/datetime fields

        :return:            A list of dict's that contain all the node properties - sanitized as needed - and,
                                optionally, an extra key named "internal_id"
                                EXAMPLE:  [ {"field1": 1, "field1": "x", "internal_id": 88, "node_labels": ["Car", "Vehicle"]},
                                            {"PatientID": 123, "DOB": "2000/01/31", "internal_id": 4},
                                            {"timestamp": 123, "DOB": "2003/07/15", "internal_id": 53}
                                          ]
        """
        # TODO: perhaps add a flag to query(), to automatically invoke this function at the end;
        #       alternatively, perhaps create a new query_recordset() method that contains query() plus this function.
        result = []
        for record in recordset:
            if dummy_name:
                data = record[dummy_name]   # A dict of field names and values, comprising the properties of the node n.
                                            # EXAMPLE: {'PatientID': 123, 'DOB': neo4j.time.DateTime(2000, 01, 31, 0, 0, 0)}
            else:
                data = record               # A flattened data structure is assumed

            # Convert any DateTime or Date values to strings; the time part is dropped
            data = self.sanitize_date_times(data, drop_time=True)   # TODO: make the time dropping optional

            if "internal_id" in record:
                data["internal_id"] = record["internal_id"]     # Integrate the internal database ID, if provided, into the record

            if "node_labels" in record:
                data["node_labels"] = record["node_labels"]     # Integrate the node labels (a list of strings), if provided, into the record

            result.append(data)

        return result





    #####################################################################################################

    '''                                   ~   DEBUGGING SUPPORT   ~                                   '''

    def ________DEBUGGING_SUPPORT________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################


    def block_query_execution(self) -> None:
        """
        Activate a special testing-only only modality.
        All the Cypher queries will get printed (just like done in debug mode),
        but no database operations will actually be performed.
        This modality will remain in effect until a call is made to unblock_query_execution()

        Caution: many functions will fail validations on the results
                 of the query that wasn't executed.  This modality should probably
                 be combined with an Exception catch

        :return: None
        """
        print("    *** In BLOCK QUERY EXECUTION mode : NO DATABASE OPERATIONS WILL BE PERFORMED ***")
        print("    To resume normal execution, invoke unblock_query_execution()")
        print("    Caution: many functions will fail validations on the results of the query that wasn't executed\n.  "
              "    This mode should probably be used in conjunction with Exception catching")
        self.block_query_execution = True


    def unblock_query_execution(self) -> None:
        """
        Terminate the special "BLOCK QUERY EXECUTION" test mode, entered by a call to block_query_execution().
        From now on, Cypher queries will be normally executed.
        The state of the "debug" mode (only affecting extra diagnostic printing) won't be affected.

        :return:    None
        """
        print("    *** block_query_execution MODE turned off.  Normal execution will resume ***")
        self.block_query_execution = False

        if self.debug:
            print("    Continuing in debugging mode")



    def assert_valid_internal_id(self, internal_id: int) -> None:
        """
        Raise an Exception if the argument is not a valid database internal ID

        :param internal_id: Alleged Neo4j internal database ID
        :return:            None
        """
        CypherUtils.assert_valid_internal_id(internal_id)



    def debug_print(self, info: str, trim=False) -> None:
        """
        If the class property "debug" is set to True,
        print out the passed info string,
        optionally trimming it, if too long

        :param info:
        :param trim:
        :return:        None
        """
        if self.debug:
            if trim:
                info = self.debug_trim(info)

            print(info)



    def debug_trim(self, data, max_len = 150) -> str:
        """
        Abridge the given data (first turning it into a string if needed), if excessively long,
        using ellipses " ..." for the omitted data.
        Return the abridged data.

        :param data:    String with data to possibly abridge
        :param max_len: Max number of characters to show from the data argument
        :return:        The (possibly) abridged text
        """
        text = str(data)
        if len(text) > max_len:
            return text[:max_len] + " ..."
        else:
            return text


    def debug_trim_print(self, data, max_len = 150) -> None:
        """
        Abridge the given data (first turning it into a string if needed),
        if it is excessively long; then print it

        :param data:    String with data to possibly abridge, and then print
        :param max_len: Max number of characters to show from the data argument
        :return:        None
        """
        print(self.debug_trim(data, max_len))



    def indent_chooser(self, level: int) -> str:
        """
        Create an indent based on a "level": handy for debugging recursive functions

        :param level:
        :return:
        """
        indent_spaces = level*4
        indent_str = " " * indent_spaces        # Repeat a blank character the specified number of times
        return indent_str
