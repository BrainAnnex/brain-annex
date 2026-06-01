/*  Vue component, to display and edit the database Schema.
    Used in the "database_overview" page.
 */

Vue.component('vue-schema-manager',
    {
        props: ['class_name'],
        /*  class_name:     Name of the Schema Class of interest
         */

        template: `
            <div class='schema-manager'>	<!-- Outer container, serving as Vue-required template root  -->

                CLASS <span class='label-name'>"{{class_name}}"</span><br>
                <span style="color:gray">Description:</span>
                N/A  <a v-on:click.prevent="add_description(class_name)"  href="#" style="margin-left:20px">ADD</a>


                <p>PROPERTIES:</p>

                <ul>
                    <li v-for="item in class_properties">
                        <b>{{item.name}}</b>
                        <span style="font-size: 11px; color: gray">(id {{item._internal_id}})</span>
                        <br>

                        <span style="color:gray">Description:</span>
                        <span v-if="item.description !== undefined" style="background-color:white">{{item.description}}</span>
                        <span v-else>N/A  <a v-on:click.prevent="add_description(item._internal_id)"  href="#" style="margin-left:20px">ADD</a></span>
                        <br>

                        <span style="color:gray">Data type:</span>
                        <span v-if="item.dtype !== undefined" style="background-color:white">{{item.dtype}}</span>
                        <span v-else>N/A  <a v-on:click.prevent="add_description(item._internal_id)"  href="#" style="margin-left:20px">CHOOSE</a></span>
                        <br>

                        <span style="color:gray">Required? :</span>
                        <span v-if="item.required !== undefined" style="background-color:white">{{item.required}}</span>
                        <span v-else>N/A</span>
                        <br>

                        <template v-if="item.system !== undefined">
                            <span style="color:gray">System:</span>
                            <span style="background-color:white">{{item.system}}</span>
                            <br>
                        </template>

                        <template v-if="item.format !== undefined">
                            <span style="color:gray">Format:</span>
                            <span style="background-color:white">{{item.format}}</span>
                            <br>
                        </template>
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

            add_description(internal_id)
            {
                alert("Not yet implemented");
            },



            /*
                ------------------   SERVER CALLS   ------------------
             */

            /**
             * Retrieve all the data of all the Schema Properties associated to this Class.
             * Store the results in the Vue variable `class_properties`
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
                    TBA

                If successful, it will update the value for this.class_properties
             */
            get_fields()
            {
                console.log(`In get_fields(): attempting to retrieve Property data of the Class '${this.class_name}'`);

                //const url_server_api = "/BA/api/get_class_properties";
                const url_server_api = "/BA/api/class-properties-full-data";

                const data_obj = {class_name: this.class_name
                                  //, include_ancestors: true,
                                  //exclude_system: true
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