Vue.component('vue-some-name',  <!-- NOTE:  Only lower cases in component names! -->
    {
        props: ['some_data_a', 'some_data_b'],  <!-- NOTE:  Only lower cases in props names! -->
        /*  some_data_a:
            some_data_b:
         */

        my_optional_component_metadata: 123,   <!-- Available thru this.$options.metadata -->

        template: `
            <div>  <!-- Outer container, serving as Vue-required template root.  OK to use a <section> instead -->

            <button @click="count++">{{ count }}</button>
            <input type='text' v-model="nickname" placeholder="Specify nickname">

            </div>		<!-- End of outer container -->
            `,



        data: function() {
            return {
                my_count: 0,
                nickname: this.some_data_a
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

            get_data_from_server()
            /* Initiate request to server
             */
            {
                // Send the request to the server, using a POST
                let url_server = "/BA/api/SOME_API_ENDPOINT";
                let post_obj = {item_id: record_id, rel_name: rel_name, dir: dir};
                console.log(`About to contact the server at ${url_server}.  POST object:`);
                console.log(post_obj);

                this.waiting = true;
                this.status_message = "";   // Clear any message from the previous operation
                this.error = false;         // Clear any error from the previous operation

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server(url_server,
                            {payload_type: "JSON",
                             post_obj: post_obj,
                             callback_fn: this.finish_get_linked_records_from_server,
                             custom_data: [rel_name, dir]});
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