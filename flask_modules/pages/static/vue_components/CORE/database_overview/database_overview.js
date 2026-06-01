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



            /**
             * Invoked when the user click on an "Add to Schema" button
             */
            add_to_schema(class_name)
            {
                alert(`Adding Class "${class_name}" to Schema not yet implemented`);
            },



            /*
                ------------------   SERVER CALLS   ------------------
             */

            sample_properties(class_name)
            {
                console.log(`In sample_properties(): attempting to estimate the Properties of the Class '${lass_name}'`);

                const url_server_api = "/BA/api/TBA";

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

            }




        }  // METHODS

    }
); // end component