/*  EXPERIMENTAL Vue component to display and edit a tabular representation
    of a group of Content Items at type "r" (Record)
    MIT License.  Copyright (c) 2021-22 Julian A. West
 */

Vue.component('vue-plugin-table',
    {
        props: ['record_data_list', 'common_fields', 'common_schema_data'],
        /*  record_data_list:  EXAMPLE:
                                 [{"item_id":52, "pos":10, "schema_code":"r", class_name:"German Vocabulary",
                                  "German":"Tier", "English":"animal"}
                                 ]
                                 (if any item_id is -1, it means that it's a newly-created header, not yet registered with the server)

            common_fields:  A list of field names, in order - shared among all records in the table
                                 EXAMPLE: ["French", "English", "notes", "some extra field"]
            common_schema_data:  A list of field names, in order - shared among all records in the table
                                 EXAMPLE: ["French", "English", "notes"]

            THE REMAINING PROPS are just passed along, for the controls [CURRENTLY NOT IN USE]
            category_id:    The ID of the Category page where this table is displayed (used when creating new records)
            index:          The zero-based position on the page of the 1st Record on this table
            item_count:     The total number of Content Items (of all types) on the page
         */

        template: `
            <table class='r-main'>  <!-- Outer container, serving as Vue-required template root  -->
                <!--
                    Header row
                  -->
                <tr>
                    <th v-for="field_name in common_fields">
                        {{field_name}}
                    </th>
                </tr>

                <!--
                    Data row
                  -->
                <tr v-for="record in record_data_list" is="vue-plugin-single-record"
                    v-bind:key="record.item_id"

                    v-bind:record_data="record"
                    v-bind:field_list="common_fields"
                >
                </tr>

            </table>    <!-- End of outer Vue container -->
            `,


        data: function() {
            return {
                editing_mode: false
            }
        }, // data



        // ------------------------------   METHODS   ------------------------------
        methods: {
            foo()
            {

            }

        }  // METHODS

    }
); // end component