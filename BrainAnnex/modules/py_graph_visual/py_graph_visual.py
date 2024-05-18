from typing import Union


class PyGraphVisual:
    """
    Facilitate data preparation for graph visualization using the Cytoscape.js library
    """


    def __init__(self, db=None):
        self.db = db                    # Object of "NeoAccess" class

        self.structure = []             # The data that defines a graph to visualize.
                                        #    A list of dicts defining nodes, and possibly edges as well.
                                        #   NODES must contain the keys 'id' and 'labels'
                                        #   EDGES must contain the keys 'name', 'source', and 'target'
                                        #       (and presumably 'id' is required as well?)
                                        # EXAMPLE (2 nodes and an edge):
                                        #   [{'id': 1, 'labels': ['PERSON'], 'name': 'Julian'},
                                        #    {'id': 2, 'labels': ['CAR'], 'color': 'white'},
                                        #    {'name': 'OWNS', 'source': 1, 'target': 2, 'id': 'edge-1'}]

        self.color_mapping = {}         # Mapping a node label to its interior color (the edge color is an automatic variation)
                                        # EXAMPLE:  {'PERSON': 'cyan', 'CAR': 'orange'}

        self.caption_mapping = {}       # Mapping a node label to its caption (field name to use on the graph)
                                        # EXAMPLE:  {'PERSON': 'name', 'CAR': 'color'}

        self._next_available_edge_id = 1 # An auto-increment value

        self._all_node_ids = []         # List of all the node id's added to the graph so far;
                                        #   used for optional prevention of duplicates


    def serialize(self) -> dict:
        """
        Extract and return a dict of relevent data from this object

        :return:
        """
        return {"structure": self.structure,
                "color_mapping": self.color_mapping,
                "caption_mapping": self.caption_mapping}



    def __str__(self) -> str:
        """
        Return an overview description of this object

        :return:    A string with a description of this object
        """
        s = f"Object describing a graph containing a total of {len(self.structure)} nodes and edges:\n"
        s += f"    Graph structure: {self.structure}\n"
        s += f"    Graph color mapping: {self.color_mapping}\n"
        s += f"    Graph caption mapping: {self.caption_mapping}"

        return s



    def get_graph_data(self) -> dict:
        """
        Return a data dictionary with all the relevant visualization info
        (typically, to pass to the front-end, for eventual use by the Cytoscape.js library)

        :return:    A dict with 3 keys - "structure", "color_mapping" and "caption_mapping"
        """
        return {"structure": self.structure,
                "color_mapping": self.color_mapping,
                "caption_mapping": self.caption_mapping}



    def add_node(self, node_id :Union[int,str], labels="", data=None) -> None:
        """
        Prepare and store the data for 1 node, in a format expected by the visualization front-end

        EXAMPLE:    {'id': 1, 'name': 'Julian', 'labels': ['PERSON']}

        :param node_id:         Either an integer or a string to uniquely identify this node in the graph;
                                    it will be used to specify the start/end nodes of edges.
                                    Typically, use either the internal database ID, or some URI
                                    Records with a duplicate node_id are silently disregarded
        :param labels:          A string, or list of strings, with the node's label(s) used in the graph database;
                                    if not used, pass an empty string
        :param data:            A dict with all other node data not already specified in any of the other arguments
        :return:                None
        """
        assert node_id != "", \
            "add_node(): cannot use an empty string for the argument `node_id`"


        if node_id in self._all_node_ids:
            return      # Silently disregard duplicates

        if data is None:
            data = {}

        d = data.copy()     # Make an independent clone of the data dict


        d["id"] = node_id

        if type(labels) == str:
            labels = [labels]

        d["labels"] = labels

        self.structure.append(d)
        self._all_node_ids.append(node_id)



    def add_edge(self, from_node :Union[str, int], to_node :Union[str, int],
                 name :str, edge_id=None, data=None) -> None:
        """
        Prepare and store the data for 1 edge, in a format expected by the visualization front-end.

        EXAMPLE:   {'name': 'OWNS', 'source': 1, 'target': 2, 'id': 'edge-1'}

        Note that 'id', in this context, is whatever we pass to the visualization module for the nodes;
        not necessarily related to the internal database ID's

        :param from_node:   Integer or a string uniquely identify the "id" of the node where the edge originates
        :param to_node:     Integer or a string uniquely identify the "id" of the node where the edge ends
        :param name:        Name of the relationship
        :param edge_id:     (OPTIONAL)  If not provided, strings such as "edge-123" are used,
                                        with auto-generated consecutive integers
                                TODO: unclear if edge id's are really needed
        :param data:        A dict with all other node data not already specified in any of the other arguments

        :return:            None
        """
        from_id = from_node
        to_id = to_node

        d = {"name": name, "source": from_id, "target": to_id}

        if edge_id is not None:
            d["id"] = edge_id
        else:
            d["id"] = f"edge-{self._next_available_edge_id}"
            self._next_available_edge_id += 1        # Maintain an auto-increment value

        if data:
            d.update(data)

        self.structure.append(d)



    def assign_caption(self, label :str, caption="name") -> None:
        """
        Assign and store a mapping from label name to caption (name of field to use on the display)

        EXAMPLES:   assign_caption(label='PERSON', caption='name')
                    assign_caption(label='CAR', caption='color')

        :param label:   The name of a node label
        :param caption: The name of the node field to use on the display (by default, "name")
        :return:        None
        """
        assert type(label) == str, \
            "assign_caption(): the argument `label` must be a string"

        self.caption_mapping[label] = caption



    def assign_color_mapping(self, label :str, color :str) -> None:
        """
        Assign and store a mapping from label name to color to use for nodes having that label

        :param label:   The name of a node label
        :param color:   The name (hex string or standard CSS name) of the color to use on the display
        :return:        None
        """
        extra_colors =  {       # Convenient extra colors, not available thru standard CSS names
            "graph_green": '#8DCC92',
            "graph_darkgreen": '#56947E',
            "graph_teal": '#569481',
            "graph_orange": '#F79768',
            "graph_blue": '#4C8EDB',
            "graph_red": '#F16668',
            "graph_darkbrown": '#604A0D',
            "graph_lightbrown": '#D9C8AD',
            "graph_orchid": '#C990C1',
            "graph_gold": '#FFC455'     # Has a bit more orange than 'gold'
        }

        if color in extra_colors:
            color = extra_colors[color]

        self.color_mapping[label] = color




    ##########   The method below require a database connection   ##########


    def prepare_graph(self, result_dataset :[dict], add_edges=True) -> [int]:
        """
        Given a list of dictionary data about graph-database nodes - for example,
        as returned by NeoAccess.get_nodes() - construct and save visualization data for them.

        Each dictionary entry is expected to have a key named "internal_id";
        if not present, it will be silently ignored.
        Though not required, a key named "neo4j_labels" is typically present as well.

        :param result_dataset:  A list of dictionary data about graph-database nodes
        :param add_edges:       If True, all existing edges among the displayed nodes
                                    will also be part of the visualization
        :return:                A list of integers with the internal databased IDs
                                    of all the nodes added to the graph structure
        """
        node_list = []      # Running list of internal databased IDs, for nodes included in visualization
        for node in result_dataset:
            internal_id = node.get("internal_id")
            if not internal_id:
                continue    # Silently ignore any entry lacking this data

            node_list.append(internal_id)

            if "neo4j_labels" in node:
                labels = node["neo4j_labels"]
                del node["neo4j_labels"]
            else:
                labels = ""

            self.add_node(node_id=internal_id, labels=labels,
                          data=node)


        if add_edges:
            # Search the database for any edges among any of the nodes selected for the visualization
            q = '''
                MATCH (n1)-[r]->(n2) 
                WHERE ID(n1) IN $node_list AND ID(n2) IN $node_list 
                RETURN DISTINCT id(n1) AS from_node, id(n2) AS to_node, type(r) AS name
                '''

            result = self.db.query(q, {"node_list": node_list})
            for edge in result:
                #print(edge)
                self.add_edge(from_node=edge["from_node"], to_node=edge["to_node"], name=edge["name"])

        return node_list



    def link_node_groups(self, group1 :[int], group2 :[int]) -> None:
        """
        Search the database for any edges from any of the nodes in the 1st group, to any node in the 2nd group.
        Any located edge will be added to the visualization data stored in this object

        :param group1:  List of integers with the internal databased IDs of the 1st group of nodes
        :param group2:  List of integers with the internal databased IDs of the 2nd group of nodes
        :return:        None
        """
        q = '''
            MATCH (n1)-[r]->(n2) 
            WHERE ID(n1) IN $group1 AND ID(n2) IN $group2 
            RETURN DISTINCT id(n1) AS from_node, id(n2) AS to_node, type(r) AS name
            '''

        result = self.db.query(q, {"group1": group1, "group2": group2})
        for edge in result:
            #print(edge)
            self.add_edge(from_node=edge["from_node"], to_node=edge["to_node"], name=edge["name"])
