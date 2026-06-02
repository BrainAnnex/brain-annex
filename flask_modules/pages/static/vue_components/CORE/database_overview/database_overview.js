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
                all_classes: this.all_class_names,

                show_schema_arr: Array(this.all_database_labels.length).fill(false),
                show_sample_arr: Array(this.all_database_labels.length).fill(false),
                item_metadata: {    class_name: "Recordset",
                                    class_handler:"recordsets",
                                    schema_code:"rs",
                                    entity_id:"fake"
                               },

                available_fields: []        // From the lookup of estimated fields for nodes with a specific database label
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



            /**
             * Invoked when the user click on an "Add to Schema" button
             */
            add_to_schema(class_name)
            {
                alert(`Adding Class "${class_name}" to Schema not yet fully implemented`);

                this.get_sample_properties(class_name);
            },



            /*
                ------------------   SERVER CALLS   ------------------
             */

            get_sample_properties(class_name)
            {
                console.log(`In sample_properties(): attempting to estimate the Properties of the Class '${class_name}'`);

                const url_server_api = `/BA/api/field-names-by-class/${class_name}`;

                console.log(`About to contact the server at ${url_server_api} .  GET object:`);
                console.log(data_obj);

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server(url_server_api,
                            {   method: "GET",
                                json_encode_send: false,
                                callback_fn: this.finish_get_sample_properties
                            });

                this.waiting = true;        // Entering a waiting-for-server mode
                this.error = false;         // Clear any error from the previous operation
                this.status_message = "";   // Clear any message from the previous operation
            }

            finish_get_sample_properties(success, server_payload, error_message, custom_data)
            /* Callback function to wrap up the action of get_sample_properties() upon getting a response from the server.
                    success:        boolean indicating whether the server call succeeded
                    server_payload: whatever the server returned (stripped of information about the success of the operation)
                    error_message:  a string only applicable in case of failure
                    custom_data:    whatever JavaScript structure, if any, was passed by the contact_server() call
            */
            {
                console.log("Finalizing the finish_get_sample_properties() operation...");

                if (success)  {     // Server reported SUCCESS
                    console.log("    server call was successful; it returned: ", server_payload);
                    this.status_message = `Operation completed`;
                    this.available_fields = server_payload;
                }
                else  {             // Server reported FAILURE
                    this.error = true;
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;      // Make a note that the asynchronous operation has come to an end
            }



        }  // METHODS

    }
); // end component