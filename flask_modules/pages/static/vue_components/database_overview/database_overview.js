/*  Vue component used by database_overview.htm
 */

Vue.component('vue-database-summary',
    {
        props: ['all_database_labels'],

        template: `
            <div>	<!-- Outer container, serving as Vue-required template root  -->

                <h2>{{all_labels.length}} <i>labels</i> found in graph database:</h2>

                <vue-record-cluster
                    v-bind:item_fields="{filter_label: 'BA', n_group: 3}"
                    v-bind:item_metadata="item_metadata"
                    v-bind:edit_mode="false"
                    v-bind:category_id="0"
                    v-bind:index="0"
                    v-bind:item_count="0"
                    v-bind:schema_data="['class', 'order_by', 'clause', 'n_group', 'caption']"
                >
                </vue-record-cluster>

                <div v-for="(label, index) in all_labels" >

                    <span style="color: gray">{{String(index).padStart(2, '0')}} </span> *

                    <img @click="toggle_schema(index)" class="clickable-icon"
                                src="/BA/pages/static/graphics/info_16.png"
                                title="Show info" alt="Show info">
                    &nbsp;
                    <img @click="toggle_sample(index)" class="clickable-icon"
                                src="/BA/pages/static/graphics/tabular_16_9040670.png"
                                title="Show sample node (record)" alt="Show sample node (record)">

                    <span style="font-size: 14px">{{label}}</span>
                    <br>

                    <div v-if="show_schema_arr[index]" style="border: 1px solid gray; margin-bottom:10px">
                        Schema info here!
                    </div>

                    <div v-if="show_sample_arr[index]" style="border: 1px solid gray; margin-bottom:10px">
                        Sample info here!  Plugin below:

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

                show_schema_arr: Array(this.all_database_labels.length).fill(false),
                show_sample_arr: Array(this.all_database_labels.length).fill(false),
                item_metadata: {    class_name: "Recordset",
                                    class_handler:"recordsets",
                                    pos:0,
                                    schema_code:"rs",
                                    entity_id:"fake"
                               }
            }
        }, // data




        // ------------------------------------   METHODS   ------------------------------------
        methods: {
            toggle_schema(index)
            {
                console.log(index);
                Vue.set(this.show_schema_arr, index, !this.show_schema_arr[index]);
            },

            toggle_sample(index)
            {
                console.log(index);
                Vue.set(this.show_sample_arr, index, !this.show_sample_arr[index]);
            },

        }  // METHODS

    }
); // end component