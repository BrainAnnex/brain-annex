# This file contains 3 helper classes for the NeoAccess library:
#       - NodeSpecs         To store the specs to identify one or more nodes (the "RAW match structure")
#       - CypherMatch       To store Cypher fragments & data-binding dict, to identify one or more nodes (the "PROCESSED match structure")
#       - CypherUtils       Static class to pre-process node specs, plus misc. Cypher-related utilities

from typing import Union, List, Tuple


class CombinedExperimental:


    def __init__(self, internal_id=None,
                 labels=None, key_name=None, key_value=None,
                 properties=None,
                 clause=None, clause_dummy_name="n"):
        """
        ALL THE ARGUMENTS ARE OPTIONAL (no arguments at all means "match everything in the database")

        :param internal_id: An integer or string with the node's internal database ID.
                                If specified, it will lead to all the remaining arguments being DISREGARDED (though saved)

        :param labels:      A string (or list/tuple of strings) specifying one or more node labels.
                                (Note: blank spaces ARE allowed in the strings)
                                EXAMPLES:  "cars"
                                            ("cars", "powered vehicles")
                            Note that if multiple labels are given, then only nodes possessing ALL of them will be matched;
                            at present, there's no way to request an "OR" operation on labels

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
                                            ("n.weight < $max_weight", {"max_weight": 100})

        :param clause_dummy_name: A string with a name by which to refer to the nodes (by default, "n") in the clause;
                                only used if a `clause` argument is passed (in the absence of a clause, it's stored as None)
        """
        # The following group of object variables can be thought of as
        #   the "RAW match structure", to indentify a database node, or group of nodes.
        #   Any of the variables could be None
        self.internal_id = internal_id              # Internal database ID (an int or string)
        self.labels = labels                        # A string (or list/tuple of strings)
        self.key_name = key_name                    # A string with a property name (not necessarily a primary key)
        self.key_value = key_value
        self.properties = properties                # A python dict, containing both the passed properties
                                                    #   and the requested key/value pair, if applicable
        self.clause = clause                        # EXAMPLES:
                                                    # EXAMPLES:  "n.age < 25 AND n.income > 100000"
                                                    #            ("n.weight < $max_weight", {"max_weight": 100})
        self.clause_dummy_name = clause_dummy_name  # EXAMPLE: "n"
                                                    #   Note: if no clause is present, it will be None

        # The following group of object variables can be thought of as
        #   the "PROCESSED match structure",
        #   i.e. data ready to be used for query parts to identify the node or nodes
        #   Note: the values get set further below
        self.node = None                # It contains filters for labels, for all the passed properties,
                                        #       and for the requested key/value pair, as applicable
                                        # EXAMPLE: "(n :`person` {`gender`: $n_par_1, `age`: $n_par_2})"
        self.where = None               # EXAMPLES: "id(n) = 123"
                                        #           "n.income > 90000 OR n.state = 'CA'"
        self.data_binding = None        # For all the passed properties,
                                        #   and for the requested key/value pair, as applicable
                                        #   EXAMPLE: {"n_par_1": "F", "n_par_2": 22}
        self.dummy_node_name = None     # Used for matching the node(s).  EXAMPLE: "n"
        self.cypher = None              # The complete Cypher query, exclusive of RETURN and later parts


        # Validate all the passed arguments
        if internal_id is not None:
            assert CypherUtils.valid_internal_id(internal_id), \
                f"NodeSpecs(): the argument `internal_id` ({internal_id}) is not a valid internal database ID value"


        if labels is not None:
            assert (type(labels) == str) or (type(labels) == list) or (type(labels) == tuple), \
                f"NodeSpecs(): the argument `labels`, if provided, must be a string, or a list/tuple of strings"


        if key_name is not None:
            assert type(key_name) == str, \
                f"NodeSpecs(): the argument `key_name`, if provided, must be a string"

            key_name = key_name.strip()           # Zap any leading/trailing blanks

            assert key_value is not None, \
                f"NodeSpecs(): if the argument `key_name` is provided, there must also be a `key_value` argument"


        if properties is not None:
            assert type(properties) == dict, \
                f"NodeSpecs(): the argument `properties`, if provided, must be a python dictionary"

        if clause is not None:
            assert (type(clause) == str) or (type(clause) == list) or (type(clause) == tuple), \
                f"NodeSpecs(): the argument `clause`, if provided, must be a string or a pair.  EXAMPLE: 'n.age > 21'"
            if type(clause) != str:
                # Scenario where the clause is meant to be a pair (str, dict)
                assert len(clause) == 2, \
                    "NodeSpecs(): the argument `clause`, if provided as tuple or list, must have exactly 2 elements.  " \
                    "EXAMPLE: ('n.weight < $max_weight', {'max_weight': 100})"

                clause_1, clause_2 = clause     # Unpack
                assert type(clause_1) == str, \
                    "NodeSpecs(): the first element of the pair passed to the argument `clause` must be a string.  " \
                    "EXAMPLE: ('n.weight < $max_weight', {'max_weight': 100})"
                assert clause_1.strip() != "", \
                    "NodeSpecs(): the first element of the pair passed to the argument `clause` cannot be an empty string.  " \
                    "EXAMPLE: ('n.weight < $max_weight', {'max_weight': 100})"
                assert type(clause_2) == dict, \
                    "NodeSpecs(): the second element of the pair passed to the argument `clause` must be a dict.  " \
                    "EXAMPLE: ('n.weight < $max_weight', {'max_weight': 100})"



        if clause is None:
            self.clause_dummy_name = None      # In this scenario, the dummy name isn't yet used, and any name could be used


        if key_name and (key_value is None):  # CAUTION: key_value might legitimately be 0 or "" (hence the "is None")
            raise Exception("NodeSpecs(): If `key_name` is specified, so must be `key_value`")

        if (key_value is not None) and not key_name:
            raise Exception("NodeSpecs(): If `key_value` is specified, so must be `key_name`")


        if properties is None:
            properties = {}

        if key_name in properties:
            raise Exception(f"NodeSpecs(): Name conflict between the specified key_name (`{key_name}`) "
                            f"and one of the keys in properties ({properties})")

        if key_name and key_value:
            properties[key_name] = key_value


        self.process_query_specs()    # Set the "processed" properties



    def process_query_specs(self, dummy_node_name_if_missing="n"):
        """
        :param dummy_node_name_if_missing:  String that will be used ONLY if
                                                self.clause_dummy_name was not already set during instantiation
        """
        # If a value is already present in the raw match structure,
        # it takes priority
        if self.clause_dummy_name is None:
            dummy_node_name = dummy_node_name_if_missing
        else:
            dummy_node_name = self.clause_dummy_name

        assert dummy_node_name is not None, \
                "NodeSpecs(): `dummy_node_name` cannot be None"


        """
        IMPORTANT:  By our convention -
                1) if internal_id is provided, all other conditions are DISREGARDED;
                2) if it's missing, an implicit "AND" operation applies to all the specified conditions
                
                TODO: maybe ditch (1) and give an option to what boolean to use in (2)
        """
        if self.internal_id is not None:    # If an internal node ID is specified, it over-rides all the other conditions
                                            # (note: internal_id might be 0)
            self.node = f"({dummy_node_name})"
            self.where = f"id({dummy_node_name}) = {self.internal_id}"
            self.data_binding = {}
            self.dummy_node_name = dummy_node_name
            self.cypher = f"MATCH {self.node} WHERE {self.where}"
            return


        # Turn labels (string or list/tuple of strings) into a string suitable for inclusion into Cypher
        cypher_labels = CypherUtils.prepare_labels(self.labels)     # EXAMPLES:     ":`patient`"
                                                                    #               ":`CAR`:`INVENTORY`"

        if self.clause is None:
            cypher_clause = ""
            cypher_dict = {}
        elif type(self.clause) == str:
            cypher_clause = self.clause
            cypher_dict = {}
        else:
            (cypher_clause, cypher_dict) = self.clause      # Unpack clauses that are in the form of a pair

            if cypher_dict is None:
                cypher_dict = {}

            self.clause = cypher_clause


        if self.properties == {}:
            clause_from_properties = ""
        else:
            # Transform the dictionary properties into a string describing its corresponding Cypher clause,
            #       plus a corresponding data-binding dictionary.
            #       (assuming an implicit AND between the equalities described by the terms in the dictionary)
            #
            #       EXAMPLE:
            #               properties: {"gender": "F", "year first met": 2003}
            #           will lead to:
            #               clause_from_properties = "{`gender`: $n_par_1, `year first met`: $n_par_2}"
            #               props_data_binding = {'n_par_1': "F", 'n_par_2': 2003}

            (clause_from_properties, props_data_binding) = CypherUtils.dict_to_cypher(self.properties, prefix=dummy_node_name + "_par_")

            if cypher_dict == {}:
                cypher_dict = props_data_binding        # The properties dictionary is to be used as the only Cypher-binding dictionary
            else:
                # Merge the properties dictionary into the existing cypher_dict, PROVIDED that there's no conflict
                overlap = cypher_dict.keys() & props_data_binding.keys()    # Take the set intersection
                if overlap != set():                                        # If not equal to the empty set
                    raise Exception(f"The data-binding dictionary in the `clause` argument should not contain any keys of the form `{dummy_node_name}_par_i`, where i is an integer. "
                                    f"Those names are reserved for internal use. Conflicting keys: {overlap}")

                cypher_dict.update(props_data_binding)      # Merge the properties dictionary into the existing cypher_dict


        # Start constructing the Cypher string
        self.node = f"({dummy_node_name} {cypher_labels} {clause_from_properties})"

        if cypher_clause:
            cypher_clause = cypher_clause.strip()           # Zap any leading/trailing blanks

        # Save all the processed data to be used for query parts to identify the node or nodes
        self.where = cypher_clause
        self.data_binding = cypher_dict
        self.dummy_node_name = dummy_node_name
        if self.where:
            self.cypher = f"MATCH {self.node} WHERE {self.where}"
        else:
            self.cypher = f"MATCH {self.node}"



    def __str__(self) -> str:
        """
        Return a description of this object

        :return:
        """
        str_1 = f"RAW match structure (object of class NodeSpecs):\n" \
                f"    internal_id: {self.internal_id}" \
                f"    labels: {self.labels}" \
                f"    key_name: {self.key_name}" \
                f"    key_value: {self.key_value}" \
                f"    properties: {self.properties}" \
                f"    clause: {self.clause}" \
                f"    clause_dummy_name: {self.clause_dummy_name}"

        str_2 = f"CYPHER-PROCESSED match structure (object of class CypherMatch):\n" \
                f"    node: {self.node}" \
                f"    where: {self.where}" \
                f"    data_binding: {self.data_binding}" \
                f"    dummy_node_name: {self.dummy_node_name}"

        return str_1 + "\n\n" + str_2



    def extract_node(self) -> str:
        """
        Return the node information to be used in composing Cypher queries

        :return:        A string with the node information, as needed by Cypher queries.  EXAMPLES:
                            "(n  )"
                            "(p :`person` )"
                            "(n :`car`:`surplus inventory` )"
                            "(n :`person` {`gender`: $n_par_1, `age`: $n_par_2})"
        """
        return self.node


    def extract_dummy_name(self) -> str:
        """
        Return the dummy node _name to be used in composing Cypher queries

        :return:    A string with the dummy node name to use in the Cypher query (often "n" , or "to" , or "from")
        """
        return self.dummy_node_name


    def unpack_match(self) -> tuple:
        """
        Return a tuple containing:
        (node, where, data_binding, dummy_node_name) ,
        for use in composing Cypher queries

        :return:    A tuple containing (node, where, data_binding, dummy_node_name)
                        1) "node":  a string, defining a node in a Cypher query,
                                    incl. parentheses but *excluding* the "MATCH" keyword
                        2) "where": a string, defining the "WHERE" part of the subquery (*excluding* the "WHERE"),
                                    if applicable;  otherwise, a blank
                        3) "data_binding":      a (possibly empty) data-binding dictionary
                        4) "dummy_node_name":   a string used for the node name inside the Cypher query (by default, "n");
                                                potentially relevant to the "node" and "where" values
        """
        return (self.node, self.where , self.data_binding, self.dummy_node_name)



    def extract_where_clause(self) -> str:
        """
        Cleanup the WHERE clause, and prefix the "WHERE" keyword as needed

        :return:
        """
        # TODO: new method to test
        return CypherUtils.prepare_where([self.where])



    def assert_valid_structure(self) -> None:
        """
        Verify that the object is a valid one (i.e., correctly initialized); if not, raise an Exception
        TODO: NOT IN CURRENT USE.  Perhaps to phase out, or keep it but tighten its tests

        :return:        None
        """
        assert type(self.node) == str, "the `node` attribute is not a string, as expected"
        assert type(self.where) == str, f"the `where` attribute is not a string, as expected; instead, it is {self.where}"
        assert type(self.data_binding) == dict, "the `data_binding` attribute is not a dictionary, as expected"
        assert type(self.dummy_node_name) == str, "the `dummy_node_name` attribute is not a string, as expected"







