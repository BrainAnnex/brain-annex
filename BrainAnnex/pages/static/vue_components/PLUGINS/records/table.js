/*  Vue component to display and edit a tabular representation
    of a group of Content Items all of type "r" (Record) and all from the same Schema Class
 */

Vue.component('vue-plugin-table',
    {
        props: ['record_data_list', 'common_fields'],
        /*  record_data_list:  EXAMPLE:
                                 [{"uri":52, "pos":10, "schema_code":"r", class_name:"German Vocabulary",
                                  "German":"Tier", "English":"animal"}
                                 ]
                                 (if any uri is -1, it means that it's a newly-created header, not yet registered with the server)

            common_fields:      A list of field names, in order - shared (and visible) among all records in the table
                                    EXAMPLE: ["French", "English", "notes", "some extra field"]

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
                    v-bind:key="record.uri"

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

        }  // METHODS

    }
); // end component