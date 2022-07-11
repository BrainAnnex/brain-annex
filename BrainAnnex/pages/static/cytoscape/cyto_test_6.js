Vue.component('vue-cyto',  <!-- NOTE:  Only lower cases in component names! -->
    {
        props: {
            <!-- NOTE:  Only lower cases in props names! -->

            graph: {
            }

        },

        my_optional_component_metadata: 123,   <!-- Available thru this.$options.metadata -->

        template: `
            <div>  <!-- Outer container, serving as Vue-required template root.  OK to use a <section> instead -->

                <div id="cy">
                <!-- CYTOSCAPE.js WILL INSERT THE GRAPH HERE -->
                </div>

            </div>		<!-- End of outer container -->
            `,



        data: function() {
            return {
                // Mapping the node label to its interior color
                color_mapping:  {
                    CLASS: '#8DCC93',
                    PROPERTY: '#F79767',
                    import: '#4C8EDA'
                },

                graph_structure: this.graph
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
            /*  Create and return the graph structure needed by Cystoscape.js
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
                EXCEPT for the DIV element <div id="cy">,
                which is now in the Vue template, above
             */
            {
                console.log('Running create_graph()');

                var cy = cytoscape({

                    container: document.getElementById('cy'),    // Container to render in

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

                cy.on('click', 'node', function(ev) {
                    var node = ev.target;
                    console.log(node.position());
                    }
                );

                /*
                // EXAMPLES of adding nodes
                cy.add([
                    { data: { id: 4, label: 'import' , name: 'Restaurants' }, position: {x: 80, y: 100} }
                ]);

                cy.add([
                    { data: { id: 5, label: 'SOME_OTHER_LABEL' , name: 'Mr. Node' }, position: {x: 80, y: 200} }
                ]);
                */
            },



            /*
                SUPPORT FUNCTIONS
             */

            node_color_f(ele)
            /*  Determine and return the color to use for the inside of the node
                passed as argument (as a graph element)
             */
            {
                //console.log(this.color_mapping);
                //console.log(ele.data("label"));
                const label = ele.data("label");  // Counterpart of Neo4j node label (but only 1 for now)
                if (label in this.color_mapping)
                    return this.color_mapping[label];
                else
                    return '#FFFFFF';       // Default color
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