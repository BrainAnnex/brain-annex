Vue.component('vue-schema-editor',
    {
        props: [],  <!-- NOTE:  Only lower cases in props names! -->
        /*  some_data_a:
            some_data_b:
         */

        template: `
            <div>  <!-- Outer container, serving as Vue-required template root.  OK to use a <section> instead -->

            <span class='title'>CREATE A NEW SCHEMA CLASS :</span><br><br>


            <table border='0' cellspacing='5' cellpadding='0'>
                <tr>
                    <td height="40px">Name</td>
                    <td style='padding-left:5px'><input type='text' v-model="new_class_name" size='30' maxlength='40'></td>
                </tr>

                <tr v-for="i in number_properties">
                    <td>Property {{i}}</td>
                    <td style='padding-left:5px'><input type='text'  v-model="property_list[i-1]" size='30' maxlength='40'></td>
                </tr>

                <tr>
                    <td colspan="2" align="right">
                        <img @click="number_properties++" src='/BA/pages/static/graphics/plus_green_32_41688.png'
                             alt='Add an extra property' title='Add an extra property'>
                    </td>
                </tr>
            </table>



            <br>
            <button @click="add_class()" v-bind:disabled="!new_class_name" style='padding: 15px'>
                <template v-if="new_class_name">
                    Add New "{{new_class_name}}" Class
                </template>
                <template v-else>
                  Must specify a Class name
                </template>
            </button>
                <span v-if="waiting" class="waiting">Adding the subcategory...</span>
                <span v-bind:class="{'error-message': error, 'status-message': !error }">{{status_message}}</span>
            <br><br>

            </div>		<!-- End of outer container -->
            `,



        data: function() {
            return {
                new_class_name: "",

                number_properties: 3,

                property_list: [],

                waiting: false,         // Whether any server request is still pending
                status_message: "",     // Message for user about the status of the last operation (NOT for "waiting" status)
                error: false            // Whether the last server communication resulted in error
            }
        },



        // ----------------  METHODS  -----------------
        methods: {

            /*
                SERVER CALLS
             */

            add_class()
            /* Initiate request to server to add a new Class with the specified Properties,
               in the given order
             */
            {
                console.log(`Processing request to add Class "${this.new_class_name}"`);
                //console.log(this.property_list);

                if (this.new_class_name == "")  {
                    alert("Must enter a Class name");
                    return;
                }

                let post_data = this.new_class_name + ",";

                properties_length = this.property_list.length;
                for (let i = 0; i < properties_length; i++) {
                    let property_name = this.property_list[i];
                    if (property_name)
                        post_data += this.property_list[i] + ",";
                }

                //console.log(post_data);

                // Send the request to the server, using a POST
                let url_server = "/BA/api/simple/create_new_record_class";
                let post_obj = {data: post_data};
                console.log(`About to contact the server at ${url_server}.  POST object:`);
                console.log(post_obj);

                this.waiting = true;
                this.status_message = "";   // Clear any message from the previous operation
                this.error = false;         // Clear any error from the previous operation

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server(url_server,
                            {post_obj: post_obj,
                             callback_fn: this.finish_add_class});
            },

            finish_add_class(success, server_payload, error_message, custom_data)
            // Callback function to wrap up the action of add_class() upon getting a response from the server
            {
                console.log("Finalizing the add_class operation...");
                if (success)  {     // Server reported SUCCESS
                    console.log("    server call was successful; it returned: ", server_payload);
                    this.status_message = `New Class added`;
                    // Clear up the form
                    this.new_class_name = "";
                    this.property_list = [];
                }
                else  {             // Server reported FAILURE
                    this.error = true;
                    this.status_message = `FAILED addition of new Class: ${error_message}`;
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;      // Make a note that the asynchronous operation has come to an end
            }


        }  // METHODS

    }
); // end component