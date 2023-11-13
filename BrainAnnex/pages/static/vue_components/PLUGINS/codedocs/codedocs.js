/*  Vue component to display and edit Content Items of type "cd" (Code Documentation)
 */

Vue.component('vue-plugin-cd',
    {
        props: ['item_data', 'allow_editing', 'category_id', 'index', 'item_count'],
        /*  index:          the zero-based position of the Record on the page
            allow_editing:  A boolean indicating whether in editing mode
            item_count:     the total number of Content Items (of all types) on the page
         */

        template: `
            <div>	<!-- Outer container box, serving as Vue-required template root  -->

            <table class='cd-main'>
            <!-- Header line  -->
            <tr>
            <th>name</th>
            <th>arguments</th>
            <th>returns</th>
            </tr>

            <!-- Lines with data  -->
            <tr>
            <td class='cd-fun-name'>
                <!-- Display SPAN or INPUT elements, depending on the editing status -->
                <span v-if="!editing_mode">{{ current_data.name }}</span>
                <input v-if="editing_mode" type="text" size="25" v-model="current_data.name">
            </td>
            <td>
                <span v-if="!editing_mode">{{ current_data.args }}</span>
                <input v-if="editing_mode" type="text" size="25" v-model="current_data.args">
            </td>
            <td>
                <span v-if="!editing_mode">{{ current_data.return }}</span>
                <input v-if="editing_mode" type="text" size="25" v-model="current_data.return">
            </td>
            </tr>

            <tr>
            <td colspan=3 class='cd-description'>
                <pre v-if="!editing_mode" v-html="current_data.description"></pre>
                <textarea v-if="editing_mode" type="text" v-model="current_data.description" rows="12" cols="75"></textarea>
            </td>
            </tr>

            <tr v-if="editing_mode">    <!-- Extra table row with SAVE/Cancel controls -->
            <td colspan=3>
                <button @click="save()">SAVE</button>
                <a @click.prevent="cancel_edit()" href="#" style="margin-left:15px">Cancel</a>
                <span v-if="waiting_mode" style="margin-left:15px">saving...</span>
            </td>
            </tr>

            </table>
            <span v-if="status!='' && !editing_mode">Status : {{status}}</span>

            <!--  STANDARD CONTROLS
                  (signals from them get relayed to the parent of this component, but some get handled here)
                  Intercept the following signal from child component:
                        v-on:edit-content-item
            -->
            <vue-controls v-bind:allow_editing="allow_editing"  v-bind:index="index"  v-bind:item_count="item_count"
                          v-on="$listeners"
                          v-on:edit-content-item="edit_content_item(item_data)">
            </vue-controls>

            \n</div>\n		<!-- End of outer container box -->
            `,


        data: function() {
            return {
                editing_mode: (this.item_data.uri == -1 ? true : false),    // -1 means "new Item"
                /*
                fun_name: this.item_data.fun,
                fun_args: this.item_data.args,
                fun_return: this.item_data.return,
                fun_description: this.item_data.body,
                */

                // This object contains the values bound to the editing fields, cloned from the prop data;
                //      it'll change in the course of the edit-in-progress
                current_data: this.clone_and_standardize(this.item_data),

                // Clone, used to restore the data in case of an edit Cancel or failed save
                original_data: Object.assign({}, this.item_data),

                waiting_mode: false,
                status: "",
                error_indicator: false
            }
        }, // data


        // ------------------------------   METHODS   ------------------------------
        methods: {

            clone_and_standardize(obj)
            {
                clone_obj = Object.assign({}, obj);

                /*
                // TODO: maybe un-necessary!
                if (!('name' in clone_obj))
                    clone_obj.name = "";

                if (!('args' in clone_obj))
                    clone_obj.args = "";

                if (!('return' in clone_obj))
                    clone_obj.return = "";

                if (!('description' in clone_obj))
                    clone_obj.description = "";
                */

                return clone_obj;
            },



            edit_content_item(item)
            {
                console.log(`Codecods component received event to edit content item of type '${item.schema_code}' , id ${item.uri}`);
                this.editing_mode = true;
            },


            save()
            {
                // Start the body of the POST to send to the server
                post_body = "schema_code=" + this.current_data.schema_code;

                if (this.item_data.uri == -1)  {     // The -1 is a convention indicating a new Content Item to create
                    // Needed for NEW CodeDocumentation items
                    post_body += "&category_id=" + this.category_id;
                    const insert_after = this.item_data.insert_after;       // ID of Content Item to insert after, or keyword "TOP" or "BOTTOM"
                    post_body += "&insert_after=" + insert_after;

                    url_server = `/BA/api/add_item_to_category`;     // URL to communicate with the server's endpoint
                }
                else {   // Update an existing Content Item
                    post_body += "&uri=" + this.item_data.uri;

                    url_server = `/BA/api/simple/update`;   // URL to communicate with the server's endpoint
                }


                // Go over each field.  TODO: generalize (as done in the "records" component)
                if ('name' in this.current_data)
                    post_body += "&name=" + encodeURIComponent(this.current_data.name);
                else
                    this.current_data.name = "";

                if ('args' in this.current_data)
                    post_body += "&args=" + encodeURIComponent(this.current_data.args);
                else
                    this.current_data.args = "";

                if ('return' in this.current_data)
                    post_body += "&return=" + encodeURIComponent(this.current_data.return);
                else
                    this.current_data.return = "";

                if ('description' in this.current_data)
                    post_body += "&description=" + encodeURIComponent(this.current_data.description);
                else
                    this.current_data.description = "";


                this.waiting_mode = true;
                this.error_indicator = false;      // Clear possible past message

                console.log("In 'vue-plugin-cd', save().  post_body: ", post_body);
                ServerCommunication.contact_server(url_server, {post_body: post_body, callback_fn: this.finish_save});
            }, // save


            finish_save(success, server_payload, error_message, index)
            /*  Callback function to wrap up the action of save() upon getting a response from the server.
                In case of newly-created items, if successful, the server_payload will contain the newly-assigned ID
             */
            {
                console.log("Finalizing the CodeDocumentation save operation...");
                if (success)  {     // Server reported SUCCESS
                    this.status = `Successful edit`;

                    // If this was a new item (with the temporary ID of -1), update its ID with the value assigned by the server
                    if (this.item_data.uri == -1)
                        this.current_data.uri = server_payload;

                    // Inform the parent component of the new state of the data
                    console.log("Codedoc component sending `updated-item` signal to its parent");
                    this.$emit('updated-item', this.current_data);

                    // Synchronize the baseline data to the current one
                    this.original_data = Object.assign({}, this.current_data);  // Clone
                }
                else  {             // Server reported FAILURE
                    this.status = `FAILED edit`;
                    this.error_indicator = true;
                    this.cancel_edit();     // Restore the data to how it was prior to the failed changes
                }

                // Final wrap-up, regardless of error or success
                this.editing_mode = false;      // Exit the editing mode
                this.waiting_mode = false;      // Make a note that the asynchronous operation has come to an end
            }, // finish_save


            cancel_edit()
            {
                // Restore the data to how it was prior to the aborted changes
                this.current_data = Object.assign({}, this.original_data);  // Clone from original_data

                if (this.current_data.uri == -1) {
                    // If the editing being aborted is of a NEW item, inform the parent component to remove it from the page
                    console.log("CodeDocs sending `cancel-edit` signal to the parent component");
                    this.$emit('cancel-edit');
                }
            } // cancel_edit

        }  // METHODS

    }
); // end component