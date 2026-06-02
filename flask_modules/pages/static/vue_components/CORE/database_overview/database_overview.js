/*  Vue components used by database_overview.htm
 */

Vue.component('vue-database-overview',
    {
        props: ['all_database_labels', 'all_class_names'],
        /*  all_database_labels
            all_class_names
         */

        template: `
            <div class="database-overview">	<!-- Outer container, serving as Vue-required template root  -->

                <h2>{{all_labels.length}} <i>labels</i> found in graph database:</h2>

                <div v-for="(label, index) in all_labels" >

                    <span style="color: gray">{{String(index).padStart(2, '0')}} </span> *

                    <img @click="toggle_schema(index)" class="clickable-icon"
                                src="/BA/pages/static/graphics/info_16.png"
                                title="Show info" alt="Show info">
                    &nbsp;
                    <img @click="toggle_sample(index)" class="clickable-icon"
                                src="/BA/pages/static/graphics/tabular_16_9040670.png"
                                title="Show sample node (record)" alt="Show sample node (record)">

                    <span style="font-size: 14px">
                        {{label}}
                    </span>

                    <br>

                    <div v-if="show_schema_arr[index]" class="schema">
                        <p v-if="(all_classes.includes(label))" style="font-size: 18px">
                          <!-- Vue component -->
                            <vue-schema-manager
                                v-bind:class_name="label"
                            >
                            </vue-schema-manager>

                        </p>

                        <p v-else class="not-found">
                            NO schema information found for Class "{{label}}" &nbsp;
                            <button @click=add_to_schema(label)>Add to Schema</button>
                            <br>
                            The Schema is a way to store information - such as descriptions and list of fields - about database entities.<br>
                            CAUTION: Use only for database entities that have well-defined prescribed structures; don't use
                            for database labels meant to index heterogeneous data
                        </p>
                    </div>


                    <div v-if="show_sample_arr[index]"
                         style="margin-bottom:30px; padding:10px; background-color: aliceblue"
                    >
                        Sample records (database nodes) with the label <span class='label-name'>{{label}}</span>:

                        <!-- Vue component -->
                        <vue-record-cluster
                            v-bind:item_fields="{filter_label: label, n_group: 3}"
                            v-bind:item_metadata="item_metadata"
                            v-bind:edit_mode="false"
                            v-bind:category_id="0"
                            v-bind:index="0"
                            v-bind:item_count="0"
                            v-bind:schema_data="['class', 'order_by', 'clause', 'n_group', 'caption']"
                        >
                        </vue-record-cluster>

                    </div>

                </div>

            </div>		<!-- End of outer container -->
            `,



        // ------------------------------------   DATA   ------------------------------------
        data: function() {
            return {
                all_labels: this.all_database_labels,
                all_classes: this.all_class_names,      // Array of all the Schema Classes in the dbase

                show_schema_arr: Array(this.all_database_labels.length).fill(false),
                show_sample_arr: Array(this.all_database_labels.length).fill(false),
                item_metadata: {    class_name: "Recordset",
                                    class_handler:"recordsets",
                                    schema_code:"rs",
                                    entity_id:"fake"
                               }
            }
        }, // data




        // ------------------------------------   METHODS   ------------------------------------
        methods: {
            /**
             * Invoked when the user click to toggle the display of the Schema information
             */
            toggle_schema(index)
            {
                //console.log(index);
                Vue.set(this.show_schema_arr, index, !this.show_schema_arr[index]);
            },


            /**
             * Invoked when the user click to toggle the display of sample records
             */
            toggle_sample(index)
            {
                //console.log(index);
                Vue.set(this.show_sample_arr, index, !this.show_sample_arr[index]);
            },




            /*
                ------------------   SERVER CALLS   ------------------
             */


            /**
             * Invoked when the user click on an "Add to Schema" button
             */
            add_to_schema(label)
            {
                alert(`Adding Class "${label}" to the database Schema`);

                console.log(`In add_to_schema(): attempting to add Class '${label}' to the Schema`);

                const url_server_api = `/BA/api/create-schema-from-data`;

                const post_data = {'label': label};

                console.log(`In add_to_schema(): about to contact the server at "${url_server_api}" .  POST data:`);
                console.log(post_data);

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server(url_server_api,
                            {   method: "POST",
                                data_obj: post_data,
                                json_encode_send: true,
                                callback_fn: this.finish_add_to_schema,
                                custom_data: label
                            });

                this.waiting = true;        // Entering a waiting-for-server mode
                this.error = false;         // Clear any error from the previous operation
                this.status_message = "";   // Clear any message from the previous operation
            },

            /** Callback function to wrap up the action of add_to_schema() upon getting a response from the server.
             *
             * @param {bool} success - Boolean indicating whether the server call succeeded
             * @param server_payload - Whatever the server returned (stripped of information about the success of the operation)
             * @param {string} error_message - Only applicable in case of failure
             * @param custom_data            - Whatever JavaScript pass-thru value, if any, was passed by the contact_server() call
             */
            finish_add_to_schema(success, server_payload, error_message, custom_data)
            {
                console.log("Finalizing the finish_add_to_schema() operation...");
                console.log(`Custom pass-thru data:`);
                console.log(custom_data);               // This contains the label for which a Schema Class was created

                if (success)  {     // Server reported SUCCESS
                    console.log("    server call was successful; it returned: ", server_payload);
                    this.status_message = `Operation completed`;
                    this.all_classes.push(custom_data);     // We now have a new Class available
                }
                else  {             // Server reported FAILURE
                    this.error = true;
                    this.status_message = `FAILED operation: ${error_message}`;
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;      // Make a note that the asynchronous operation has come to an end
            }


        }  // METHODS

    }
); // end component