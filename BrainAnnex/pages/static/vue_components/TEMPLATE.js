Vue.component('vue-some-name',  <!-- NOTE:  Only lower cases in component names! -->
    {
        props: {
            <!-- NOTE:  Only lower cases in props names! -->

            some_data_a: {
                type: Boolean,
                required: true
            },

            some_data_b: {
                type: Number,
                default: 0
            }
        },

        my_optional_component_metadata: 123,   <!-- Available thru this.$options.metadata -->

        template: `
            <div>  <!-- Outer container, serving as Vue-required template root.  OK to use a <section> instead -->

            <button @click="count++">{{ count }}</button>
            <input type='text' v-model="nickname" placeholder="Specify nickname">

            <!-- Status info -->
            <span v-if="waiting" class="waiting">Performing the requested operation... [OR A MORE SPECIFIC DESCRIPTION]</span>
            <span v-bind:class="{'error-message': error, 'status-message': !error }">{{status_message}}</span>

            </div>		<!-- End of outer container -->
            `,



        data: function() {
            return {
                count: 0,
                nickname: this.some_data_a,

                waiting: false,         // Whether any server request is still pending
                error: false,           // Whether the last server communication resulted in error
                status_message: ""      // Message for user about status of last operation upon server response (NOT for "waiting" status)
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
            //console.log('The component is now mounted');
        },



        // ----------------  COMPUTED  -----------------
        computed: {
            example() {
                return this.my_count+ 10;
            }
        },



        // ----------------  METHODS  -----------------
        methods: {
            foo() {
                console.log("In foo. some_data_a= " + this.some_data_a);
            },



            /*
                SERVER CALLS
             */

            get_data_from_server_POST()          /* "POST"  version */
            /* Initiate request to server
             */
            {
                // Send the request to the server, using a POST
                let url_server_api = "/BA/api/SOME_API_ENDPOINT";
                let my_var = "some value";  // Optional parameter, if needed
                let post_obj = {my_var: my_var};

                console.log(`About to contact the server at ${url_server_api}.  POST object:`);
                console.log(post_obj);

                this.waiting = true;        // Entering a waiting-for-server mode
                this.error = false;         // Clear any error from the previous operation
                this.status_message = "";   // Clear any message from the previous operation

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server(url_server_api,
                            {post_obj: post_obj,
                             callback_fn: this.finish_get_data_from_server,
                             custom_data: [my_var]
                             });
            },


            get_data_from_server_GET()          /* "GET"  version */
            /* Initiate request to server
             */
            {
                // Send the request to the server, using a GET
                let url_server_api = "/BA/api/SOME_API_ENDPOINT";
                let my_var = "some value";  // Optional parameter, if needed
                console.log(`About to contact the server at ${url_server_api}`);

                this.waiting = true;        // Entering a waiting-for-server mode
                this.error = false;         // Clear any error from the previous operation
                this.status_message = "";   // Clear any message from the previous operation

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server(url_server_api,
                            {callback_fn: this.finish_get_data_from_server,
                             custom_data: [my_var]
                             });
            },



            finish_get_data_from_server(success, server_payload, error_message, custom_data)
            // Callback function to wrap up the action of get_data_from_server() upon getting a response from the server
            {
                console.log("Finalizing the get_data_from_server operation...");
                if (success)  {     // Server reported SUCCESS
                    console.log("    server call was successful; it returned: ", server_payload);
                    this.status_message = `Operation completed`;
                    //...
                }
                else  {             // Server reported FAILURE
                    this.error = true;
                    this.status_message = `FAILED operation: ${error_message}`;
                    //...
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;      // Make a note that the asynchronous operation has come to an end
                //...
            }

        }  // METHODS

    }
); // end component