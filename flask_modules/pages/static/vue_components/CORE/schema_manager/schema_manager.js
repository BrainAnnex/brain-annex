/*  Vue component
 */

Vue.component('vue-schema-manager',
    {
        props: ['class_name'],
        /*  class_list:     List of all the names of the Classes in the Schema
         */

        template: `
            <div class='schema-manager'>	<!-- Outer container, serving as Vue-required template root  -->

                <p>PROPERTIES:</p>

                <ul>
                    <li v-for="item in class_properties">
                        <b>{{item}}</b><br>
                        <span style="color:gray">Description:</span> N/A<br>
                        <span style="color:gray">Data type:</span> N/A<br>
                    </li>
                </ul>



            </div>		<!-- End of outer container -->
            `,



        // ------------------------------   DATA   ------------------------------
        data: function() {

            return {

                class_properties: [],

                waiting: false,         // Whether any server request is still pending
                error: false,           // Whether the last server communication resulted in error
                status_message: ""      // Message for user about status of last operation upon server response (NOT for "waiting" status)
            }
        }, // data




        // ------------------------------------   HOOKS   ------------------------------------

        mounted()
        /* Note: the "mounted" Vue hook is invoked later in the process of launching this component.
         */
        {
            console.log(`The schema-editor component has been mounted`);
            this.fetch_properties();
        },




        // ------------------------------------   COMPUTED   ------------------------------------

        computed: {
        },




        // ------------------------------   METHODS   ------------------------------
        methods: {


            /*
                ------------------   SERVER CALLS   ------------------
             */

            /**
             * Retrieve all the Schema Properties associated to this Class,
             * and return the array of their names
             */
            fetch_properties()
            {
                //return ["a", 'b', 'c'];
                this.get_fields();
            },


            /**
             * Make a server call to obtain all the field names associated to a sample of nodes with the given label.
                E.g.
                    GraphSchema.get_class_properties(class_node="Quote", include_ancestors=True, exclude_system=True)
                to fetch:
                    ['quote', 'attribution', 'notes']

                If successful, it will update the value for this.class_properties
             */
            get_fields()
            {
                console.log(`In get_fields(): attempting to retrieve property names of the Class '${this.class_name}'`);

                const url_server_api = "/BA/api/get_class_properties";

                const data_obj = {class_name: this.class_name,
                                  include_ancestors: true,
                                  exclude_system: true
                                  };

                console.log(`About to contact the server at ${url_server_api} .  GET object:`);
                console.log(data_obj);

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server(url_server_api,
                            {   data_obj: data_obj,
                                json_encode_send: true,
                                callback_fn: this.finish_get_fields
                            });

                this.waiting = true;        // Entering a waiting-for-server mode
                this.error = false;         // Clear any error from the previous operation
                this.status_message = "";   // Clear any message from the previous operation
            },

            finish_get_fields(success, server_payload, error_message)
            // Callback function to wrap up the action of get_fields() upon getting a response from the server
            {
                //console.log("Finalizing the get_fields() operation...");
                if (success)  {     // Server reported SUCCESS
                    //console.log("    server call was successful; it returned: ", server_payload);
                    this.status_message = `Operation completed`;
                    this.class_properties = server_payload;
                }
                else  {             // Server reported FAILURE
                    this.error = true;
                    this.status_message = `FAILED operation: ${error_message}`;
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;      // Make a note that the asynchronous operation has come to an end

            }, // finish_get_fields


        }  // methods

    }
); // end component