######################################################################################################################


class NodeSpecs:
    """
    Helper class.
    Meant as a PRIVATE class; not indicated for the end user.
    
    Validates and stores all the passed specifications (the "RAW match structure"),
    that are used to identify a node or group of nodes.

    Note:   NO database operation is actually performed

    IMPORTANT:  By our convention -
                    if internal_id is provided, all other conditions are DISREGARDED;
                    if it's missing, an implicit AND operation applies to all the specified conditions
                (Regardless, all the passed data is stored in this object)
    """

    def __init__(self, internal_id=None,
                 labels=None, key_name=None, key_value=None,
                 properties=None,
                 clause=None, clause_dummy_name="n"):
        """
        ALL THE ARGUMENTS ARE OPTIONAL (no arguments at all means "match everything in the database")

        :param internal_id: An integer with the node's internal database ID.
                                If specified, it will lead to all the remaining arguments being DISREGARDED (though saved)

        :param labels:      A string (or list/tuple of strings) specifying one or more Neo4j labels.
                                (Note: blank spaces ARE allowed in the strings)
                                EXAMPLES:  "cars"
                                            ("cars", "powered vehicles")
                            Note that if multiple labels are given, then only nodes possessing ALL of them will be matched;
                            at present, there's no way to request an "OR" operation on labels

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
                                            ("n.weight < $max_weight", {"max_weight": 100})

        :param clause_dummy_name: A string with a name by which to refer to the nodes (by default, "n") in the clause;
                                only used if a `clause` argument is passed (in the absence of a clause, it's stored as None)
        """
        # Validate all the passed arguments
        if internal_id is not None:
            assert CypherUtils.valid_internal_id(internal_id), \
                f"NodeSpecs(): the argument `internal_id` ({internal_id}) is not a valid internal database ID value"

        if labels is not None:
            assert (type(labels) == str) or (type(labels) == list) or (type(labels) == tuple), \
                f"NodeSpecs(): the argument `labels`, if provided, must be a string, or a list/tuple of strings"

        if key_name is not None:
            assert type(key_name) == str, \
                f"NodeSpecs(): the argument `key_name`, if provided, must be a string"
            assert key_value is not None, \
                f"NodeSpecs(): if the argument `key_name` is provided, there must also be a `key_value` argument"

        if properties is not None:
            assert type(properties) == dict, \
                f"NodeSpecs(): the argument `properties`, if provided, must be a python dictionary"

        if clause is not None:
            assert (type(clause) == str) or (type(clause) == list) or (type(clause) == tuple), \
                f"NodeSpecs(): the argument `clause`, if provided, must be a string or a pair.  EXAMPLE: 'n.age > 21'"
            if type(clause) != str:
                assert len(clause) == 2, \
                    f"NodeSpecs(): the argument `clause`, if provided as tuple or list, must have exactly 2 elements.  " \
                    f"EXAMPLE: ('n.weight < $max_weight', {'max_weight': 100})"
                    


        if clause is None:
            clause_dummy_name = None      # In this scenario, the dummy name isn't yet used, and any name could be used


        # The following group of object variables can be thought of as
        #   the "RAW match structure".  Any of the variables could be None
        self.internal_id = internal_id
        self.labels = labels
        self.key_name = key_name
        self.key_value = key_value
        self.properties = properties
        self.clause = clause
        self.clause_dummy_name = clause_dummy_name



    def __str__(self) -> str:
        """
        Return a description of this object

        :return:
        """
        return f"RAW match structure (object of class NodeSpecs):\n" \
                f"    internal_id: {self.internal_id}" \
                f"    labels: {self.labels}" \
                f"    key_name: {self.key_name}" \
                f"    key_value: {self.key_value}" \
                f"    properties: {self.properties}" \
                f"    clause: {self.clause}" \
                f"    clause_dummy_name: {self.clause_dummy_name}"




