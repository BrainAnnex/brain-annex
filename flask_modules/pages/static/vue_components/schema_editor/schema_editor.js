/* To provide various operations to edit an existing Schema */

Vue.component('vue-schema-editor',
    {
        props: ['class_list'],  <!-- NOTE:  Only lower cases in props names! -->
        /*  class_list:     List of all the names of the Classes in the Schema
         */

        template: `
            <div class='form-container'>  <!-- Outer container, serving as Vue-required template root.  OK to use a <section> instead -->

            <!-- Status of the last operation -->
            <span v-if="waiting" class="waiting">Performing the requested operation...</span>
            <span v-bind:class="{'error-message': error, 'status-message': !error }">{{status_message}}</span>
            <br>


            <!-- ----------------------------------------------------------------------------------- -->
            <template>
                <span class='title'>ADD A PROPERTY TO AN EXISTING CLASS</span><br><br>

                <table border='0' cellspacing='5' cellpadding='0'>
                    <tr>
                        <td height="40px">Existing Class:</td>
                        <td>New Property Name</td>
                        <td>&nbsp;</td>
                    </tr>

                    <tr>
                        <td style='padding-left:5px'>
                            <select  v-model="class_to_add_prop_to">
                                <option value='-1'>[Choose an existing Class]</option>
                                <template v-for="item in class_list">
                                    <option>{{item}}</option>
                                </template>
                            </select>
                        </td>

                        <td style='padding-left:5px'>
                            <input type='text' v-model="add_prop_name" size='30' maxlength='40'>
                        </td>

                        <td style='padding-left:5px'>
                            <button @click="add_property(add_prop_name, class_to_add_prop_to)"
                                    v-bind:disabled="add_prop_name.trim() == ''" style='padding: 15px'
                            >
                                Add the Property {{add_prop_name}}
                            </button>
                        </td>

                    </tr>
                </table>

            </template>

            <br><br>
            <hr>

            <!-- ----------------------------------------------------------------------------------- -->
            <span class='title'>DELETE AN EXISTING RELATIONSHIP BETWEEN CLASSES</span><br><br>

            <table border='0' cellspacing='5' cellpadding='0'>
                <tr>
                    <td height="40px">From Existing Class:</td>
                    <td>Existing Relationship Name</td>
                    <td>To Existing Class:</td>
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
            <button @click="delete_relationship()" v-bind:disabled="del_rel_name.trim() == ''" style='padding: 15px'>
                Delete the {{del_rel_name}} Relationship
            </button>


            <br><br>
            <hr>


            <!-- ----------------------------------------------------------------------------------- -->
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
            <button @click="add_relationship()" v-bind:disabled="add_rel_name.trim() == ''" style='padding: 15px'>
                Add the {{add_rel_name}} Relationship
            </button>



            <br><br>
            <hr>


            <!-- ----------------------------------------------------------------------------------- -->
            <template>
                <span class='title'>DELETE AN EXISTING CLASS</span> &nbsp; (and all its Properties)<br><br>

                <table border='0' cellspacing='5' cellpadding='0'>

                    <tr>
                        <td style='padding-left:5px'>
                            <select  v-model="del_class_name">
                                <option value=''>[Choose an existing Class]</option>
                                <template v-for="item in class_list">
                                    <option>{{item}}</option>
                                </template>
                            </select>
                        </td>
                        <td style='font-style:italic'>
                        Classes can be deleted only if there are no data points of that class
                        </td>

                    </tr>
                </table>

                <br>
                <button @click="delete_class()" v-bind:disabled="del_class_name.trim() == ''" style='padding: 15px'>
                    Delete the Class {{del_class_name}}
                </button>

            </template>  <!-- END DELETE AN EXISTING CLASS -->


            </div>		<!-- END of outer container -->
            `,



        data: function() {
            return {
                del_linked_from: -1,
                del_linked_to: -1,
                del_rel_name: "",

                // To add a Property to an existing Class
                class_to_add_prop_to: -1,   // Name of Class to which add a Property
                add_prop_name: "",          // Name of Property to add to an existing Class

                add_linked_from: -1,
                add_linked_to: -1,
                add_rel_name: "",

                del_class_name: "",         // Name of Class to delete

                // Status-related
                waiting: false,         // Whether any server request is still pending
                status_message: "",     // Message for user about the status of the last operation (NOT for "waiting" status)
                error: false            // Whether the last server communication resulted in error
            }
        },



        // ----------------  COMPUTED  -----------------
        computed: {
        },



        // ----------------  METHODS  -----------------
        methods: {

            /*
                SERVER CALLS
             */

            add_property(add_prop_name, class_to_add_prop_to)
            /* Initiate request to server to add a new Property to an existing Classes
             */
            {
                //console.log(`Processing request to add a property named "${this.add_prop_name}" to the Class "${this.class_to_add_prop_to}"`);
                console.log(`Processing request to add a property named "${add_prop_name}" to the Class "${class_to_add_prop_to}"`);

                if (class_to_add_prop_to == "")  {
                    alert("Must first select a Class name");
                    return;
                }
                if (add_prop_name == -1)  {
                    alert("Must enter a name for the new Property");
                    return;
                }


                // Send the request to the server, using a POST
                let url_server = "/BA/api/schema_add_property_to_class";
                let post_obj = {prop_name: add_prop_name.trim(),
                                class_name: class_to_add_prop_to
                               };


                console.log(`About to contact the server at ${url_server}.  POST object:`);
                console.log(post_obj);

                this.waiting = true;
                this.status_message = "";   // Clear any message from the previous operation
                this.error = false;         // Clear any error from the previous operation

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server_OLD(url_server,
                            {post_obj: post_obj,
                             callback_fn: this.finish_add_property});
            },

            finish_add_property(success, server_payload, error_message, custom_data)
            // Callback function to wrap up the action of finish_add_property() upon getting a response from the server
            {
                console.log("Finalizing the finish_add_property operation...");
                if (success)  {     // Server reported SUCCESS
                    console.log("    server call was successful; it returned: ", server_payload);
                    this.status_message = `New property added`;
                    // Clear up the form
                    this.class_to_add_prop_to = -1;
                    this.add_prop_name = "";
                }
                else  {             // Server reported FAILURE
                    this.error = true;
                    this.status_message = `FAILED creation of new property: ${error_message}`;
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;      // Make a note that the asynchronous operation has come to an end
            },




            // ---------------------------------------

            delete_class()
            /* Initiate request to server to delete the specified Class
             */
            {
                console.log(`Processing request to delete the Class "${this.del_class_name}"`);

                if (this.del_class_name == "")  {
                    alert("Must enter a class name");
                    return;
                }

                // Send the request to the server, using a POST
                let url_server = "/BA/api/delete_class";
                let post_obj = {class_name: this.del_class_name
                               };

                console.log(`About to contact the server at ${url_server}.  POST object:`);
                console.log(post_obj);

                this.waiting = true;
                this.status_message = "";   // Clear any message from the previous operation
                this.error = false;         // Clear any error from the previous operation

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server_OLD(url_server,
                            {post_obj: post_obj,
                             callback_fn: this.finish_delete_class});
            },

            finish_delete_class(success, server_payload, error_message, custom_data)
            // Callback function to wrap up the action of delete_relationship() upon getting a response from the server
            {
                console.log("Finalizing the delete_class operation...");
                if (success)  {     // Server reported SUCCESS
                    console.log("    server call was successful; it returned: ", server_payload);
                    this.status_message = `Class deleted`;
                    // Clear up the form
                    this.del_class_name = "";
                    // TODO: ought to change the list of Class (currently kept as a prop) accordingly
                }
                else  {             // Server reported FAILURE
                    this.error = true;
                    this.status_message = `FAILED deletion of class: ${error_message}`;
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;      // Make a note that the asynchronous operation has come to an end
            },


            // ---------------------------------------

            delete_relationship()
            /* Initiate request to server to delete the specified relationship between Classes
             */
            {
                console.log(`Processing request to delete the relationship "${this.del_linked_from} - ${this.del_rel_name} -> ${this.del_linked_to}"`);

                if (this.del_rel_name == "")  {
                    alert("Must enter a relationship name");
                    return;
                }
                if (this.del_linked_from == -1)  {
                    alert("Must enter a class name that the link originates from");
                    return;
                }
                if (this.del_linked_to == -1)  {
                    alert("Must enter a class name that the link goes to");
                    return;
                }

                // Send the request to the server, using a POST
                let url_server = "/BA/api/delete_schema_relationship";
                let post_obj = {from_class_name: this.del_linked_from,
                                to_class_name: this.del_linked_to,
                                rel_name: this.del_rel_name
                               };

                console.log(`About to contact the server at ${url_server}.  POST object:`);
                console.log(post_obj);

                this.waiting = true;
                this.status_message = "";   // Clear any message from the previous operation
                this.error = false;         // Clear any error from the previous operation

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server_OLD(url_server,
                            {post_obj: post_obj,
                             callback_fn: this.finish_delete_relationship});
            },

            finish_delete_relationship(success, server_payload, error_message, custom_data)
            // Callback function to wrap up the action of delete_relationship() upon getting a response from the server
            {
                console.log("Finalizing the delete_relationship operation...");
                if (success)  {     // Server reported SUCCESS
                    console.log("    server call was successful; it returned: ", server_payload);
                    this.status_message = `New relationship added`;
                    // Clear up the form
                    this.del_linked_from = -1;
                    this.del_linked_to = -1;
                    this.del_rel_name = "";
                }
                else  {             // Server reported FAILURE
                    this.error = true;
                    this.status_message = `FAILED deletion of relationship: ${error_message}`;
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;      // Make a note that the asynchronous operation has come to an end
            },



            // ---------------------------------------

            add_relationship()
            /* Initiate request to server to add a new relationship between specified Classes
             */
            {
                console.log(`Processing request to add the relationship "${this.add_linked_from} - ${this.add_rel_name} -> ${this.add_linked_to}"`);

                if (this.add_rel_name == "")  {
                    alert("Must enter a relationship name");
                    return;
                }
                if (this.add_linked_from == -1)  {
                    alert("Must enter a class name that the new link originates from");
                    return;
                }
                if (this.add_linked_to == -1)  {
                    alert("Must enter a class name that the new link goes to");
                    return;
                }


                // Send the request to the server, using a POST
                let url_server = "/BA/api/add_schema_relationship";
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
                ServerCommunication.contact_server_OLD(url_server,
                            {post_obj: post_obj,
                             callback_fn: this.finish_add_relationship});
            },

            finish_add_relationship(success, server_payload, error_message, custom_data)
            // Callback function to wrap up the action of add_relationship() upon getting a response from the server
            {
                console.log("Finalizing the add_relationship operation...");
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