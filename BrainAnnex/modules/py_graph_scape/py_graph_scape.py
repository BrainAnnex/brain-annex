from typing import Union


class PyGraphScape:     # Alternate name: PyGraphVisual
    """

    GraphicLog.export_plot(PyGraphScape_object, "vue_cytoscape_1")
    """


    def __init__(self):
        self.graph_data = []
        self.graph_color_mapping = {}
        self.id_map = {}
        self.next_available_id = 0



    def add_node(self, uri :Union[str, int], label :str, data :dict, name=None) -> None:
        """
        :param uri:     Either an integer or a string to uniquely identify this node in the graph;
                            it will use to specify the start/end nodes of edges
        :param label:   A string with the node's label used in the graph database; if not use, pass an empty string
                            (TODO: or a list of strings)
        :param data:    A dict with all other node data not specified in any of the other arguments
        :param name:    An optional string meant to be displayed by default on the node;
                            if not specified, a decision will be made by the front end about with other data field
                            to use (for example the value of the "uri" argument
        :return:        None
        """
        if type(uri) == str:
            assert uri != "", "add_node(): cannot use an empty string for the argument `uri'"

        d = data.copy()     # Make an independent clone

        d["id"] = self.next_available_id
        self.id_map[uri] = self.next_available_id
        self.next_available_id += 1

        d["label"] = label

        if name:
            d["name"] = name

        self.graph_data.append(d)



    def add_edge(self, from_node :Union[str, int], to_node :Union[str, int], name :str) -> None:
        """
        :param from_node:
        :param to_node:
        :param name:
        :return:            None
        """
        from_id = self.id_map.get(from_node)
        to_id = self.id_map.get(to_node)

        d = {"name": name, "source": from_id, "target": to_id}

        d["id"] = self.next_available_id
        self.next_available_id += 1

        self.graph_data.append(d)



    def assign_color_mapping_OLD(self, color_mapping :dict) -> None:
        """

        :param color_mapping:
        :return:
        """
        self.graph_color_mapping = color_mapping



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

        self.graph_color_mapping[label] = color