######################################################################################################################

class CypherMatch:
    """
    Helper class.
    Meant as a PRIVATE class; not indicated for the end user.
    
    Objects of this class (sometimes referred to as a "PROCESSED match structures")
    are used to facilitate a user to specify a node in a wide variety of ways - and
    save those specifications, in a "pre-digested" way, to use as needed in Cypher queries.

    NO extra database operations are involved.
    
    They store the following 4 properties:

        1) "node":  a string, defining a node in a Cypher query, incl. parentheses but *excluding* the "MATCH" keyword
        2) "where": a string, defining the "WHERE" part of the subquery (*excluding* the "WHERE"), if applicable;
                    otherwise, a blank
        3) "data_binding":      a (possibly empty) data-binding dictionary
        4) "dummy_node_name":   a string used for the node name inside the Cypher query (by default, "n");
                                potentially relevant to the "node" and "where" values

        EXAMPLES:
            *   node: "(n)"
                    where: ""
                    data_binding: {}
                    dummy_node_name: "n"
            *   node: "(p :`person` )"
                    where: ""
                    data_binding: {}
                    dummy_node_name: "p"
            *   node: "(n  )"
                    where: "id(n) = 123"
                    data_binding: {}
                    dummy_node_name: "n"
            *   node: "(n :`car`:`surplus inventory` )"
                    where: ""
                    data_binding: {}
                    dummy_node_name: "n"
            *    node: "(n :`person` {`gender`: $n_par_1, `age`: $n_par_2})"
                    where: ""
                    data_binding: {"n_par_1": "F", "n_par_2": 22}
                    dummy_node_name: "n"
            *   node: "(n :`person` {`gender`: $n_par_1, `age`: $n_par_2})"
                    where: "n.income > 90000 OR n.state = 'CA'"
                    data_binding: {"n_par_1": "F", "n_par_2": 22}
                    dummy_node_name: "n"
            *   node: "(n :`person` {`gender`: $n_par_1, `age`: $n_par_2})"
                    where: "n.income > $min_income"
                    data_binding: {"n_par_1": "F", "n_par_2": 22, "min_income": 90000}
                    dummy_node_name: "n"
    """
    
    def __init__(self, node_specs, dummy_node_name_if_missing=None):
        """


        :param node_specs:                  Object of type "NodeSpecs"
        :param dummy_node_name_if_missing:  String that will be used ONLY if the object passed to in node_specs
                                                lacks that attribute
        """
        # If a value is already present in the raw match structure,
        # it takes priority
        if node_specs.clause_dummy_name is None:
            dummy_node_name = dummy_node_name_if_missing
        else:
            dummy_node_name = node_specs.clause_dummy_name

        assert dummy_node_name is not None, \
                "The class `CypherMatch` cannot be instantiated with a missing dummy node name"


        """
        IMPORTANT:  By our convention -
                1) if internal_id is provided, all other conditions are DISREGARDED;
                2) if it's missing, an implicit "AND" operation applies to all the specified conditions
                
                TODO: maybe ditch (1) and give an option to what boolean to use in (2)
        """
        if node_specs.internal_id is not None:  # If an internal node ID is specified, it over-rides all the other conditions
                                                # CAUTION: internal_id might be 0 ; that's a valid Neo4j node ID
            cypher_match = f"({dummy_node_name})"
            cypher_where = f"id({dummy_node_name}) = {node_specs.internal_id}"
            self.node = cypher_match
            self.where = cypher_where
            self.data_binding = {}
            self.dummy_node_name = dummy_node_name
            return



        # Turn labels (string or list/tuple of strings) into a string suitable for inclusion into Cypher
        cypher_labels = CypherUtils.prepare_labels(node_specs.labels)       # EXAMPLES:     ":`patient`"
                                                                            #               ":`CAR`:`INVENTORY`"

        # Extract all the data from the "NodeSpecs" object
        key_name=node_specs.key_name
        key_value=node_specs.key_value
        properties=node_specs.properties
        subquery=node_specs.clause

        if key_name and key_value is None:  # CAUTION: key_value might legitimately be 0 or "" (hence the "is None")
            raise Exception("If key_name is specified, so must be key_value")

        if key_value and not key_name:
            raise Exception("If key_value is specified, so must be key_name")


        if properties is None:
            properties = {}

        if key_name in properties:
            raise Exception(f"Name conflict between the specified key_name ({key_name}) "
                            f"and one of the keys in properties ({properties})")

        if key_name and key_value:
            properties[key_name] = key_value


        if subquery is None:
            cypher_clause = ""
            cypher_dict = {}
        elif type(subquery) == str:
            cypher_clause = subquery
            cypher_dict = {}
        else:
            (cypher_clause, cypher_dict) = subquery
            if (cypher_clause is None) or (cypher_clause.strip() == ""):    # Zap any leading/trailing blanks
                cypher_clause = ""
                cypher_dict = {}
            elif cypher_dict is None:
                cypher_dict = {}


        if not properties:
            clause_from_properties = ""
        else:
            # Transform the dictionary properties into a string describing its corresponding Cypher clause,
            #       plus a corresponding data-binding dictionary.
            #       (assuming an implicit AND between the equalities described by the terms in the dictionary)
            #
            #       EXAMPLE:
            #               properties: {"gender": "F", "year first met": 2003}
            #           will lead to:
            #               clause_from_properties = "{`gender`: $n_par_1, `year first met`: $n_par_2}"
            #               props_data_binding = {'n_par_1': "F", 'n_par_2': 2003}

            (clause_from_properties, props_data_binding) = CypherUtils.dict_to_cypher(properties, prefix=dummy_node_name + "_par_")

            if not cypher_dict:
                cypher_dict = props_data_binding        # The properties dictionary is to be used as the only Cypher-binding dictionary
            else:
                # Merge the properties dictionary into the existing cypher_dict, PROVIDED that there's no conflict
                overlap = cypher_dict.keys() & props_data_binding.keys()    # Take the set intersection
                if overlap != set():                                        # If not equal to the empty set
                    raise Exception(f"The data-binding dictionary in the `subquery` argument should not contain any keys of the form `{dummy_node_name}_par_i`, where i is an integer. "
                                    f"Those names are reserved for internal use. Conflicting keys: {overlap}")

                cypher_dict.update(props_data_binding)      # Merge the properties dictionary into the existing cypher_dict


        # Start constructing the Cypher string
        cypher_match = f"({dummy_node_name} {cypher_labels} {clause_from_properties})"

        if cypher_clause:
            cypher_clause = cypher_clause.strip()           # Zap any leading/trailing blanks

        # Save all the processed data to be used for query parts to identify the node or nodes
        self.node = cypher_match
        self.where = cypher_clause
        self.data_binding = cypher_dict
        self.dummy_node_name = dummy_node_name



    def __str__(self) -> str:
        """
        Return a description of this object
        :return:
        """
        return f"CYPHER-PROCESSED match structure (object of class CypherMatch):\n" \
               f"    node: {self.node}" \
               f"    where: {self.where}" \
               f"    data_binding: {self.data_binding}" \
               f"    dummy_node_name: {self.dummy_node_name}"



    def extract_node(self) -> str:
        """
        Return the node information to be used in composing Cypher queries

        :return:        A string with the node information, as needed by Cypher queries.  EXAMPLES:
                            "(n  )"
                            "(p :`person` )"
                            "(n :`car`:`surplus inventory` )"
                            "(n :`person` {`gender`: $n_par_1, `age`: $n_par_2})"
        """
        return self.node


    def extract_dummy_name(self) -> str:
        """
        Return the dummy node _name to be used in composing Cypher queries

        :return:        A string with the dummy node name (often "n" , or "to" , or "from")
        """
        return self.dummy_node_name


    def unpack_match(self) -> tuple:
        """
        Return a tuple containing:
        (node, where, data_binding, dummy_node_name) ,
        for use in composing Cypher queries

        :return:    A tuple containing (node, where, data_binding, dummy_node_name)
                        1) "node":  a string, defining a node in a Cypher query,
                                    incl. parentheses but *excluding* the "MATCH" keyword
                        2) "where": a string, defining the "WHERE" part of the subquery (*excluding* the "WHERE"),
                                    if applicable;  otherwise, a blank
                        3) "data_binding":      a (possibly empty) data-binding dictionary
                        4) "dummy_node_name":   a string used for the node name inside the Cypher query (by default, "n");
                                                potentially relevant to the "node" and "where" values
        """
        return (self.node, self.where , self.data_binding, self.dummy_node_name)



    def extract_where_clause(self) -> str:
        """
        Cleanup the WHERE clause, and prefix the "WHERE" keyword as needed

        :return:
        """
        # TODO: new method to test
        return CypherUtils.prepare_where([self.where])



    def assert_valid_structure(self) -> None:
        """
        Verify that the object is a valid one (i.e., correctly initialized); if not, raise an Exception
        TODO: NOT IN CURRENT USE.  Perhaps to phase out, or keep it but tighten its tests

        :return:        None
        """
        assert type(self.node) == str, "the `node` attribute is not a string, as expected"
        assert type(self.where) == str, f"the `where` attribute is not a string, as expected; instead, it is {self.where}"
        assert type(self.data_binding) == dict, "the `data_binding` attribute is not a dictionary, as expected"
        assert type(self.dummy_node_name) == str, "the `dummy_node_name` attribute is not a string, as expected"





