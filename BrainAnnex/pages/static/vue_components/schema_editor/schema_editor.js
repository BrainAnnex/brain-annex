Vue.component('vue-schema-editor',
    {
        props: ['class_list'],  <!-- NOTE:  Only lower cases in props names! -->
        /*  class_list:     List of all the names of the Classes in the Schema
         */

        template: `
            <div class='form-container'>  <!-- Outer container, serving as Vue-required template root.  OK to use a <section> instead -->


            <span v-if="waiting" class="waiting">Performing the requested operation...</span>
            <span v-bind:class="{'error-message': error, 'status-message': !error }">{{status_message}}</span>
            <br>


            <span class='title'>DELETE AN EXISTING RELATIONSHIP BETWEEN CLASSES</span><br><br>

            <table border='0' cellspacing='5' cellpadding='0'>
                <tr>
                    <td height="30px">From Existing Class:</td>
                    <td height="40px">Existing Relationship Name</td>
                    <td height="30px">To Existing Class:</td>
                </tr>

                <tr>
                    <td style='padding-left:5px'>
                        <select  v-model="del_linked_from">
                            <option value='-1'>[Choose an existing Class]</option>
                            <template v-for="item in class_list">
                                <option>{{item}}</option>
                            </template>
                        </select>
                    </td>

                    <td style='padding-left:5px'><input type='text' v-model="del_rel_name" size='30' maxlength='40'></td>

                    <td style='padding-left:5px'>
                        <select  v-model="del_linked_to">
                            <option value='-1'>[Choose an existing Class]</option>
                            <template v-for="item in class_list">
                                <option>{{item}}</option>
                            </template>
                        </select>
                    </td>

                </tr>
            </table>

            <br>
            <button @click="delete_relationship()" v-bind:disabled="!del_rel_name" style='padding: 15px'>
                Delete the {{del_rel_name}} Relationship
            </button>


            <br><br>
            <hr>



            <span class='title'>ADD A RELATIONSHIP BETWEEN EXISTING CLASSES</span><br><br>

            <table border='0' cellspacing='5' cellpadding='0'>
                <tr>
                    <td height="30px">From Existing Class:</td>
                    <td height="40px">New Relationship Name</td>
                    <td height="30px">To Existing Class:</td>
                </tr>

                <tr>
                    <td style='padding-left:5px'>
                        <select  v-model="add_linked_from">
                            <option value='-1'>[Choose an existing Class]</option>
                            <template v-for="item in class_list">
                                <option>{{item}}</option>
                            </template>
                        </select>
                    </td>

                    <td style='padding-left:5px'><input type='text' v-model="add_rel_name" size='30' maxlength='40'></td>

                    <td style='padding-left:5px'>
                        <select  v-model="add_linked_to">
                            <option value='-1'>[Choose an existing Class]</option>
                            <template v-for="item in class_list">
                                <option>{{item}}</option>
                            </template>
                        </select>
                    </td>

                </tr>
            </table>

            <br>
            <button @click="add_relationship()" v-bind:disabled="!add_rel_name" style='padding: 15px'>
                Add the {{add_rel_name}} Relationship
            </button>
            </div>		<!-- End of outer container -->
            `,



        data: function() {
            return {
                del_linked_from: -1,
                del_linked_to: -1,
                del_rel_name: "",

                add_linked_from: -1,
                add_linked_to: -1,
                add_rel_name: "",

                waiting: false,         // Whether any server request is still pending
                status_message: "",     // Message for user about the status of the last operation (NOT for "waiting" status)
                error: false            // Whether the last server communication resulted in error
            }
        },



        // ----------------  COMPUTED  -----------------
        computed: {
            name_of_class_to_link_to()
            // Name to show on the page
            {
                if (this.linked_to == -1)
                    return "Existing class ";
                else
                    return "'" + this.linked_to + "'";
            }
        },



        // ----------------  METHODS  -----------------
        methods: {

            /*
                SERVER CALLS
             */

            add_relationship()
            /* Initiate request to server to add a new Class with the specified Properties,
               in the given order
             */
            {
                console.log(`Processing request to add the relationship "${this.add_linked_from} - ${this.add_rel_name} -> ${this.add_linked_to}"`);
                //console.log(this.property_list);

                if (this.add_rel_name == "")  {
                    alert("Must enter a relationship name");
                    return;
                }
                if (this.from_class_name == -1)  {
                    alert("Must enter a class name that the new link originates from");
                    return;
                }
                if (this.to_class_name == -1)  {
                    alert("Must enter a class name that the new link goes to");
                    return;
                }


                // Send the request to the server, using a POST
                let url_server = "/BA/api/simple/add_schema_relationship";
                let post_obj = {from_class_name: this.add_linked_from,
                                to_class_name: this.add_linked_to,
                                rel_name: this.add_rel_name
                               };


                console.log(`About to contact the server at ${url_server}.  POST object:`);
                console.log(post_obj);

                this.waiting = true;
                this.status_message = "";   // Clear any message from the previous operation
                this.error = false;         // Clear any error from the previous operation

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server(url_server,
                            {post_obj: post_obj,
                             callback_fn: this.finish_add_relationship});
            },

            finish_add_relationship(success, server_payload, error_message, custom_data)
            // Callback function to wrap up the action of finish_add_relationship() upon getting a response from the server
            {
                console.log("Finalizing the finish_add_relationship operation...");
                if (success)  {     // Server reported SUCCESS
                    console.log("    server call was successful; it returned: ", server_payload);
                    this.status_message = `New relationship added`;
                    // Clear up the form
                    this.add_linked_from = -1;
                    this.add_linked_to = -1;
                    this.add_rel_name = "";
                }
                else  {             // Server reported FAILURE
                    this.error = true;
                    this.status_message = `FAILED creation of new relationship: ${error_message}`;
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;      // Make a note that the asynchronous operation has come to an end
            }


        }  // METHODS

    }
); // end component