Vue.component('vue_cytoscape_2',
    {
        props: {
            /* graph_data is an object with the keys:
                1) "structure"
                        EXAMPLE:
                            [{'id': 1, 'name': 'Julian', 'labels': ['PERSON']},
                             {'id': 2, 'color': 'white', 'labels': ['CAR']},
                             {'name': 'OWNS', 'source': 1, 'target': 2, 'id': 'edge-1'}]

                2) "color_mapping"
                        EXAMPLE:  {'PERSON': 'cyan', 'CAR': 'orange'}

                3) "caption_mapping"
                        EXAMPLE:  {'PERSON': 'name', 'CAR': 'color'}
             */
            graph_data: {
                required: true
            },

            component_id: {
                default: 1
            }
        },



        template: `
            <div>  <!-- Outer container, serving as Vue-required template root.  OK to use a <section> instead -->

                <div v-bind:id="'cy_' + component_id" class="cytoscape-container">
                    <!-- CYTOSCAPE.js WILL INSERT THE GRAPH HERE -->
                </div>

                <div class="legend">
                    <template v-for="item in node_info">
                        <span v-html="item"></span>
                        <br>
                    </template>
                </div>

            </div>		<!-- End of outer container -->
            `,



        // ----------------  DATA  -----------------
        data: function() {
            return {
                graph_structure: this.graph_data.structure,

                node_info: ["Click on a node to see its attributes"]
            }
        },



        // ----------------  MOUNTED  -----------------
        mounted() {
            /* Note: the "mounted" Vue hook is invoked later in the process of launching this component
             */
            console.log('The component is now mounted');

            this.create_graph('cy_' + this.component_id);    // This will let Cytoscape.js do its thing
        },



        // ----------------  COMPUTED  -----------------
        computed: {
            assemble_element_structure()
            /*  Create and return the graph structure needed by Cytoscape.js
                (a list of objects with a key named "data")
                EXAMPLE:
                    [
                        {data: {'id': 1, 'name': 'Julian', 'labels': ['PERSON']}
                        },
                        {data: {'id': 2, 'color': 'white', 'labels': ['CAR']}
                        },
                        {data: {'name': 'OWNS', 'source': 1, 'target': 2, 'id': 'edge-1'}
                        }
                    ]
             */
            {
                res = [];

                for (i in this.graph_structure) {   // Note:  i will be an integer, not an array element!!
                    el = {data: this.graph_structure[i]};
                    res.push(el);
                }

                console.log("assemble_element_structure produced:")
                console.log(res);

                return res;
            }
        },



        // ----------------  METHODS  -----------------
        methods: {
            create_graph(element_id)
            /*  This function needs to be invoked after this Vue component is "mounted".
                Replace the contents of the HTML element whose id is the given element_id
                with the graphic structure created by Cytoscape
             */
            {
                console.log(`Running create_graph() to replace page element with ID ${element_id}`);

                var cy_object = cytoscape({

                    container: document.getElementById(element_id),    // Container to render in

                    elements: this.assemble_element_structure,          // List of graph elements (nodes & edges)


                    style: [    // The stylesheet for the graph
                        {
                            selector: 'node',       // NODES
                            style: {
                                'width': 60,
                                'height': 60,
                                //'label': 'data(name)',
                                'label': this.node_caption_f,
                                //'background-color': '#8DCC93',
                                'background-color': this.node_color_f,

                                'border-width': 2,
                                //'border-color': '#5db665',
                                'border-color': this.node_border_color_f,

                                'font-size': '11px',
                                'color': '#101010',        // Color of the text
                                'text-halign': 'center',
                                'text-valign': 'center'
                            }
                        },

                        {
                            selector: 'edge',      // RELATIONSHIPS
                            style: {
                                'width': 2,
                                'line-color': '#C6C6C6',
                                'target-arrow-color': '#C6C6C6',
                                'target-arrow-shape': 'triangle',
                                'curve-style': 'bezier',
                                'label': 'data(name)',
                                'font-size': '10px',
                                'color': '#000',    // Color of the text
                                'text-rotation': 'autorotate',
                                'text-background-color': '#f6f6f6', // Same as graph background
                                'text-background-opacity': 1
                            }
                        },

                        {
                            selector: ':selected',
                            style: {
                                'background-color': 'yellow',
                                'line-color': 'red'
                            }
                        }

                    ],  // END of style


                    layout: {
                        name: 'breadthfirst',   // CHOICES: 'grid', 'circle', 'random', 'concentric', 'breadthfirst', 'cose'
                        rows: 1
                    }

                });

                cy_object.on('click', 'node', this.show_node_info);

                /*
                // EXAMPLES of adding nodes
                cy_object.add([
                    { data: { id: 4, labels: 'import' , name: 'Restaurants' }, position: {x: 80, y: 100} }
                ]);

                cy_object.add([
                    { data: { id: 5, labels: 'SOME_OTHER_LABELS' , name: 'Mr. Node' }, position: {x: 80, y: 200} }
                ]);
                */
            },



            /*
                SUPPORT FUNCTIONS
             */

            show_node_info(ev)
            // Invoked when clicking on a node
            {
                const node = ev.target;

                //console.log(node.position());   // EXAMPLE: {x: 361, y: 144}
                //console.log(node.id());
                //console.log(node.data());
                //console.log(node);
                //console.log(node.data);
                //console.log(node.data('name'));
                //console.log(Object.keys(node.data()));    // EXAMPLE: ['id', 'labels', 'name']

                const cyto_data_obj = node.data();
                let info_arr = [];
                for (k in cyto_data_obj) {
                    //console.log( k, cyto_data_obj[k] );
                    info_arr.push(`<b>${k}</b>: ${cyto_data_obj[k]}`);  // This will update the UI graph legend
                }
                //console.log(info_arr);

                const pos = node.position()
                const x = pos.x.toFixed(1);
                const y = pos.y.toFixed(1);
                //this.node_info = `id: ${node.id()} , x: ${x} , y: ${y}`;
                this.node_info = info_arr;
            },



            map_labels_to_color(labels)
            /*  Given the labels of a node (an array of strings),
                return the name of the color to use for the inside of the node,
                based on what was specified in "color_mapping" from the "graph_data" prop.
                In case of multiple labels, try them sequentially, until a mapping is found.
                If no mapping information is present for any of the labels, use the color white by default
             */
            {
                // The default value, in case no mapping info found for any of the labels
                const default_color = '#FFFFFF';    // TODO: assign colors on rotation instead

                //console.log("labels: ", labels);    // Example: ["PERSON"]
                //console.log(this.graph_data.color_mapping);

                for (single_label of labels) {
                    if (single_label in this.graph_data.color_mapping)  {
                        const color = this.graph_data.color_mapping[labels];
                        //console.log(`Using the color '${color}' for the inside of this node`);
                        return color;
                    }
                }

                return default_color;
            },


            map_labels_to_caption_field(labels)
            /*  Given the labels of a node (an array of strings),
                return the name of the field to use for the node caption,
                based on what was specified in "caption_mapping" from the "graph_data" prop.
                In case of multiple labels, try them sequentially, until a mapping is found.
                If no mapping information is present for any of the labels, use the field name "id" by default
             */
            {
                // The default value, in case no mapping info found for any of the labels
                const default_caption_field_name = "id";

                //console.log("labels: ", labels);    // Example: ["PERSON"]
                //console.log(this.graph_data.caption_mapping);

                for (single_label of labels) {
                    if (single_label in this.graph_data.caption_mapping)  {
                        const caption_field_name = this.graph_data.caption_mapping[labels];
                        //console.log(`Using the field '${caption_field_name}' for the caption of this node`);
                        return caption_field_name;
                    }
                }

                return default_caption_field_name;
            },



            node_caption_f(ele)
            /*  Function to generate the caption to show on the graph, for a given node.
                The caption is based on the node's labels; in the absence of a user-specified mapping,
                the data in the field "id" is used as caption.

                Note: the various fields of the node may be extracted from the argument ele (representing a node element)
                      as ele.data(field_name).  For example: ele.data("id")
             */
            {
                //console.log("Determining node caption for node with id: ", ele.data("id"));
                //console.log("    and labels: ", ele.data("labels"));

                const field_to_use_as_caption = this.map_labels_to_caption_field(ele.data("labels"));

                return ele.data(field_to_use_as_caption)
            },


            node_color_f(ele)
            /*  Function to generate the color to use for the inside of the given node.
                The color is based on the node's labels; in the absence of a user-specified mapping,
                white is used.

                Note: the various fields of the node may be extracted from the argument ele (representing a node element)
                      as ele.data(field_name).  For example: ele.data("id")
             */
            {
                //console.log("Determining color for node with id: ", ele.data("id"));
                //console.log("    and labels: ", ele.data("labels"));

                return this.map_labels_to_color(ele.data("labels"));
            },


            node_border_color_f(ele)
            /*  Function to generate the color to use for the border of the node
                passed as argument (as a graph element).
                The relationship between the interior and edge color is:
                same Hue/Saturation but less Luminosity
             */
            {
                //console.log(this.graph_data.color_mapping);
                //console.log(ele.data("labels"));
                const interior_color = this.node_color_f(ele);
                //console.log(interior_color);
                const c = d3.hsl(interior_color);
                //console.log(c);
                const c_new = c.darker(0.635).formatHex();  // Less Luminosity
                //console.log(c_new);
                return c_new;
            }


        }  // METHODS

    }
); // end component