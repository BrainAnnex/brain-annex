/*  Vue component used by database_overview.htm
 */

Vue.component('vue-database-summary',
    {
        props: ['all_database_labels', 'all_class_names'],
        /*  all_database_labels
            all_class_names
         */

        template: `
            <div>	<!-- Outer container, serving as Vue-required template root  -->

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

                    <div v-if="show_schema_arr[index]" style="border: 1px solid gray; margin-bottom:10px">
                        <p v-if="(all_classes.includes(label))" style="font-size: 18px">
                            CLASS <span class='label-name'>{{label}}</span> FOUND
                        </p>

                        <p v-else style="font-size: 18px">
                            NO schema information found. <button>Add to Schema</button><br>
                            The Schema is a way to store information - such as descriptions and list of fields - about database entities.<br>
                            Use only for database entities that have well-defined prescribed structures; don't use
                            for database labels meant to index heterogeneous data
                        </p>
                    </div>

                    <div v-if="show_sample_arr[index]"
                         style="margin-bottom:30px; padding:10px; background-color: aliceblue"
                    >
                        Sample records (database nodes) with the label <span class='label-name'>{{label}}</span>:

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

        }  // METHODS

    }
); // end component