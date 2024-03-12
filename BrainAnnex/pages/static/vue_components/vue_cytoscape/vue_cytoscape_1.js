Vue.component('vue_cytoscape_1',  <!-- NOTE:  Only lower cases in component names! -->
    {
        props: {
            <!-- NOTE:  Only lower cases in props names! -->

            graph: {
            },

            color_mapping: {        // Mapping the node label to its interior color
                required: true      // For now (TODO: auto-assign if unspecified; SEE vue_curves_4.js)
            },

            component_id: {
                default: 1
            }

        },

        my_optional_component_metadata: 123,   <!-- Available thru this.$options.metadata -->

        template: `
            <div>  <!-- Outer container, serving as Vue-required template root.  OK to use a <section> instead -->

                <div v-bind:id="'cy_' + component_id" class="cytoscape-container">
                    <!-- CYTOSCAPE.js WILL INSERT THE GRAPH HERE -->
                </div>

                <div class="legend">
                    <template v-for="item in node_info">{{item}}<br></template>
                </div>

            </div>		<!-- End of outer container -->
            `,



        data: function() {
            return {
                // Convenient extra colors, not available thru standard CSS names
                nonstandard_colors:  {
                    neo4j_green: '#8DCC93',
                    neo4j_teal: '#569480',
                    neo4j_orange: '#F79767',
                    neo4j_blue: '#4C8EDA',
                    neo4j_red: '#F16667',
                    neo4j_darkbrown: '#604A0E',
                    neo4j_lightbrown: '#D9C8AE',
                    neo4j_orchid: '#C990C0',
                    neo4j_gold: '#FFC454'     // Has a bit more orange than 'gold'
                },

                graph_structure: this.graph,

                node_info: ["Click on a node to see its attributes"]
            }
        },



        watch: {
            /*
            some_data_b() {
                console.log('The prop `some_data_b` has changed!');
            }
            */
        },



        mounted() {
            /* Note: the "mounted" Vue hook is invoked later in the process of launching this component
             */
            console.log('The component is now mounted');

            this.create_graph();    // This will let Cytoscape.js do its thing
        },



        // ----------------  COMPUTED  -----------------
        computed: {
            assemble_element_structure()
            /*  Create and return the graph structure needed by Cytoscape.js
                (a list of objects with a key named "data")
                EXAMPLE:
                    [
                        {data: {id: 1, name: 'Headers', label: 'CLASS'}
                        },
                        {data: {id: 2, name: 'text', label: 'PROPERTY'}
                        },
                        {data: {id: 3, source: 1, target: 2, name: 'HAS_PROPERTY'}
                        }
                    ]
             */
            {
                res = [];

                for (i in this.graph_structure) {   // Note:  i will be an integer, not an array element!!
                    el = {data: this.graph_structure[i]};
                    res.push(el);
                }

                console.log(res);

                return res;
            }
        },



        // ----------------  METHODS  -----------------
        methods: {
            create_graph()
            /* The main part of the old Cytoscape code got moved here,
                EXCEPT for the DIV element <div id="SOME_ID">,
                which is now in the Vue template, above
             */
            {
                console.log('Running create_graph()');

                var cy_object = cytoscape({

                    container: document.getElementById('cy_' + this.component_id),    // Container to render in

                    elements: this.assemble_element_structure,   // List of graph elements (nodes & edges)


                    style: [ // the stylesheet for the graph
                        {
                            selector: 'node',       // NODES
                            style: {
                                'width': 60,
                                'height': 60,
                                'label': 'data(name)',
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
                                'font-size': '9px',
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
                        name: 'circle',   // OR: 'grid'
                        rows: 1
                    }

                });

                cy_object.on('click', 'node', this.show_node_info);

                /*
                // EXAMPLES of adding nodes
                cy_object.add([
                    { data: { id: 4, label: 'import' , name: 'Restaurants' }, position: {x: 80, y: 100} }
                ]);

                cy_object.add([
                    { data: { id: 5, label: 'SOME_OTHER_LABEL' , name: 'Mr. Node' }, position: {x: 80, y: 200} }
                ]);
                */
            },



            /*
                SUPPORT FUNCTIONS
             */

            show_node_info(ev)
            // Invoked when clicking on a node
            {
                var node = ev.target;
                console.log(node.position());
                //console.log(node.id());
                //console.log(node.data());
                //console.log(node);
                //console.log(node.data);
                //console.log(node.data('name'));
                console.log(Object.keys(node.data()));

                const cyto_data_obj = node.data();
                let info_arr = [];
                for (k in cyto_data_obj) {
                    //console.log( k, cyto_data_obj[k] );
                    info_arr.push(`${k}: ${cyto_data_obj[k]}`);
                }
                //console.log(info_arr);

                const pos = node.position()
                const x = pos.x.toFixed(1);
                const y = pos.y.toFixed(1);
                //this.node_info = `id: ${node.id()} , x: ${x} , y: ${y}`;
                this.node_info = info_arr;
            },


            node_color_f(ele)
            /*  Determine and return the color to use for the inside of the node
                passed as argument (as a graph element)
             */
            {
                const default_color = '#FFFFFF';    // TODO: assign colors on rotation instead

                //console.log(this.color_mapping);
                //console.log(ele.data("label"));
                const label = ele.data("label");  // Counterpart of Neo4j node label (but only 1 for now)
                if (label in this.color_mapping)  {
                    let requested_color = this.color_mapping[label];
                    if (requested_color in this.nonstandard_colors)
                        return this.nonstandard_colors[requested_color];
                    else
                        return requested_color;
                }
                else
                    return default_color;
            },


            node_border_color_f(ele)
            /*  Determine and return the color to use for the border of the node
                passed as argument (as a graph element).
                The relationship between the interior and edge color emulates
                the Neo4j browser interface (same Hue/Saturation but less Luminosity)
             */
            {
                //console.log(this.color_mapping);
                //console.log(ele.data("label"));
                const interior_color = this.node_color_f(ele);
                //console.log(interior_color);
                const c = d3.hsl(interior_color);
                //console.log(c);
                const c_new = c.darker(0.635).formatHex();  // This value emulates the Neo4j browser interface
                //console.log(c_new);
                return c_new;
            }


        }  // METHODS

    }
); // end component