######################################################################################################################

class CypherUtils:
    """
    Helper STATIC class.
    Meant as a PRIVATE class; not indicated for the end user.
    """

    @classmethod
    def process_match_structure(cls, handle :Union[int, str, dict, NodeSpecs], dummy_node_name="n", caller_method=None) -> CypherMatch:
        """
        Accept either a valid internal database node ID, or a "NodeSpecs" object (representing a "raw match"),
        and turn it into a "CypherMatch" object (representing a "processed match")

        Note: no database operation is performed

        :param handle:          EITHER a valid internal database ID (int or string),
                                    OR a python dictionary (with property matches to require),
                                    OR a "NodeSpecs" object (containing data to identify a node or set of nodes)

        :param dummy_node_name: A string that will be used inside a Cypher query, to refer to nodes
        :param caller_method:   [OPTIONAL] String with name of caller method, only used for error messages

        :return:                A "CypherMatch" object (representing a "processed match"), used to identify a node,
                                    or group of nodes
        """
        if type(handle) == NodeSpecs:
            return CypherMatch(handle, dummy_node_name_if_missing=dummy_node_name)

        if type(handle) == dict:
            node_specs = NodeSpecs(properties=handle)
            return CypherMatch(node_specs, dummy_node_name_if_missing=dummy_node_name)

        # Since the `handle` argument is not on object of class "NodeSpecs", nor a dict,
        # then it's expected to be a valid internal dbase ID
        if cls.valid_internal_id(handle):    # If the argument "handle" is a valid internal database ID
            node_specs = NodeSpecs(internal_id=handle)      # Instantiate an object of type "NodeSpecs"
            return CypherMatch(node_specs, dummy_node_name_if_missing=dummy_node_name)
        else:
            if caller_method is None:
                caller_method = "process_match_structure"   # This is used for the error message, below
            raise Exception(f"{caller_method}(): the `match` argument is neither a valid internal database ID, "
                        f"nor an object of type 'cypher_utils.NodeSpecs' ; the passed value is: {handle}")



    @classmethod
    def assemble_cypher_blocks(cls, handle :Union[int, str, dict, NodeSpecs], caller_method=None) -> tuple:
        """

        :param handle:          EITHER a valid internal database ID (int or string),
                                    OR a python dictionary (with property matches to require),
                                    OR a "NodeSpecs" object (containing data to identify a node or set of nodes)

        :param caller_method:   [OPTIONAL] String with name of caller method, only used for error messages

        :return:                A tuple containing (node, where, data_binding, dummy_node_name)
                                    1) "node":  a string, defining a node in a Cypher query,
                                                incl. parentheses but *excluding* the "MATCH" keyword
                                    2) "where": a string, defining the "WHERE" part of the subquery
                                                (*excluding* the "WHERE"),
                                                if applicable;  otherwise, a blank
                                    3) "data_binding":      a (possibly empty) data-binding dictionary
                                    4) "dummy_node_name":   a string used for the node name inside the Cypher query (by default, "n");
                                                            potentially relevant to the "node" and "where" values
        """
        match_structure = cls.process_match_structure(handle=handle, caller_method=caller_method)
        return match_structure.unpack_match()



    @classmethod
    def check_match_compatibility(cls, match1: CypherMatch, match2: CypherMatch) -> None:
        """
        If the two given "CypherMatch" objects (i.e. PROCESSED match structures)
        are incompatible - in terms of collision in their dummy node names -
        raise an Exception.

        :param match1:  A CypherMatch" object to be used to identify a node, or group of nodes
        :param match2:  A CypherMatch" object to be used to identify a node, or group of nodes
        :return:        None
        """
        assert match1.dummy_node_name != match2.dummy_node_name, \
            f"check_match_compatibility(): conflict between 2 matches " \
            f"using the same dummy node name ({match1.dummy_node_name}). " \
            f"Make sure to pass different dummy names"



    @classmethod
    def combined_where(cls, match1: CypherMatch, match2: CypherMatch, check_compatibility=True) -> str:
        """
        Given the two "CypherMatch" objects (i.e. PROCESSED match structures),
        return the combined version of all their WHERE statements.
        Also prefix the WHERE keyword to the result (if appropriate);
        if there are no clauses, an empty string is returned (without the WHERE keyword.)
        For details, see prepare_where()

        :param match1:  A CypherMatch" object to be used to identify a node, or group of nodes
        :param match2:  A CypherMatch" object to be used to identify a node, or group of nodes
        :param check_compatibility: Use True if the individual matches are meant to refer to different nodes,
                                        and need to make sure there's no conflict in the dummy node names
        :return:        A string with the combined WHERE statement,
                            suitable for inclusion into a Cypher query (empty if there were no subclauses)
        """
        if check_compatibility:
            cls.check_match_compatibility(match1, match2)

        where_list = [match1.where, match2.where]
        return cls.prepare_where(where_list)


    @classmethod
    def combined_data_binding(cls, match1: CypherMatch, match2: CypherMatch) -> dict:
        """
        Given the two "CypherMatch" objects (i.e. PROCESSED match structures),
        return the combined version of all their data binding dictionaries.
        NOTE:  if the individual matches are meant to refer to different nodes,
                    need to first make sure there's no conflict in the dummy node names -
                    use check_match_compatibility() as needed.
                    In practice, combined_where() is typically run whenever combined_data_binding() is -
                    and the former can take care of checking for compatibility

        :param match1:  A CypherMatch" object to be used to identify a node, or group of nodes
        :param match2:  A CypherMatch" object to be used to identify a node, or group of nodes
        :return:        A (possibly empty) dict with the combined data binding dictionaries,
                            suitable for inclusion into a Cypher query
        """
        combined_data_binding = match1.data_binding     # Our 1st dict
        new_data_binding = match2.data_binding          # Our 2nd dict
        combined_data_binding.update(new_data_binding)  # Merge the second dict into the first one

        return combined_data_binding




    ############ The following methods make no reference to any "match" object (neither NodeSpecs nor CypherMatch objects)

    @classmethod
    def assert_valid_internal_id(cls, internal_id :Union[int, str]) -> None:
        """
        Raise an Exception if the argument is not a valid internal graph database ID

        :param internal_id: Alleged internal graph database ID
        :return:            None
        """
        assert cls.valid_internal_id(internal_id), \
            f"assert_valid_internal_id(): the passed value ({internal_id}) is not a valid internal graph database ID; " \
            f"a string or non-negative integer expected"



    @classmethod
    def valid_internal_id(cls, internal_id :Union[int, str]) -> bool:
        """
        Return True if `internal_id` is a potentially valid ID for a graph database.
        Note that whether it's actually valid will depend on the specific graph database, which isn't known here.

        EXAMPLES:
            - Neo4j version 4 uses non-negative integers
            - Neo4j version 5 still uses non-negative integers, but also offers an alternative internal ID that is a string
            - Most other graph databases (such as Neptune) use strings

        :param internal_id: An alleged internal database ID
        :return:            True if internal_id is a valid internal database ID, or False otherwise
        """
        # TODO: also invoke the database-specific lower layer InterGraph
        t = type(internal_id)
        if t != int and t != str:
            return False

        if t == int:
            if internal_id < 0:
                return False

        return True



    @classmethod
    def prepare_labels(cls, labels :Union[str, List[str], Tuple[str]]) -> str:
        """
        Turn the given string, or list/tuple of strings - representing one or more database node labels - into a string
        suitable for inclusion into a Cypher query.
        Blanks ARE allowed in the names.
        EXAMPLES:
            "" or None          both give rise to    ""
            "client"            gives rise to   ":`client`"
            "my label"          gives rise to   ":`my label`"
            ["car", "vehicle"]  gives rise to   ":`car`:`vehicle`"

        :param labels:  A string, or list/tuple of strings, representing one or multiple Neo4j labels;
                            it's acceptable to be None
        :return:        A string suitable for inclusion in the node part of a Cypher query
        """
        if not labels:
            return ""   # No labels

        if type(labels) == str:
            labels = [labels]

        cypher_labels = ""
        for single_label in labels:
            cypher_labels += f":`{single_label}`"       # EXAMPLE: ":`label 1`:`label 2`"
            # Note: the back ticks allow the inclusion of blank spaces in the labels

        return cypher_labels



    @classmethod
    def prepare_where(cls, where_list: Union[str, list]) -> str:
        """
        Given a WHERE clause, or list/tuple of them, combined them all into one -
        and also prefix the WHERE keyword to the result (if appropriate).
        The *combined* clauses of the WHERE statement are parentheses-enclosed, to protect against code injection

        EXAMPLES:   "" or "      " or [] or ("  ", "") all result in  ""
                    "n.name = 'Julian'" returns "WHERE (n.name = 'Julian')"
                        Likewise for ["n.name = 'Julian'"]
                    ("p.key1 = 123", "   ",  "p.key2 = 456") returns "WHERE (p.key1 = 123 AND p.key2 = 456)"

        :param where_list:  A string with a subclause, or list or tuple of subclauses,
                            suitable for insertion in a WHERE statement

        :return:            A string with the combined WHERE statement,
                            suitable for inclusion into a Cypher query (empty if there were no subclauses)
        """
        if type(where_list) == str:
            where_list = [where_list]
        else:
            assert type(where_list) == list or type(where_list) == tuple, \
                f"prepare_where(): the argument must be a string, list or tuple; instead, it was of type {type(where_list)}"

        purged_where_list = [w for w in where_list if w.strip() != ""]      # Drop all the blank terms in the list

        if len(purged_where_list) == 0:
            return ""

        return "WHERE (" + " AND ".join(purged_where_list) + ")"    # The outer parentheses are to protect against code injection



    @classmethod
    def dict_to_cypher(cls, data_dict: {}, prefix="par_") -> (str, {}):
        """
        Turn a Python dictionary (meant for specifying node or relationship attributes)
        into a string suitable for Cypher queries,
        plus its corresponding data-binding dictionary.

        EXAMPLE :
                {'cost': 65.99, 'item description': 'the "red" button'}

                will lead to the pair:
                    (
                        '{`cost`: $par_1, `item description`: $par_2}',
                        {'par_1': 65.99, 'par_2': 'the "red" button'}
                    )

        Note that backticks are used in the Cypher string to allow blanks in the key names.
        Consecutively-named dummy variables ($par_1, $par_2, etc) are used,
        instead of names based on the keys of the data dictionary (such as $cost),
        because the keys might contain blanks.

        SAMPLE USAGE:
            (cypher_properties, data_binding) = dict_to_cypher(data_dict)

        :param data_dict:   A Python dictionary
        :param prefix:      Optional prefix string for the data-binding dummy names (parameter tokens); handy to prevent conflict;
                                by default, "par_"

        :return:            A pair consisting of a string suitable for Cypher queries,
                                and a corresponding data-binding dictionary.
                            If the passed dictionary is empty or None,
                                the pair returned is ("", {})
        """
        if data_dict is None or data_dict == {}:
            return ("", {})

        assert type(data_dict) == dict, f"The data_dict argument passed to dict_to_cypher() is not a dictionary. Value: {data_dict}"

        rel_props_list = []     # A list of strings
        data_binding = {}
        parameter_count = 1     # Sequential integers used in the data dictionary, such as "par_1", "par_2", etc.

        for prop_key, prop_value in data_dict.items():
            parameter_token =  f"{prefix}{parameter_count}"          # EXAMPLE: "par_3"

            # Extend the list of Cypher property relationships and their corresponding data dictionary
            rel_props_list.append(f"`{prop_key}`: ${parameter_token}")    # The $ refers to the data binding
            data_binding[parameter_token] = prop_value
            parameter_count += 1

        rel_props_str = ", ".join(rel_props_list)

        rel_props_str = "{" + rel_props_str + "}"

        return (rel_props_str, data_binding)
