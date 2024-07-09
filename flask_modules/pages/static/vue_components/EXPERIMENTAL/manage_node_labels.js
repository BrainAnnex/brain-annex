/* Vue-related code.  This must appear AFTER the Vue-containing element
 */

const bus = new Vue();


Vue.component('vue-show-node-labels',
    {
        props: ['my_labels', 'wakeup'],

        template: `
            <div class="content-block">
            <div class="content-block-title">Component 'vue-show-node-labels'</div>
            <h2>{{all_labels.length}} <i>labels</i> found in Neo4j database:</h2>
            <ul>
                <li v-for="label in all_labels" >
                    {{label}}
                </li>
            </ul>
            </div>
            `,

        data: function() {
            return {
                all_labels: this.my_labels
            }
        },

        created() {         // Register, at component creation, to receive refresh events
            bus.$on("refresh-needed" , () => {this.refresh()} );    // We're using a nameless function as a 2nd arg
        },

        // ------------- METHODS --------------
        methods: {
            refresh() {
                //alert("show-node-labels: Caught 'refresh-needed' event in bus. Now processing the request");
                console.log("show-node-labels: Caught 'refresh-needed' event in bus. Now processing the request");

                // Prepare a URL to communicate with the server's endpoint
                url_server = "/api/retrieve_labels";

                ServerCommunication.contact_server(url_server, {callback_fn: this.finish_refresh});
            }, // refresh


            finish_refresh(success, server_payload, error_message, index)
            // Callback function to wrap up the action of refresh() upon getting a response from the server
            {
                console.log("Finalizing the refresh operation...");
                if (success)  {     // Server reported SUCCESS
                    console.log("show-node-labels: Successful retrieval of node labels from database");
                    this.all_labels = server_payload.labels;
                    //this.$parent.outdated = false;
                    //this.stale = false;
                }
                else  {             // Server reported FAILURE
                    alert("show-node-labels: Failed retrieval");
                }
                //this.waiting_mode = false;

            } // finish_refresh



        }

    }

);  // end component 'vue-show-node-labels'



///////////////////////////////////////////////////////////////////////////////////////////////////////

Vue.component('vue-add-new-record',
    {
        template: `
            <div class="content-block">
            <div class="content-block-title">Component 'vue-add-new-record'</div>
            <table style="margin-top:10px">
            <tr><th>Label</th><td><input type='text' v-model="new_label_value" placeholder="Specify label"></td></tr>
            </table>
            <br>
            <button @click="add_node">Add new empty node with the above label</button>
            <span class='status-subdue'>{{status}}</span>
            </div>`,

        data: function() {
            return {
                new_label_value: "",    // Linked to the value in the input box
                status: "",             // An explanation about the result of the operation
                error_indicator: false, // Will get toggled to true in case an error occurs
                waiting_mode: false     // Gets transiently changed to true during the execution of the operation
            }
        },

        // ------------- METHODS --------------
        methods: {
            add_node: function () {
                //alert("In add_node. New label to add : `" + this.new_label_value + "`");
                console.log("In add_node. New label to add : `" + this.new_label_value + "`");

                this.waiting_mode = true;
                this.status = `Adding node with label "${this.new_label_value}"...`;

                // Prepare a URL to communicate with the server's endpoint
                url_server = "/api/add_label/" + encodeURIComponent(this.new_label_value);

                ServerCommunication.contact_server(url_server, {callback_fn: this.finish_add_node});
            }, // add_node


            finish_add_node(success, server_payload, error_message, index)
            // Callback function to wrap up the action of add_node() upon getting a response from the server
            {
                console.log("Finalizing the get_note operation...");
                if (success)  {     // Server reported SUCCESS
                    this.status = "added successfully";
                    // Clear the value in the checkbox
                    this.new_label_value = "";

                    // Inform the parent (root) component about the updated data (so that other components may be informed)
                    //alert("New label added successfully.  Sending signal to parent (root) component that a data refresh is needed");
                    //console.log("New label added successfully.  Sending signal to parent (root) component that a data refresh is needed");
                    //this.$emit('data-changed');       // Send signal to parent
                    //this.$parent.outdated = true;     // Less-modular alternate approach, directly modifying data on the parent

                    console.log("New label added successfully.  Sending signal on signal bus that a data refresh is needed");
                    bus.$emit('refresh-needed');
                }
                else  {             // Server reported FAILURE
                    this.status = "FAILED UPDATE";
                    this.error_indicator = true;
                }
                this.waiting_mode = false;

            } // finish_add_node

        }
    }

);  // end component 'vue-add-new-record'

///////////////////////////////////////////////////////////////////////////////////////////////////////


Vue.component('vue-pulldown-menu',
    {
        props: ['labels_from_flask'],

        template: `
            <div class="content-block">
            <div class="content-block-title">Component 'vue-pulldown-menu'</div>
            <br>
            <span style="font-weight:bold">Choose one of the following {{all_labels.length}} existing Neo4j labels: </span>
            <select>
                <option value='0'>[SELECT]</option>
                <option v-for="label in all_labels">{{label}}</option>
            </select>
            <br><br>
            </div>  <!-- End "content-block" -->
            `,

        data: function() {
            return {
                all_labels: this.labels_from_flask
            }
        },

        created() {     // Register, at component creation, to receive refresh events
            bus.$on("refresh-needed" , () => {this.refresh()} );    // We're using a nameless function as a 2nd arg
        },


        // ------------- METHODS --------------
        methods: {
            refresh()  {
                 console.log("pulldown-menu: Caught 'refresh-needed' event in bus. Now processing the request");

                // Prepare a URL to communicate with the server's endpoint
                url_server = "/api/retrieve_labels";

                ServerCommunication.contact_server(url_server, {callback_fn: this.finish_refresh});
            }, //  refresh


            finish_refresh(success, server_payload, error_message, index)
            // Callback function to wrap up the action of refresh() upon getting a response from the server
            {
                console.log("Finalizing the get_note operation...");
                if (success)  {     // Server reported SUCCESS
                    //this.status = "added successfully";
                    // Inform the other components about the updated data
                    console.log("pulldown-menu: Successful retrieval of node labels from database");
                    this.all_labels = server_payload.labels;
                    //this.$parent.outdated = false;
                    //this.stale = false;
                }
                else  {             // Server reported FAILURE
                    alert("pulldown-menu: Failed retrieval");
                }
                //this.waiting_mode = false;

            } // finish_refresh

        } // end METHODS

    }

);  // end component 'vue-pulldown-menus'



///////////////////////////////////////////////////////////////////////////////////////////////////////



// Instantiation must come after the component definition
new Vue({
    el: '#vue-root-1',

    data: {
    },

    methods : {
    }
});