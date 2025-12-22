/*  "Record navigator" with recursive drill-down capabilities to follow links
    and explore neighbor nodes as sub-records.

    Currently used in the filter page.
 */

Vue.component('vue-record-navigator',
    {
        props: {
            /*  Array of objects, with one entry per "record" (data from one database node) */
            nodes_data: {
                required: true
            }
        },



        template: `
            <!-- Outer container, serving as Vue-required template root -->
            <div style="border:1px solid #DDD; padding:10px; background-color: #f4f4f4">

                <p v-if="recordset_array.length === 0" style="color: gray">
                    NO RECORDS
                </p>


                <!--  For each item in the current recordset -->
                <p v-for="(item, index) in recordset_array"
                            style="border: 1px solid #CCC; padding-bottom: 5px; padding-left: 3px; margin-bottom:2px; margin-top:3px;
                                   background-color: white"
                            v-bind:style="{'margin-left': item.controls.indent * 50 + 'px'}">


                    <!--  Eye icon, offering option to hide (delete from memory) the record  -->
                    <span style="color:#d0d0d0">{{item.controls.record_id}} </span>
                    <img src="/BA/pages/static/graphics/eye_16_173007.png"
                         @click="hide_record(item, index, true)" class="clickable-icon"
                         v-bind:title="'HIDE record (index ' + index + ')'"   alt="HIDE"
                    >

                    &nbsp;


                    <!-- If applicable, show the parentage of the record  (i.e. link name/direction to a record above) -->
                    <template v-if="item.controls.parent_record_id !== null">
                        <span v-if="item.controls.parent_dir == 'OUT'"
                            class="subrecord-out"
                            v-bind:title="'Neighbor of node ' + item.controls.parent_record_id + ' by the OUT-bound link \`' + item.controls.parent_link + '\`'"
                            style="display: inline-block; margin-right:10px">
                            <img src='/BA/pages/static/graphics/20_outbound_4619660.png'>
                            {{item.controls.parent_link}}
                        </span>

                        <span v-else
                            class="subrecord-in"
                            v-bind:title="'Neighbor of node ' + item.controls.parent_record_id + ' by the IN-bound link \`' + item.controls.parent_link + '\`'"
                            style="display: inline-block; margin-right:10px">
                            <img src='/BA/pages/static/graphics/20_inbound_4619661.png'>
                            {{item.controls.parent_link}}
                        </span>
                    </template>


                    <!-- Display the data record (all its fields, incl. "internal_id" and "node_labels")
                      -->

                    <!-- Part 1 of 2: the node LABELS receive special handling -->
                    <span  v-for="label in item.data.node_labels"  class="node-label">
                        {{label}}
                    </span>

                    <!-- Part 2 of 2: all the other fields, incl. internal_id -->
                    <template  v-if="key != 'node_labels'"  v-for="(val, key) in item.data">
                        <span style="color:grey; font-size:12px" class="monospace">{{key}}: </span>
                         \`<span style="background-color: rgb(251, 240, 240)">{{val}}</span>\` <span style="color:brown; font-weight: bold">|| </span>
                    </template>

                    &nbsp;


                    <!-- If the link-summary data for the record is hidden, show an arrow to expand the record and show its link summary... -->
                    <img  v-if="item.controls.expand==false"
                        src="/BA/pages/static/graphics/arrow_right_22_79650.png" title="Show LINKS" alt="Show LINKS"
                         @click="toggle_links(item, index)"
                         class="clickable-icon" style="background-color:black"
                    >

                    <!-- ...otherwise, if the link-summary data is to be shown, show it -->
                    <span v-else>

                        <template v-for="link in item.controls.links">  <!-- Show all the links (inbound and outbound) -->

                            <span v-if="link[1]=='IN'" @click="toggle_linked_records(item, index, link[0], 'IN', link[2])"
                                  class="clickable-icon relationship-in"
                                  v-bind:title="'Show/Hide ' + link[2] + ' IN-bound link(s) \`' + link[0] + '\`'"
                            >
                                <!-- Inbound link : show the number of links, an icon, and the link's name -->
                                {{ link[2] }}
                                <img src="/BA/pages/static/graphics/20_inbound_4619661.png" alt="Show/Hide IN-bound links">
                                {{ link[0] }}
                            </span>

                             <span v-else @click="toggle_linked_records(item, index, link[0], 'OUT', link[2])"
                                  class="clickable-icon relationship-out"
                                  v-bind:title="'Show/Hide ' + link[2] + ' OUT-bound link(s) \`' + link[0] + '\`'"
                             >
                                <!-- Outbound link : show the number of links, an icon, and the link's name -->
                                {{ link[2] }}
                                <img src="/BA/pages/static/graphics/20_outbound_4619660.png" alt="Show/Hide OUT-bound links">
                                {{ link[0] }}
                            </span>

                            &nbsp;
                        </template>


                        <!-- Arrow to shrink the record, to hide the links -->
                        <img src="/BA/pages/static/graphics/arrow_down_22_79479.png" title="Hide LINKS" alt="Hide LINKS"
                          @click="toggle_links(item, index)"
                          class="clickable-icon" style="background-color:black"
                        >
                    </span>

                </p>

            </div>  <!-- End of outer container -->
            `,



        // ----------------  DATA  -----------------
        data: function() {
            return {
                next_record_id: 0,      // Auto-increment to identify records shown on page

                recordset_array: [],
                                        // Array of objects, with one entry per record (database node)
                                        //
                                        //      EACH ENTRY is an object with 2 keys: "controls" and "data":
                                        //
                                        //      * "controls" is an object with the following keys:
                                        //                      "record_id" (int)
                                        //                      "parent_record_id" (int)
                                        //                      "parent_link" (str)
                                        //                      "parent_dir" (str: "IN" or "OUT")
                                        //                      "expand" (bool)
                                        //                      "indent" (int)
                                        //                      "links" (array of triples: name, "IN"/"OUT", count)
                                        //                      "pos" (int) : meant to hold TEMPORARY values
                                        //
                                        //      * "data" is an object containing all the field names and values
                                        //            returned from the database node
                                        //           (incl. the special fields "internal_id" and "node_labels")

                waiting: false,         // Whether any server request is still pending
                error: false,           // Whether the last server communication resulted in error
                status_message: ""      // Message for user about status of last operation upon server response (NOT for "waiting" status)
            }
        },



        // -----------------------  WATCH  ------------------------
        watch: {
            nodes_data()  {
                //console.log('The prop `nodes_data` has changed!');

                this.recordset_array = [];  // Clear all past records (TODO: maybe make this optional)

                for (let i = 0; i < this.nodes_data.length; i++)  {
                    let new_entry = {controls: {
                                                    record_id: this.next_record_id,

                                                    parent_record_id: null,
                                                    parent_link: null,
                                                    parent_dir: null,

                                                    expand: false,
                                                    indent: 0,
                                                    links: null
                                                },
                                     data: this.nodes_data[i]
                                     };
                    this.next_record_id += 1;
                    //console.log(`new_entry: ${new_entry.controls}, ${new_entry.data}`);
                    Vue.set(this.recordset_array, i, new_entry);
                }
            }
        },


        // ----------------  METHODS  -----------------
        methods: {

            toggle_links(record, record_index)
            /*  Show/Hide an inline summary of the available links from/to the given record.
                If hiding the summary, also hide all its descendant sub-records (but not the record itself)
             */
            {
                record.controls.expand = !record.controls.expand;   // Toggle the line-expansion status

                if (record.controls.expand)  {    // Enable showing a little inline summary of the available links
                    this.get_link_summary_from_server(record, record_index);
                    return;
                }

                // Hide all its descendant sub-records (but not the record itself)
                this.hide_record(record, record_index, false);
            },



            toggle_linked_records(record, index, rel_name, dir, n_links)
            /* Toggle the display of all the "sub-records" (database nodes)
               that have a relationship by the given name
               to the specified record

               :param record:   Object with the information about the database node of interest
               :param index:    Integer with the position of the record in the current listing
               :param rel_name: The name of the relationship to follow (for one hop)
               :param dir:      Either "IN" or "OUT"
               :param n_links:  Number of links to (possibly) fetch from the server
             */
            {
                // The given record will be referred to as "parent", because we'll be dealing
                // with its "children" (neighbor database nodes)
                const parent_record_id = record.controls.record_id;
                const parent_internal_id = record.data.internal_id;
                console.log(`In toggle_linked_records() - parent_record_id: ${parent_record_id} | parent_internal_id: ${parent_internal_id} | index: ${index} | rel_name: "${rel_name}" | dir: "${dir}"`);

                console.log(`    checking if immediate children by the relationship "${rel_name}" are present...`);
                var children = this.locate_children(record, index, rel_name, dir);


                // **** "HIDE" SCENARIO

                if (children.length > 0)  {
                    // Given existing sub-records from our link name, the toggle operation is taken to be a "HIDE"
                    //alert(`${children.length} link(s) already found.  No action taken`);
                    console.log(`${children.length} link(s) already found; the toggle operation will be a "HIDE"...`);
                    // Consider the children in reverse order (lowest one in the list, first),
                    // and hide each of them (along with their descendants, if applicable)
                    for (var child_n = children.length -1; child_n >= 0; child_n--)  {
                        // For each child record
                        var child_record = children[child_n];

                        var child_data = child_record.data;
                        var child_controls = child_record.controls;

                        var child_index = child_controls.pos;

                        this.hide_record(child_record, child_index, true);
                    }

                    return;     // We've hidden the child sub-records, and we're done!
                }


                // **** "SHOW" SCENARIO

                // Given no sub-records from our link name, the toggle operation is taken to be a "SHOW"
                console.log(`    No existing sub-records (children) found; the toggle operation will be a "SHOW"...`);

                if (n_links > 100)
                    alert(`Due to the high number of links (${n_links}), only 100 will be shown`);

                this.get_linked_records_from_server(record, rel_name, dir);
            },



            populate_subrecords(record, rel_name, dir, new_data_arr)
            /*  Update the overall array of database records (this.recordset_array),
                to also include records newly returned by the server.
                The new objects are regarded as sub-records of the given record - neighbor
                nodes by means of the specified relationship in the given direction - and
                are to be inserted below the record, with increasing indent; they also
                get assigned auto-incremented record ID's.

                :param record:       Object
                :param rel_name:     The name of the relationship to follow (for one hop)
                :param dir:          Either "IN" or "OUT"
                :param new_data_arr: Array of objects, each containing the data of a database node
             */
            {
                const parent_record_id = record.controls.record_id;
                const n_links = new_data_arr.length;

                for (let counter = 0; counter < n_links; counter++)  {
                    let new_entry = {controls: {
                                                    record_id: this.next_record_id,
                                                    expand: false,
                                                    indent: record.controls.indent + 1,

                                                    parent_record_id: parent_record_id,
                                                    parent_link: rel_name,
                                                    parent_dir: dir
                                                },
                                     data:
                                                new_data_arr[counter]
                                     };

                    this.next_record_id += 1;   // Advance the auto-increment value
                    console.log(`new_entry: record_id = ${new_entry.controls.record_id}`);
                    console.log(new_entry.data);

                    const i = this.locate_item(parent_record_id);

                    if (i == -1)
                        alert(`Unable to locate any item with a record_id of ${parent_record_id}`);
                    else  {
                        console.log(`Located parent record at index position ${i}`);
                        this.recordset_array.splice(i+1, 0, new_entry); // Insert the new entry just below its parent
                    }
                }
            },



            locate_item(record_id)
            /* Attempt to locate a record with the requested id, from the overall array of records.
               If found, return its index in the array; otherwise, return -1
             */
            {
                //console.log(`Attempting to locate the record with record_id '${record_id}'`);

                const number_items = this.recordset_array.length;

                for (var i = 0; i < number_items; i++) {
                    if (this.recordset_array[i].controls.record_id == record_id)
                        return i;          //  Found it
                }

                return -1;    // Didn't find it
            },



            hide_record(record, record_index, hide)
            /*  Recursively hide all the descendant of the specified record;
                If hide is true, also hide the record itself
             */
            {
                console.log(`hide_record() invoked for record with index=${record_index} and record_id=${record.controls.record_id}`);

                var children = this.locate_children(record, record_index);   // By any link name/direction
                if (children.length > 0)  {
                    console.log(`hide_record() : the record to hide has children; considering them first, in reverse order`);
                    // Consider the children in reverse order (lowest one in the list, first)
                    for (var child_n = children.length -1; child_n >= 0; child_n--)  {
                        // For each child record
                        var child_record = children[child_n];

                        var child_data = child_record.data;
                        var child_controls = child_record.controls;

                        var child_index = child_controls.pos;

                        console.log(`    considering the ${child_n}-th child (record_id=${child_id} at index pos ${child_index})`);
                        console.log(child_record);

                        var child_id = child_controls.record_id;

                        // Recursive call
                        this.hide_record(child_record, child_index, true);
                    }
                }

                if (hide)  {
                    // Delete 1 element from the specified index position
                    console.log(`Deleting record with record_id=${record.controls.record_id}, at index pos ${record_index}`);
                    this.recordset_array.splice(record_index, 1);
                }
            },


            locate_children(record, index, rel_name, dir)
            /* Given a record, and its index in the overall array of records,
               locate all its (immediate) children records - optionally requiring the given relationship.

               "Children" are defined as records below the given index position (i.e.,
               start the search just past the given index position in the overall array of records)
               that have the given record as their parent, optionally by means of the given relationship.
               One-hop relationships only.

               Return an array with all the child records, after saving their index position in their `controls` objects.

               :param record:   An object that is an element of the overall array of records this.recordset_array
               :param index:    An integer with the index of the above record in the overall array of records
               :param rel_name: [OPTIONAL] If not specified (null),
                                    then children records are not restricted to that particular relationship name
               :param dir:      [OPTIONAL] Either "IN" or "OUT"
             */
            {
                const reference_id = record.controls.record_id;
                const reference_indent = record.controls.indent;
                console.log(`In locate_children(): REFERENCE record_id: ${reference_id} | index: ${index} | indent: ${reference_indent}
                            | rel_name: "${rel_name}" | dir: "${dir}"`);

                let children = [];      // Building list of all the found child records

                // Start the search just past the given index position
                //      in `this.recordset_array` (the overall array of records)
                for (var pos = index+1;  pos < this.recordset_array.length;  pos++)  {
                    let record_under_consideration = this.recordset_array[pos];
                    let control_data = record_under_consideration.controls;
                    let parent_record_id = control_data.parent_record_id;
                    let indent = control_data.indent;

                    console.log(`    examining record in position ${pos}; it has indent ${indent}, id ${control_data.record_id},
                                        parent id ${parent_record_id} and parent_link ${control_data.parent_link}`);

                    if (indent <= reference_indent)
                        break;      // Quit as soon as the indent is <= that of the reference record


                    if (parent_record_id == reference_id)
                        // Found a match in the parentage; if a rel_name was specified, also match for that
                        if  ((rel_name == null)  || (control_data.parent_link == rel_name  &&  control_data.parent_dir == dir))  {
                            control_data.pos = pos;     // Save the array index position with the child's control data

                            console.log(`      ^--- found a child!  Pushing "record_under_consideration"`);
                            children.push(record_under_consideration);
                        }
                }

                console.log(`    Finished looping.  Number of children: ${children.length}`);

                if (children.length > 0)  {
                    //console.log(`    First child:`);
                    //console.log(children[0]);       // Show the 1st (0-th child), if present

                    // Show the record id's of all the children
                    let children_ids = [];
                    for (let i=0 ;  i < children.length;  ++i)
                        children_ids.push(children[i].controls.record_id);

                    console.log(`    Id's of all children: [${children_ids}]`);
                }


                //console.log("    Returning from locate_children()");

                return children;
            },




            /*
                --------------   SERVER CALLS   ----------------------------------------------------------------
             */

            get_link_summary_from_server(record, record_index)
            /*  Invoked when the user clicks to expand the "Show Links" region.
                Initiate request to server, to get the list of the names/counts
                of all the Inbound and Outbound links from the given record (node)
                Note: record_index is used to force Vue to detect the change
                      within an element of the array this.recordset_array
             */
            {
                console.log(`Getting the links summary info for record id ${record.controls.record_id}`);

                const internal_id = record.data.internal_id;
                if (internal_id == null)  {
                    alert("get_link_summary_from_server(): the record lacks an internal database ID.  Its links cannot be expanded");
                    return;
                }
                const url_server_api = `/BA/api/get-link-summary-by-id/${internal_id}`;

                console.log(`About to contact the server at "${url_server_api}"`);

                // Initiate asynchronous contact with the server
                this.waiting = true;
                this.error = false;         // Clear any error from the previous operation
                this.status_message = "";

                ServerCommunication.contact_server(url_server_api,
                        {method: "GET",
                        callback_fn: this.finish_get_link_summary_from_server,
                        custom_data: [record, record_index]
                        });
            },

            finish_get_link_summary_from_server(success, server_payload, error_message, custom_data)
            /* Callback function to wrap up the action of get_link_summary_from_server() upon getting a response from the server.

                success:        boolean indicating whether the server call succeeded
                server_payload: whatever the server returned (stripped of information about the success of the operation)
                error_message:  a string only applicable in case of failure
                custom_data:    whatever JavaScript pass-thru value, if any, was passed by the contact_server() call
            */
            {
                console.log("Finalizing the get_link_summary_from_server() operation...");
                console.log(`Custom pass-thru data:`);
                console.log(custom_data);
                if (success)  {     // Server reported SUCCESS
                    console.log("    server call was successful; it returned: ", server_payload);
                    this.status_message = `Operation completed`;
                    var record = custom_data[0];                // The record object to which the retrieved link into applies
                    let record_index = custom_data[1];          // The position of the above record object in an array
                    record.controls.links = server_payload;     // Populate the record with the retrieved data.  TODO: NOT Vue reactive!!!
                    Vue.set(this.recordset_array, record_index, record);    // This replacement will force Vue reactivity
                }
                else  {             // Server reported FAILURE
                    this.error = true;
                    this.status_message = `FAILED operation: ${error_message}`;
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;      // Make a note that the asynchronous operation has come to an end
            },



            get_linked_records_from_server(record, rel_name, dir)
            /* Initiate request to server, to get the list of the properties
               of the data nodes linked to the specified node (record),
               by the relationship named by rel_name, in the direction requested by dir

               :param record:   Object with the record of interest
               :param rel_name: The name of the relationship to follow (for one hop)
               :param dir:      Either "IN" or "OUT"
             */
            {
                const internal_id = record.data.internal_id;

                console.log(`get_linked_records_from_server(): Getting the properties of data nodes linked to record with internal dbase ID ${internal_id} by means of the ${dir}-bound relationship '${rel_name}'`);

                const url_server_api = "/BA/api/get_records_by_link";
                const post_obj = {internal_id: internal_id, rel_name: rel_name, dir: dir};
                const my_var = [record, rel_name, dir];        // Pass-thru parameters

                console.log(`About to contact the server at "${url_server_api}" .  POST object:`);
                console.log(post_obj);

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server(url_server_api,
                            {method: "POST",
                             data_obj: post_obj,
                             json_encode_send: false,
                             callback_fn: this.finish_get_linked_records_from_server,
                             custom_data: my_var
                            });
            },

            finish_get_linked_records_from_server(success, server_payload, error_message, custom_data)
            /* Callback function to wrap up the action of get_data_from_server() upon getting a response from the server.

                success:        Boolean indicating whether the server call succeeded
                server_payload: Whatever the server returned (stripped of information about the success of the operation)
                                    The server returns a JSON value.
                error_message:  A string only applicable in case of failure
                custom_data:    Whatever JavaScript pass-thru value, if any, was passed by the contact_server() call
            */
            {
                console.log("Finalizing the get_linked_records_from_server() operation...");
                console.log(`Custom pass-thru data:`);
                console.log(custom_data)
                if (success)  {     // Server reported SUCCESS
                    console.log("    server call was successful; it returned: ", server_payload);
                    /*  EXAMPLE of server_payload:
                            [
                                {uri: "100", internal_id: 2, name: "mushrooms pie", eval: "+"},
                                {uri: "180", internal_id: 9, name: "Margherita pie", eval: "OK"}
                            ]
                    */
                    this.status_message = `Operation completed`;

                    const record =  custom_data[0];
                    const rel_name = custom_data[1];
                    const dir = custom_data[2];
                    this.populate_subrecords(record, rel_name, dir, server_payload);
                }
                else  {             // Server reported FAILURE
                    this.error = true;
                    this.status_message = `FAILED operation: ${error_message}`;
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;      // Make a note that the asynchronous operation has come to an end

            }  // finish_get_linked_records_from_server


        }  // METHODS

    }
); // end component