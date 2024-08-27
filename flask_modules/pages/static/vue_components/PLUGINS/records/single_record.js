/*  Vue component to display and edit a SINGLE table row of data (NOT headers)
    from a Content Item at type "r" (Record).
    Table headers, and <table> tag, are handled by the parent component, in table.js

    Record edits are enabled by double-clicking on the row.

    At present, no new fields (from the Schema) can be added with this editor;
    however, fields can be eliminated by blanking them out (the Vue root component will handle
    resulting changes in the record groupings.)
 */

Vue.component('vue-plugin-single-record',
    {
        props: ['record_data', 'field_list'],
        /*  record_data:    EXAMPLE:
                            {"uri":"52", "pos":10, "schema_code":"r",
                             class_name:"German Vocabulary", <-- NOT CURRENTLY BEING PASSED
                             "German":"Tier", "English":"animal"}

            field_list:     A list of field names being shown, in order.
                            EXAMPLE: ["French", "English", "notes"]
          */

        template: `
            <tr @dblclick="detect_double_click">    <!-- Outer container, serving as Vue-required template root  -->
            <!--
                Row of data
            -->

                <td v-for="key in field_list">
                    <!-- Display SPAN or INPUT elements, depending on the editing mode -->
                    <span v-if="!editing_mode" v-html="render_cell(record_current[key])"></span>
                    <input v-if="editing_mode" type="text" size="25" v-model="record_current[key]">
                </td>

                <td v-if="editing_mode">
                    <button @click="save">SAVE</button>
                    <a @click.prevent="cancel_edit" href="#" style="margin-left:15px">Cancel</a>
                </td>

                <!-- Status info -->
                <td v-if="waiting" class="waiting">
                    Saving...
                </td>
                <td v-if="status_message">
                    <span v-bind:class="{'error-message': error, 'status-message': !error }">{{status_message}}</span>
                </td>

            </tr>
            `,


        data: function() {
            return {
                editing_mode: false,

                /*
                    "PROP" DATA PASSED BY THE PARENT COMPONENT (NOT copied to component variables):
                        record_data:        The FULL data passed by the parent component

                    COMPONENT VARIABLES:
                        record_current:     Object with the values bound to the editing fields,
                                            initially cloned from (part of) the "prop" data;
                                            it'll change in the course of the edit-in-progress

                        record_pre_edit:    Object with pre-edit data,
                                            initially cloned from (part of) the "prop" data;
                                            used to restore the data in case of an edit Cancel or failed save
                 */

                record_current: this.clone_and_standardize(this.record_data),
                record_pre_edit: this.clone_and_standardize(this.record_data),
                // Scrub some data, so that it won't show up in the tabular format
                // NOTE: clone_and_standardize() gets called twice

                waiting: false,         // Whether any server request is still pending
                error: false,           // Whether the last server communication resulted in error
                status_message: ""      // Message for user about status of last operation upon server response (NOT for "waiting" status)
            }
        }, // data



        // ------------------------------   METHODS   ------------------------------
        methods: {
            detect_double_click()
            // Enter the editing mode when a double-click is detected
            {
                //alert("Double click detected ");
                this.editing_mode = true;
            },



            cancel_edit()
            /* Invoked when the user cancels the edit-in-progress, or when the save operation fails.
               Revert any changes, and exit the edit mode
             */
            {
                // Restore the data to how it was prior to the aborted changes
                this.record_current = Object.assign({}, this.record_pre_edit);  // Clone from record_pre_edit
                
                this.editing_mode = false;      // Exit the editing mode
            },



            save()
            // Invoked when the user asks to save the edit-in-progress
            {
                // Send the request to the server, using a POST
                const url_server_api = "/BA/api/update_content_item";

                let post_obj = {schema_code: this.record_data.schema_code,
                                uri: this.record_data.uri,
                                class_name: "Records"
                                };
                // Go over each key (field name); note that keys that aren't field names were previously eliminated
                for (key in this.record_current) {
                    if ( (this.record_current[key] != "")  ||  (key in this.record_pre_edit) )
                        // Non-blank values always lead to updates; blanks, only if the field was originally present
                        post_obj[key] = this.record_current[key];
                }

                console.log(`About to contact the server at ${url_server_api} .  POST object:`);
                console.log(post_obj);

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server(url_server_api,
                            {post_obj: post_obj,
                             callback_fn: this.finish_save
                            });

                this.waiting = true;        // Entering a waiting-for-server mode
                this.error = false;         // Clear any error from the previous operation
                this.status_message = "";   // Clear any message from the previous operation

                this.editing_mode = false;  // Exit the editing mode
            },

            finish_save(success, server_payload, error_message)
            // Callback function to wrap up the action of save() upon getting a response from the server
            {
                console.log("Finalizing the save() operation...");

                if (success)  {     // Server reported SUCCESS
                    console.log("    server call was successful; it returned: ", server_payload);
                    this.status_message = `Successful edit`;

                    // Synchronize the accepted baseline data to the current one
                    this.record_pre_edit = Object.assign({}, this.record_current);  // Clone

                    this.editing_mode = false;      // Exit the editing mode

                    // Inform the ancestral root component of the new state of the data
                    console.log("'vue-plugin-single-record' component sending 'updated-item' signal to its parent");
                    let signal_data = Object.assign({}, this.record_current);    // Clone the object
                    // We'll be passing all the edited values, plus the field "uri" and "schema_code" to identify the record
                    signal_data.uri = this.record_data.uri;
                    signal_data.schema_code = "r";
                    this.$emit('updated-item', signal_data);
                }

                else  {             // Server reported FAILURE
                    this.error = true;
                    this.status_message = `FAILED edit`;
                    this.cancel_edit();     // Restore the data to how it was prior to the failed changes
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;      // Make a note that the asynchronous operation has come to an end

            }, // finish_save



            clone_and_standardize(obj)
            // Clone first; then remove some keys that shouldn't get shown nor edited
            {
                clone_obj = Object.assign({}, obj);     // Clone the object

                // Scrub some data, so that it won't be passed to the server during edits.
                // In this Vue component, this scrubbing is NOT needed for the UI display, because
                // we're currently only dealing with a FIXED set of fields, as passed by the props
                delete clone_obj.uri;           // A protected field; TODO: specify that in the Schema
                delete clone_obj.schema_code;   // A protected field; TODO: specify that in the Schema
                delete clone_obj.class_name;    // Not part of the record; TODO: maybe pass as separate prop
                delete clone_obj.pos;           // TODO: this might be getting phased out

                return clone_obj;
            },



            render_cell(cell_data)
            /*  If the passed argument is a string that appears to be a URL, convert it into a string with HTML code
                for a hyperlink that opens in a new window;
                if the URL is very long, show it in abbreviated form in the hyperlink text.
                In all other cases, just return the argument.

                Note: this function is also found in records.js and documents.js
             */
            {
                const max_url_len = 35;     // For text to show, NOT counting the protocol part (such as "https://")

                if (typeof cell_data != "string")
                     return cell_data;

                let dest_name = "";         // Name of the destination of the link, if applicable

                if (typeof cell_data != "string")  {
                    //console.log(`Argument passed to render_cell() is not a string.  Value passed: ${cell_data}`);
                    return cell_data;
                }

                // Do a simple-minded check as to whether the cell content appear to be a hyperlink
                if (cell_data.substring(0, 8) == "https://")
                    dest_name = cell_data.substring(8);
                else if (cell_data.substring(0, 7) == "http://")
                    dest_name = cell_data.substring(7);

                if (dest_name != "")  {     // If the cell data was determined to be a URL
                    if (dest_name.length > max_url_len)
                        dest_name = dest_name.substring(0, max_url_len) + "...";    // Display long links in abbreviated form

                    return `<a href='${cell_data}' target='_blank' style='font-size:10px'>${dest_name}<a>`;
                }
                else
                    return cell_data;
            }

        }  // METHODS

    }
); // end component