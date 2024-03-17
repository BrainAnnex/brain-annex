from typing import Union


class PyGraphScape:     # Alternate name: PyGraphVisual
    """

    GraphicLog.export_plot(PyGraphScape_object, "vue_cytoscape_1")
    """


    def __init__(self):
        self.structure = []             # A list of dicts defining nodes, and possibly edges as well
                                        #   Nodes must contain the key 'id' (and, typically, 'labels')
                                        #   Edges must contain the keys 'source', 'target' and 'name'
                                        #   (and presumably 'id' as well?)

        self.color_mapping = {}         # Mapping a node label to its interior color
                                        # EXAMPLE: {"Chemical": "graph_green", "Reaction": "graph_lightbrown"}
        self.caption_mapping = {}
        self.next_available_edge_id = 1



    def __str__(self):
        s = f"Graph contains a total of {len(self.structure)} nodes and edges\n"
        s += f"    Graph structure: {self.structure}\n"
        s += f"    Graph color mapping: {self.color_mapping}\n"
        s += f"    Graph caption mapping: {self.caption_mapping}"
        return s


    def get_graph_data(self):
        return {"structure": self.structure,
                "color_mapping": self.color_mapping,
                "caption_mapping": self.caption_mapping}



    def add_node(self, node_id :Union[int,str], labels="", name=None, data=None) -> None:
        """
        Prepare the data for 1 node for the visualization

        :param node_id: Either an integer or a string to uniquely identify this node in the graph;
                            it will be used to specify the start/end nodes of edges.
                            Typically, use either the internal database ID, or some URI
        :param labels:  A string, or list of strings, with the node's label(s) used in the graph database;
                            if not used, pass an empty string
                            TODO: if more than 1 label is passed, only the 1st one is being used for now
        :param name:    An optional string meant to be displayed by default on the node;
                            if not specified, a decision will be made by the front end about with other data field
                            to use (for example the value of the "uri" argument)
        :param data:    A dict with all other node data not specified in any of the other arguments
        :return:        None
        """
        if type(node_id) == str:
            assert node_id != "", \
                "add_node(): cannot use an empty string for the argument `node_id`"

        if data is None:
            data = {}


        d = data.copy()     # Make an independent clone


        d["id"] = node_id

        if type(labels) == list:
            labels = labels[0]      # TODO: utilize all labels in the future
        d["labels"] = labels

        if name:
            d["name"] = name

        self.structure.append(d)



    def add_edge(self, from_node :Union[str, int], to_node :Union[str, int], name :str, edge_id=None) -> None:
        """
        Prepare the data for 1 edge for the visualization.
        Note that "id", in this context, is whatever we pass to the visualization module for the nodes;
        not necessarily related to the internal database ID's

        :param from_node:   Integer or a string uniquely identify the "id" of the node where the edge originates
        :param to_node:     Integer or a string uniquely identify the "id" of the node where the edge ends
        :param name:        Name of the relationship
        :param edge_id:     (OPTIONAL) If not provided, auto-generated consecutive integers are used
                                TODO: unclear if edge id's are really needed
        :return:            None
        """
        from_id = from_node
        to_id = to_node

        d = {"name": name, "source": from_id, "target": to_id}

        if edge_id is not None:
            d["id"] = edge_id
        else:
            d["id"] = f"edge-{self.next_available_edge_id}"
            self.next_available_edge_id += 1

        self.structure.append(d)


    def assign_caption(self, label :str, caption :str) -> None:
        self.caption_mapping[label] = caption



    def assign_color_mapping(self, label :str, color :str) -> None:
        """

        :param label:
        :param color:
        :return:
        """
        extra_colors =  {       # Convenient extra colors, not available thru standard CSS names
                    "graph_green": '#8DCC93',
                    "graph_darkgreen": '#56947f',
                    "graph_teal": '#569480',
                    "graph_orange": '#F79767',
                    "graph_blue": '#4C8EDA',
                    "graph_red": '#F16667',
                    "graph_darkbrown": '#604A0E',
                    "graph_lightbrown": '#D9C8AE',
                    "graph_orchid": '#C990C0',
                    "graph_gold": '#FFC454'     # Has a bit more orange than 'gold'
                }

        if color in extra_colors:
            color = extra_colors[color]

        self.color_mapping[label] = color