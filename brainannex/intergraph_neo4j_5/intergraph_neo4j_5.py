from neo4j import GraphDatabase                         # The Neo4j python connectivity library "Neo4j Python Driver"
from neo4j import __version__ as neo4j_driver_version   # The version of the Neo4j driver being used
from neo4j.exceptions import ServiceUnavailable         # To catch inactivity timeout errors (new to v. 5 of Neo4j)
from neo4j.time import DateTime                         # To convert datetimes (and dates) between neo4j.time.DateTime and python
import neo4j.graph                                      # To check returned data types
import pandas as pd
import os
import sys


'''
    ----------------------------------------------------------------------------------
	MIT License

        Copyright (c) 2021-2025 Julian A. West

        This file is part of the "Brain Annex" project (https://BrainAnnex.org),
        though it's released independently.
	----------------------------------------------------------------------------------
'''


class InterGraph:
    """
    IMPORTANT : for versions 5.26 of the Neo4j database
                (the final release of major version 5)

    A thin wrapper around the Neo4j python connectivity library "Neo4j Python Driver",
    which is documented at: https://neo4j.com/docs/api/python-driver/5.26/index.html

    This is a bottom layer that is dependent on the specific graph database
    (for operations such as connection, indexes, constraints),
    and insulates the higher layers from it.

    This "CORE" library allows the execution of arbitrary Cypher (query language) commands,
    and helps manage the complex data structures that they return.
    It may be used independently,
    or as the foundation of the higher-level child class, "GraphAccess"

    SECTIONS IN THIS CLASS:
        * INIT (constructor) and DATABASE CONNECTION
        * RUNNING GENERIC CYPHER QUERIES
    """

    def __init__(self,
                 host=os.getenv("NEO4J_HOST"),
                 credentials=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD")),
                 apoc=False,
                 debug=False,
                 autoconnect=True):
        """
        If unable to create a Neo4j driver object, raise an Exception
        reminding the user to check whether the Neo4j database is running

        :param host:        URL to connect to database with.
                                EXAMPLES: bolt://123.456.0.29:7687  ,  bolt://your_domain.com:7687  ,  neo4j://localhost:7687
                                DEFAULT: read from NEO4J_HOST environmental variable
        :param credentials: Pair of strings (tuple or list) containing, respectively, the database username and password
                                DEFAULT: read from NEO4J_USER and NEO4J_PASSWORD environmental variables
        :param apoc:        Flag indicating whether apoc library is used on Neo4j database to connect to
                                Notes: APOC, if used, must also be enabled on the database.
                                The only method currently requiring APOC is export_dbase_json()
        :param debug:       Flag indicating whether a debug mode is to be used :
                                if True, all the Cypher queries, and some additional info, will get printed
        :param autoconnect  Flag indicating whether the class should establish connection to database at initialization
        """

        self.debug = debug                  # If True, all the Cypher queries, and some additional info,
                                            # will get printed

        self.block_query_execution = False  # If True, all the Cypher queries will get printed (just like done by debug),
                                            # but no database operations will actually be performed.
                                            # Caution: many functions will fail validations on the results
                                            #          of the query that wasn't executed.  This option should probably
                                            #          be combined with an Exception catch

        self.host = host            # It must start with "bolt" or "neo4j"

        self.credentials = credentials

        self.apoc = apoc

        self.driver = None

        assert host, "Cannot instantiate the GraphAccess object with an undefined argument`host`; " \
                     "unable to obtain a default value from getenv('NEO4J_HOST') . You need to pass a value, " \
                     "or to set that environment variable"

        assert credentials, "Cannot instantiate the GraphAccess object with an undefined argument `credentials`; " \
                            "unable to obtain a default value from getenv('NEO4J_USER') and getenv('NEO4J_PASSWORD') . You need to pass a value, " \
                            "or to set those environment variables"

        assert ("bolt" in host) or ("neo4j" in host), \
                        "`host` argument must start with `bolt` or `neo4j`"
                        # TODO: check that substrings actual occur at start, after trimming blanks.
                        # TODO: maybe accept a host name without port number, and default port to 7687


        if self.debug:
            print ("~~~~~~~~~ Initializing Intergraph object ~~~~~~~~~")

        if autoconnect:
            # Attempt to establish a connection to the Neo4j database, and to create a driver object
            self.connect()



    def connect(self) -> None:
        """
        Attempt to establish a connection to the Neo4j database, using the credentials stored in the object.
        In the process, create and save a driver object.
        """
        assert self.host, "Host name must be specified in order to connect to the Neo4j database"
        assert self.credentials, "Neo4j database credentials (username and password) must be specified in order to connect to it"

        try:
            user, password = self.credentials  # This unpacking will work whether the credentials were passed as a tuple or list
            if self.debug:
                print(f"Attempting to connect to Neo4j host '{self.host}', with username '{user}'...")

            self.driver = GraphDatabase.driver(self.host,
                                               auth=(user, password))   # Object to connect to Neo4j's Bolt driver for Python
            # https://neo4j.com/docs/api/python-driver/4.3/api.html#driver
        except Exception as ex:
            error_msg = f"CHECK WHETHER NEO4J IS RUNNING! While instantiating the Intergraph object, it failed to create the driver: {ex}"
            # In case of sluggish server connection, a ConnectionResetError seems to be generated;
            # TODO: maybe try to detect that, and give a more informative message
            raise Exception(error_msg)


        # If we get thus far, the connection to the host was successfully established,
        # BUT this doesn't prove that we can actually connect to the database;
        # for example, with bad credentials, the connection to the host can still be established
        # TODO: specifically also look the Exception ServiceUnavailable
        try:
            self.test_dbase_connection()
        except Exception as ex:
            (exc_type, _, _) = sys.exc_info()   # This is for the purpose of giving more informative error messages;
                                                # for example, a bad database passwd will show "<class 'neo4j.exceptions.AuthError'>"
            error_msg = f"Unable to access the Neo4j database; " \
                        f"CHECK THE DATABASE USERNAME/PASSWORD in the credentials your provided: {str(exc_type)} - {ex}"
            raise Exception(error_msg)


        if self.debug:
            print(f"Connection to host '{self.host}' established.  *** IN DEBUG MODE ***")
        else:
            print("Connection to Neo4j database established.")

        if self.block_query_execution:
            print(f"    *** In BLOCK QUERY EXECUTION mode : NO DATABASE OPERATIONS WILL BE PERFORMED ***")



    def test_dbase_connection(self) -> None:
        """
        Attempt to perform a trivial Neo4j query, for the purpose of validating
        whether a connection to the database is possible.
        A failure at start time is typically indicative of invalid credentials

        :return:    None
        """
        q = "MATCH (n) RETURN n LIMIT 1"
        self.query(q)



    def version(self) -> str:
        """
        Return the version of the Neo4j driver being used.  EXAMPLE: "4.4.12"

        :return:    A string with the version number
        """
        return neo4j_driver_version



    def close(self) -> None:
        """
        Terminate the database connection.
        Note: this method is automatically invoked
              after the last operation included in "with" statements

        :return:    None
        """
        if self.driver is not None:
            self.driver.close()



    def empty_dbase(self, keep_labels=None, drop_indexes=False, drop_constraints=False) -> None:
        """
        Use this to get rid of everything in the database,
        including all the indexes and constraints (unless otherwise specified.)
        Optionally, keep nodes with a given label, or keep the indexes, or keep the constraints

        :param keep_labels:     An optional list of strings, indicating specific labels to KEEP
        :param drop_indexes:    Flag indicating whether to also ditch all indexes (by default, True)
        :param drop_constraints:Flag indicating whether to also ditch all constraints (by default, True)

        :return:                None
        """
        self.delete_nodes_by_label(keep_labels=keep_labels)

        if drop_indexes:
            self.drop_all_indexes(including_constraints=drop_constraints)






    #####################################################################################################

    '''                          ~   RUN GENERIC CYPHER QUERIES   ~                                   '''

    def ________RUN__GENERIC_QUERIES________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################

    def run_cypher_query(self, q :str, data_binding :dict, session):
        """
        Single entry point for ALL Cypher query executions

        :param q:               A string with a Cypher query
        :param data_binding:    An optional Cypher dictionary
        :param session:
        :return:
        """
        try:
            result = session.run(q, data_binding)
        except ServiceUnavailable as ex:
            print("*** NOTICE - ServiceUnavailable condition: attempting to reconnect to the database...")
            self.connect()
            #  Details: {ex}
            raise Exception(f"ServiceUnavailable signal received, probably from a timeout.\n"
                            f"Automatically re-connected.  Please RE-RUN your last command")

        return result



    def query(self, q :str, data_binding=None, single_row=False, single_cell="", single_column=""):
        """
        Run a Cypher query.  Best suited for Cypher queries that return individual values
        (such as node properties or computed values),
        but may also be used with queries that return entire nodes or relationships or paths - or nothing.

        Execute the query and fetch the returned values as a list of dictionaries.
        In cases of no results, return an empty list.
        A new session to the database driver is started, and then immediately terminated after running the query.

        ALTERNATIVES:
            * if the Cypher query returns nodes, and one wants to extract the internal database ID or node labels
              (in addition to all the properties and their values) then use query_extended() instead.

            * in case of queries that alter the database (and may or may not return values),
              use update_query() instead, in order to retrieve information about the effects of the operation

        :param q:               A string with a Cypher query
        :param data_binding:    An optional Cypher dictionary
                                EXAMPLE, assuming that the cypher string contains the substrings "$node_id":
                                        {'node_id': 20}

        :param single_row:      [OPTIONAL] If True, return a dictionary containing just the first (0-th) result row, if present,
                                    or None in case of no results.
                                    Note that if the query returns multiple records, then the picked one
                                    will be arbitrary, unless an ORDER BY is included in the query
                                    EXAMPLES of returned values:
                                        {"brand": "Toyota", "color": "White"}
                                        {'n': {}}

        :param single_cell:     [OPTIONAL] Meant for situations where only 1 node (record) is expected,
                                    and one wants only 1 specific field of that record.
                                    If a string is provided, return the value of the field by that name
                                    in the first (0-th) retrieved record.
                                    In case of no nodes found, or a node that lacks a key with this name, None will be returned.
                                    Note that if the query returns multiple records, the picked one
                                    will be arbitrary, unless an ORDER BY is included in the query

        :param single_column:   [OPTIONAL] Name of the column of interest.
                                    If provided, assemble a list (possibly empty)
                                    from all the values of that particular column all records.
                                    Note: can also be used to extract data from a particular node, for queries that return whole nodes

        :return:        If any of single_row, single_cell or single_column are True, see info under their entries.
                        If those arguments are all False, it returns a (possibly empty) list of dictionaries.
                        The structure of each dictionary in the list will depend on the nature of the Cypher query.
                        EXAMPLES:
                            Cypher returns nodes (after finding or creating them): RETURN n1, n2
                                    -> list item such as {'n1': {'gender': 'M', 'patient_id': 123}
                                                          'n2': {'gender': 'F', 'patient_id': 444}}
                            Cypher returns attribute values that get renamed: RETURN n.gender AS client_gender, n.pid AS client_id
                                    -> list items such as {'client_gender': 'M', 'client_id': 123}
                            Cypher returns attribute values without renaming them: RETURN n.gender, n.pid
                                    -> list items such as {'n.gender': 'M', 'n.pid': 123}
                            Cypher returns a single computed value
                                    -> a single list item such as {"count(n)": 100}
                            Cypher returns RELATIONSHIPS (LINKS), with or without properties: MERGE (c)-[r :PAID_BY]->(p)
                                    -> a single list item such as [{ 'r': ({}, 'PAID_BY', {}) }]   NOTE: link properties are NOT returned
                            Cypher returns a path:   MATCH p= .......   RETURN p
                                    -> list item such as {'p': [ {'name': 'Eve'}, 'LOVES', {'name': 'Adam'} ] }
                            Cypher creates nodes (without returning them)
                                    -> empty list
        """
        if self.debug or self.block_query_execution:
            self.debug_query_print(q, data_binding, method="query")
            print(f"    single_row: {single_row} , single_cell: `{single_cell}` , single_column : `{single_column}`")
            if self.block_query_execution:
                return

        # Start a new session, use it, and then immediately close it
        with self.driver.session() as new_session:
            #result = new_session.run(q, data_binding)
            result = self.run_cypher_query(q=q, data_binding=data_binding, session=new_session)


            # Note: A neo4j.Result object (printing it, shows an object of type "neo4j.work.result.Result")
            #       See https://neo4j.com/docs/api/python-driver/current/api.html#neo4j.Result
            if result is None:
                return []

            data_as_list = result.data()    # Return the result as a list of dictionaries.
                                            #       This must be done inside the "with" block,
                                            #       while the session is still open
            #print(f"data_as_list: {data_as_list}")

        # Deal with empty result lists
        if len(data_as_list) == 0:  # If no results were produced
            if single_row:
                return None
            if single_cell:
                return None
            return []

        if single_row:
            return data_as_list[0]
        if single_cell:
            return data_as_list[0].get(single_cell)


        if not single_column:
            return data_as_list
        else:    # Useful in cases where one wants to return ALL the fields of a particular node returned by the query
            data = []
            for node in data_as_list:
                data.append(node[single_column])

            return data



    def query_extended(self, q: str, data_binding = None, flatten = False, fields_to_exclude = None) -> [dict]:
        """
        Extended version of query(), meant to extract additional info
        for queries that return so-called Graph Data Types,
        i.e. nodes, relationships or paths,
        such as:    "MATCH (n) RETURN n"
                    "MATCH (n1)-[r]->(n2) RETURN r"

        For example, useful in scenarios where nodes were returned,
        and their internal database IDs (using the key "internal_id")
        and/or node labels (using the key "node_labels") are desired -
        in addition to all the properties and their values.

        Unless the flatten flag is True, individual records are kept as separate lists.
            For example, "MATCH (b:boat), (c:car) RETURN b, c"
            will return a structure such as [ [b1, c1] , [b2, c2] ]  if flatten is False,
            vs.  [b1, c1, b2, c2]  if  flatten is True.  (Note: each b1, c1, etc, is a dictionary.)

        TODO:  Scenario to test:
            if b1 == b2, would that still be [b1, c1, b1(b2), c2] or [b1, c1, c2] - i.e. would we remove the duplicates?
            Try running with flatten=True "MATCH (b:boat), (c:car) RETURN b, c" on data like "CREATE (b:boat), (c1:car1), (c2:car2)"

        :param q:                   A Cypher query : typically, one returning nodes, relationships or paths
        :param data_binding:        An optional Cypher dictionary
                                    EXAMPLE, assuming that the cypher string contains the substring "$age":
                                            {'age': 20}
        :param flatten:             Flag indicating whether the Graph Data Types need to remain clustered by record,
                                        or all placed in a single flattened list
        :param fields_to_exclude:   [OPTIONAL] list of strings with name of fields
                                        (in the database, or special keys added by this function)
                                        that wishes to drop.  No harm in listing fields that aren't present.
                                        For example, if the query returns relationships, there will be 3 keys
                                        named 'neo4j_start_node', 'neo4j_end_node', 'neo4j_type' ('type' is the name of the relationship)

        :return:        A (possibly empty) list of dictionaries, if flatten is True,
                        or a list of list, if flatten is False.
                        Each item in the lists is a dictionary, with details that will depend on which Graph Data Types
                                were returned in the Cypher query.

                        EXAMPLE with flatten=True for a query returning nodes "MATCH n RETURN n":
                                [   {'year': 2023, 'make': 'Ford', 'internal_id': 123, 'node_labels': ['Motor Vehicle']},
                                    {'year': 2013, 'make': 'Toyota', 'internal_id': 4, 'node_labels': ['Motor Vehicle']}
                                ]
                        EXAMPLE with flatten=False for that same query returning nodes "MATCH n RETURN n":
                                [   [{'year': 2023, 'make': 'Ford', 'internal_id': 123, 'node_labels': ['Motor Vehicle']}],
                                    [{'year': 2013, 'make': 'Toyota', 'internal_id': 4, 'node_labels': ['Motor Vehicle']}]
                                ]

                        EXAMPLE of *individual items* - for a returned NODE
                            {'gender': 'M', 'age': 20, 'internal_id': 123, 'node_labels': ['patient']}

                        EXAMPLE of *individual items* - for a returned RELATIONSHIP (note that 'neo4j_type' is the link name,
                            and that any properties of the relationships, such as 'price', appear as key/values in the dict)
                            {'price': 7500, 'internal_id': 2,
                             'neo4j_start_node': <Node id=11 labels=frozenset() properties={}>,
                             'neo4j_end_node': <Node id=14 labels=frozenset() properties={}>,
                             'neo4j_type': 'bought_by'}]
        """
        #TODO: rename neo4j_start_node to start_node, etc
        #TODO: perhaps merge with query()

        if self.debug or self.block_query_execution:
            self.debug_query_print(q, data_binding, method="query_extended")
            print(f"    flatten: {flatten} , fields_to_exclude: {fields_to_exclude}")
            if self.block_query_execution:
                return []

        # Start a new session, use it, and then immediately close it
        with self.driver.session() as new_session:
            #result = new_session.run(q, data_binding)
            result = self.run_cypher_query(q=q, data_binding=data_binding, session=new_session)

            # Note: A neo4j.Result iterable object (printing it, shows an object of type "neo4j.work.result.Result")
            #       See https://neo4j.com/docs/api/python-driver/current/api.html#neo4j.Result
            if result is None:
                return []

            data_as_list = []

            # The following must be done inside the "with" block, while the session is still open
            for record in result:
                # Note: record is a neo4j.Record object - an immutable ordered collection of key-value pairs.
                #       (the keys are the dummy names used for the nodes, such as "n")
                #       See https://neo4j.com/docs/api/python-driver/current/api.html#record

                # EXAMPLE of record (if node n was returned):
                #       <Record n=<Node id=227 labels=frozenset({'person', 'client'}) properties={'gender': 'M', 'age': 99}>>
                #       (it has one key, "n")
                # EXAMPLE of record (if node n and node c were returned):
                #       <Record n=<Node id=227 labels=frozenset({'person', 'client'}) properties={'gender': 'M', 'age': 99}>
                #               c=<Node id=66 labels=frozenset({'car'}) properties={'color': 'blue'}>>
                #       (it has 2 keys, "n" and "c")

                data = []
                for item in record:
                    # Note: item is a neo4j.graph.Node object
                    #       OR a neo4j.graph.Relationship object
                    #       OR a neo4j.graph.Path object
                    #       See https://neo4j.com/docs/api/python-driver/current/api.html#node
                    #           https://neo4j.com/docs/api/python-driver/current/api.html#relationship
                    #           https://neo4j.com/docs/api/python-driver/current/api.html#path
                    # EXAMPLES of item:
                    #       <Node id=95 labels=frozenset({'car'}) properties={'color': 'white', 'make': 'Toyota'}>
                    #       <Relationship id=12 nodes=(<Node id=147 labels=frozenset() properties={}>, <Node id=150 labels=frozenset() properties={}>) type='bought_by' properties={'price': 7500}>

                    neo4j_properties = dict(item.items())   # EXAMPLE: {'gender': 'M', 'age': 99}

                    if isinstance(item, neo4j.graph.Node):
                        neo4j_properties["internal_id"] = item.id               # Example: 227
                        neo4j_properties["node_labels"] = list(item.labels)     # Example: ['person', 'client']

                    elif isinstance(item, neo4j.graph.Relationship):
                        neo4j_properties["internal_id"] = item.id               # Example: 227
                        neo4j_properties["neo4j_start_node"] = item.start_node  # A neo4j.graph.Node object with "id", "labels" and "properties"
                        neo4j_properties["neo4j_end_node"] = item.end_node      # A neo4j.graph.Node object with "id", "labels" and "properties"
                        #   Example: <Node id=118 labels=frozenset({'car'}) properties={'color': 'white'}>
                        neo4j_properties["neo4j_type"] = item.type              # The name of the relationship

                    elif isinstance(item, neo4j.graph.Path):
                        neo4j_properties["neo4j_nodes"] = item.nodes            # The sequence of Node objects in this path

                    # Exclude any unwanted (ordinary or special) field
                    if fields_to_exclude:
                        for field in fields_to_exclude:
                            if field in neo4j_properties:
                                del neo4j_properties[field]

                    if flatten:
                        data_as_list.append(neo4j_properties)
                    else:
                        data.append(neo4j_properties)

                if not flatten:
                    data_as_list.append(data)

            return data_as_list



    def update_query(self, q: str, data_binding=None) -> dict:
        """
        Run a Cypher query and return statistics about its actions (such number of nodes created, etc.)
        Typical use is for queries that update the database.
        If the query returns any values, they are made available as  list, as the value of the key 'returned_data'.

        Note: if the query creates nodes and one wishes to obtain their internal database ID's,
              one can include Cypher code such as "RETURN id(n) AS internal_id" (where n is the dummy name of the newly-created node)

        EXAMPLE:  result = update_query("CREATE(n :CITY {name: 'San Francisco'}) RETURN id(n) AS internal_id")

                  result will be {'nodes_created': 1, 'properties_set': 1, 'labels_added': 1,
                                  'returned_data': [{'internal_id': 123}]
                                 } , assuming 123 is the internal database ID of the newly-created node

        :param q:           Any Cypher query, but typically one that doesn't return anything
        :param data_binding: Data-binding dictionary for the Cypher query

        :return:            A dictionary of statistics (counters) about the query just run
                            EXAMPLES -
                                {}      The query had no effect
                                {'nodes_deleted': 3}    The query resulted in the deletion of 3 nodes
                                {'properties_set': 2}   The query had the effect of setting 2 properties
                                {'relationships_created': 1}    One new relationship got created
                                {'returned_data': [{'internal_id': 123}]}  'returned_data' contains the results of the query,
                                                                        if it returns anything, as a list of dictionaries
                                                                        - akin to the value returned by query()
                                {'returned_data': []}  Gets returned by SET QUERIES with no return statement
                            OTHER KEYS include:
                                nodes_created, nodes_deleted, relationships_created, relationships_deleted,
                                properties_set, labels_added, labels_removed,
                                indexes_added, indexes_removed, constraints_added, constraints_removed
                                More info:  https://neo4j.com/docs/api/python-driver/current/api.html#neo4j.SummaryCounters
        """
        if self.debug or self.block_query_execution:
            self.debug_query_print(q, data_binding, method="update_query")
            if self.block_query_execution:
                 return {}

        # Start a new session, use it, and then immediately close it
        with self.driver.session() as new_session:
            #result = new_session.run(q, data_binding)
            result = self.run_cypher_query(q=q, data_binding=data_binding, session=new_session)

            # Note: result is a neo4j.Result iterable object
            #       See https://neo4j.com/docs/api/python-driver/4.4/api.html#neo4j.Result

            data_as_list = result.data()    # Fetch any data returned by the query, as a (possibly-empty) list of dictionaries

            info = result.consume()     # Get the stats of the query just executed
            # This is a neo4j.ResultSummary object
            # See https://neo4j.com/docs/api/python-driver/current/api.html#neo4j.ResultSummary

            if self.debug:
                print("    In update_query(). Attributes of ResultSummary object:")
                # Show as dictionary, which is available in info.__dict__
                for k, v in info.__dict__.items():
                    print(f"    {k} -> {v}")
                '''
                EXAMPLE of info.__dict__: 
                {   'metadata': { 
                                    'query': 'MATCH (n :`A` {`name`: $par_1}) DETACH DELETE n', 
                                    'parameters': {'par_1': 'Jill'}, 
                                    'server': <neo4j.api.ServerInfo object at 0x0000013AFFAF36A0>, 
                                    't_first': 0, 'fields': [], 'bookmark': 'FB:kcwQ7BUXt6dES3GUrMEnTGTC5ck+BZA=', 
                                    'stats': {'nodes-deleted': 1}, 'type': 'w', 't_last': 0, 'db': 'neo4j'
                                }, 
                    'server': <neo4j.api.ServerInfo object at 0x0000013AFFAF36A0>, 
                    'database': 'neo4j', 
                    'query': 'MATCH (n :`A` {`name`: $par_1}) DETACH DELETE n', 
                    'parameters': {'par_1': 'Jill'}, 
                    'query_type': 'w', 
                    'plan': None, 'profile': None, 
                    'notifications': None, 
                    'counters': {'nodes_deleted': 1}, 
                    'result_available_after': 0, 
                    'result_consumed_after': 0
                }
                '''

            stats = info.counters   # A neo4j.SummaryCounters object
            # See https://neo4j.com/docs/api/python-driver/current/api.html#neo4j.SummaryCounters
            stats_dict = stats.__dict__   # Convert object to dictionary

            stats_dict['returned_data'] = data_as_list  # Add an extra entry to the dictionary, with the data returned by the query

            return stats_dict






    #####################################################################################################

    '''                                      ~   LABELS   ~                                           '''

    def ________LABELS________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################


    def get_labels(self) -> [str]:
        """
        Extract and return a list of ALL the Neo4j labels present in the database.
        No particular order should be expected.
        Note: to get the labels of a particular node, use get_node_labels()

        :return:    A list of strings
        """
        results = self.query("MATCH (n) UNWIND labels(n) As label RETURN DISTINCT label")
        return [x['label'] for x in results]



    def delete_nodes_by_label(self, delete_labels=None, keep_labels=None) -> None:
        """
        Empty out (by default completely) the Neo4j database.
        Optionally, only delete nodes with the specified labels, or only keep nodes with the given labels.
        Note: the keep_labels list has higher priority; if a label occurs in both lists, it will be kept.
        IMPORTANT: it does NOT clear indexes; "ghost" labels may remain!
        TODO: return the number of nodes deleted

        :param delete_labels:   An optional string, or list of strings, indicating specific labels to DELETE
        :param keep_labels:     An optional string or list of strings, indicating specific labels to KEEP
                                    (keep_labels has higher priority over delete_labels)
        :return:                None
        """
        if (delete_labels is None) and (keep_labels is None):
            # Delete ALL nodes AND ALL relationship from the database; for efficiency, do it all at once

            q = "MATCH (n) DETACH DELETE(n)"
            self.query(q)       # TODO: switch to update_query() and return the number of nodes deleted
            return

        if not delete_labels:
            delete_labels = self.get_labels()   # If no specific labels to delete were given,
            # then consider all labels for possible deletion (unless marked as "keep", below)
        else:
            if type(delete_labels) == str:
                delete_labels = [delete_labels] # If a string was passed, turn it into a list

        if not keep_labels:
            keep_labels = []    # Initialize list of labels to keep, if not provided
        else:
            if type(keep_labels) == str:
                keep_labels = [keep_labels] # If a string was passed, turn it into a list

        # Delete all nodes with labels in the delete_labels list,
        #   EXCEPT for any label in the keep_labels list
        for label in delete_labels:
            if not (label in keep_labels):
                q = f"MATCH (x:`{label}`) DETACH DELETE x"
                self.query(q)       # TODO: switch to update_query() and return the number of nodes deleted



    def bulk_delete_by_label(self, label: str):
        """
        IMPORTANT: APOC required (starting from v 4.4 of Neo4j, will be able to do this without APOC; TODO: not yet tested)

        Meant for large databases, where the straightforward deletion operations may result
        in very large number of nodes, and take a long time (or possibly fail)

        "If you need to delete some large number of objects from the graph,
        one needs to be mindful of the not building up such a large single transaction
        such that a Java OUT OF HEAP Error will be encountered."
        See:  https://neo4j.com/developer/kb/large-delete-transaction-best-practices-in-neo4j/

        TODO: generalize to bulk-deletion not just by label
        TODO: test.  CAUTION: only tested interactively

        :param label:   A string with the label of the nodes to delete (blank spaces in name are ok)
        :return:        A dict with the keys "batches" and "total"
        """
        batch_size = 10000
        q = f'''
            CALL apoc.periodic.iterate("MATCH (n :`{label}`) RETURN id(n) as id", 
                                       "MATCH (n) WHERE id(n) = id DETACH DELETE n", {{batchSize:{batch_size}}})
            YIELD batches, total 
            RETURN batches, total
        '''
        result = self.query(q)
        return result[0]



    def get_label_properties(self, label:str) -> list:
        """
        Extract and return all the property (key) names used in nodes with the given label,
        sorted alphabetically

        :param label:   A string with the name of a node label
        :return:        A list of property names, sorted alphabetically
        """
        q = """
            CALL db.schema.nodeTypeProperties() 
            YIELD nodeLabels, propertyName
            WHERE $label in nodeLabels and propertyName IS NOT NULL
            RETURN DISTINCT propertyName 
            ORDER BY propertyName
            """
        data_binding = {'label': label}

        return [res['propertyName'] for res in self.query(q, data_binding)]





    #####################################################################################################

    '''                                      ~   INDEXES   ~                                          '''

    def ________INDEXES________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################


    def get_indexes(self) -> pd.DataFrame:
        """
        Return all the database indexes, and some of their attributes,
        as a Pandas dataframe.

        Standard (always present) column names: "name", "labelsOrTypes", "properties".
        Other columns will depend on the (version of the) underlying graph database.

        EXAMPLE of a returned dataframe:
                               name  labelsOrTypes        properties      entityType     type
             0      "index_23b59623"  ["my_label"]   ["my_property"]            NODE    RANGE
             1         "L.client_id"         ["L"]     ["client_id"]    RELATIONSHIP    RANGE

        :return:        A (possibly-empty) Pandas dataframe
        """

        q = """
            SHOW INDEXES 
            YIELD name, labelsOrTypes, properties, entityType, type
            return *
            """

        results = self.query(q)
        if len(results) > 0:
            return pd.DataFrame(list(results))
        else:    # No index found
            return pd.DataFrame([], columns=['name'])



    def create_index(self, label :str, key :str) -> bool:
        """
        Create a new database index, unless it already exists,
        to be applied to the pairing of the specified label and key (property).
        The standard name automatically given to the new index is of the form label.key
        EXAMPLE - to index nodes labeled "car" by their key "color", use:
                        create_index(label="car", key="color")
                  This new index - if not already in existence - will be named "car.color"

        If an existing index entry contains a list of labels (or types) such as ["l1", "l2"] ,
        and a list of properties such as ["p1", "p2"] ,
        then the given pair (label, key) is checked against ("l1_l2", "p1_p2"), to decide whether it already exists.

        :param label:   A string with the node label to which the index is to be applied
        :param key:     A string with the key (property) name to which the index is to be applied
        :return:        True if a new index was created, or False otherwise
        """
        # TODO: clarify naming, and offer option to specify a custom name.  Allow use of multiple keys
        existing_indexes = self.get_indexes()   # A Pandas dataframe with info about indexes;
                                                #       in particular 2 columns named "labelsOrTypes" and "properties"

        # Ditch Pandas dataframe rows where either column "labelsOrTypes" or "properties" is missing
        # (this would be the case for indexes of type "LOOKUP", which won't have "labelsOrTypes" nor "properties")
        existing_indexes = existing_indexes.dropna(subset=["labelsOrTypes", "properties"])

        # Proceed by row (axis=1) along the Pandas dataframe `existing_indexes`, and assemble a list of pairs.
        # The 1st element in the pairs consists of underscore-separated `labelsOrTypes` entries;
        # the 2nd element in the pairs consists of underscore-separated `properties` entries
        existing_standard_name_pairs = list(existing_indexes.apply(
            lambda x: ("_".join(x['labelsOrTypes']), "_".join(x['properties'])), axis=1))
        """
        For example, if the Pandas dataframe `existing_indexes` contains the following columns: 
                            labelsOrTypes     properties
                0                   [car]  [color, make]
                1                [person]          [sex]
                
        then `existing_standard_name_pairs` will be:  [('car', 'color_make'), ('person', 'sex')]
        """


        # Index is created if not already exists;
        # a standard name for the index is assigned: `{label}.{key}`
        if (label, key) not in existing_standard_name_pairs:
            q = f'CREATE INDEX `{label}.{key}` FOR (s:`{label}`) ON (s.`{key}`)'
            self.query(q)
            return True
        else:
            return False



    def drop_index(self, name :str) -> bool:
        """
        Get rid of the index with the given name

        :param name:    Name of the index to jettison
        :return:        True if successful
                            or False otherwise (for example, if the index doesn't exist)
        """
        try:
            self.query(f"DROP INDEX `{name}`")      # Note: this generates an Exception if the index doesn't exist
            return True
        except Exception:
            return False



    def drop_all_indexes(self, including_constraints=True) -> None:
        """
        Eliminate all the indexes in the database and, optionally, also get rid of all constraints

        :param including_constraints:   Flag indicating whether to also ditch all the constraints
        :return:                        None
        """
        if including_constraints:
            #if self.apoc:
                #self.query("call apoc.schema.assert({},{})")
                #return      # DEPRECATED: it may not delete all indexes!
            #else:
            self.drop_all_constraints()


        indexes = self.get_indexes()
        for name in indexes['name']:
            self.drop_index(name)





    #####################################################################################################

    '''                                     ~   CONSTRAINTS   ~                                        '''

    def ________CONSTRAINTS________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################


    def get_constraints(self) -> pd.DataFrame:
        """
        Return all the database constraints, and some of their attributes,
        as a Pandas dataframe with 3 columns:
            COLUMN          EXAMPLES
            name            "my_constraint"
            type            "UNIQUENESS"
            labelsOrTypes   ["patient"]
            properties      ["patient_id"]
            entityType      "NODE"
            ownedIndexId    3    or  "my_constraint"

        :return:  A (possibly-empty) Pandas dataframe with 3 columns: 'name', 'description', 'details'
        """
        q = """
           SHOW CONSTRAINTS
           yield name, type, labelsOrTypes, properties, entityType, ownedIndex
           return *
           """
        results = self.query(q)
        if len(results) > 0:
            return pd.DataFrame(list(results))
        else:
            return pd.DataFrame([], columns=['name', 'type', 'labelsOrTypes', 'properties', 'entityType', 'ownedIndex'])



    def create_constraint(self, label :str, key :str, name=None) -> bool:
        """
        Create a uniqueness constraint for a node property in the graph,
        optionally with the specified name (by default `{label}.{key}.UNIQUE`),
        and also create an index for the specified label and property

        The constraint creation will not take place, and False will be returned,
        if a constraint by the same name already exists,
        or if an index for the specified label and property already exists.

        EXAMPLE: create_constraint(label="patient", key="patient_id")

        :param label:   A string with the node label to which the constraint is to be applied
        :param key:     A string with the key (property) name to which the constraint is to be applied
        :param name:    Optional name to give to the new constraint; if not provided, a
                            standard name of the form `{label}.{key}.UNIQUE` is used.
                            EXAMPLE: "patient.patient_id.UNIQUE"
        :return:        True if a new constraint was created, or False otherwise
        """
        #TODO: offer the option to pass multiple keys

        # A standard name for a constraint is assigned: `{label}.{key}.UNIQUE` if name was not provided
        cname = (name if name else f"{label}.{key}.UNIQUE")

        # Constraint is created if not already exists
        # TODO: this part could probably be ditched, if the "IF NOT EXISTS" is taken out of the query below
        existing_constraints = self.get_constraints()
        if cname in list(existing_constraints['name']):
            #print("--- ALREADY EXISTS")
            return False


        try:
            q = f'''
                CREATE CONSTRAINT `{cname}` IF NOT EXISTS FOR (n:`{label}`) REQUIRE n.`{key}` IS UNIQUE
                '''
            self.query(q)
            # Note: creation of a constraint will crash if another constraint, or index, already exists
            #           for the specified label and key
            return True
        except Exception:
            #print("Exception triggered")
            return False



    def drop_constraint(self, name: str) -> bool:
        """
        Eliminate the constraint with the specified name.
        Its associated index is also deleted.

        :param name:    Name of the constraint to eliminate
        :return:        True if successful or False otherwise (for example, if the constraint doesn't exist)
        """
        try:
            q = f"DROP CONSTRAINT `{name}`"
            self.query(q)     # Note: it crashes if the constraint doesn't exist
            return True
        except Exception:
            return False



    def drop_all_constraints(self) -> None:
        """
        Eliminate all the constraints in the database

        :return:    None
        """
        constraints = self.get_constraints()
        for name in constraints['name']:
            self.drop_constraint(name)





    #####################################################################################################

    '''                                     ~   DATA TYPES   ~                                        '''

    def ________DATA_TYPES________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################


    def property_data_type_cypher(self) -> str:
        """
        Return the Cypher fragment to be used as the name of the function
        to use to extract the data type from a node property.

        EXAMPLE:    cyp = property_data_type_cypher()
                    q = f"MATCH (n) WHERE id(n) = 123 RETURN {cyp}(n.`my_field`) AS dtype"
                    Then run the above query q

        :return:    A string with a Cypher fragment
        """
        return "apoc.meta.cypher.type"





    #####################################################################################################

    '''                                   ~   DEBUGGING SUPPORT   ~                                   '''

    def ________DEBUGGING_SUPPORT________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################


    def debug_print_query(self, q :str, data_binding=None, method=None) -> None:
        """
        Print out the given Cypher query
        (and, optionally, its data binding and/or the name of the calling method)

        :param q:               String with Cypher query
        :param data_binding:    OPTIONAL dictionary
        :param method:          OPTIONAL string with the name of the calling method
                                    EXAMPLE:  "foo"
        :return:                None
        """
        if method:
            print(f"\nIn {method}().  Query:")
        else:
            print(f"Query:")

        print(f"    {q}")

        if data_binding:
            print("Data binding:")
            print(f"    {data_binding}")

        print()



    def debug_query_print(self, q :str, data_binding=None, method=None) -> None:
        """
        Synonym for debug_print_query()

        Print out the given Cypher query
        (and, optionally, its data binding and/or the name of the calling method)

        :param q:               String with Cypher query
        :param data_binding:    OPTIONAL dictionary
        :param method:          OPTIONAL string with the name of the calling method
                                    EXAMPLE:  "foo"
        :return:                None
        """
        self.debug_print_query(q=q, data_binding=data_binding, method=method)
