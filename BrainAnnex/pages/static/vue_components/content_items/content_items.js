/*  Vue component to display and edit Content Items of ANY type.
    Depending on the specific type,
    it DISPATCHES to Vue components specialized for that type.

    IMPORTANT: if no handler is registered - as described by the argument 'registered_plugins' -
               it will default to be treated as a generic record, managed by the general "r" handler
 */

Vue.component('vue-content-items',
    {
        props: ['item', 'expose_controls', 'category_uri', 'index', 'item_count',
                'registered_plugins', 'records_types', 'schema_data', 'all_categories'],
        /*  item:           EXAMPLE: {uri:"52", pos:10, schema_code:"h", text:"MY NEW SECTION", class_name: "Headers"}
                                     (if uri is -1, it means that it's a newly-created header, not yet registered with the server)
            expose_controls:Flag indicating whether in edit mode
            category_uri:   A string indicating which Category-viewer page is using this component
            index:          The zero-based position of this Content Items on the above Category-specific page
            item_count:     The total number of Content Items (of all types) on the above Category-specific page
            registered_plugins: A list of codes of Content Items that have a dedicated Vue plugin
                                    EXAMPLE: ["n", "i", "h", "cd", "d"]
            records_types:  A list of all the Classes that can be used for new Records
                                (i.e. classes that are INSTANCE_OF the "Records" class)
            schema_data:    Only used for Content Items of type Record (schema_code "r"). A list of field names, in order.
                                EXAMPLE: ["French", "English", "notes"]
            all_categories: A list of dicts.  Note that the 'remarks' and 'pinned' keys may or may not be present.
                                EXAMPLE:
                                      [{"uri": 1, "name": "HOME"},
                                       {"uri": 523, "name": "Work at Acme", "remarks": "at main branch", "pinned": True}]

            NOTE: some of the data is just passed thru by the child components, on its way to the grand-child 'vue-controls'
                  (TODO: bundle that data into an object)
         */

        template: `
            <div v-bind:class="{'highlight': highlight}">	<!-- Outer container, serving as Vue-required template root  -->

            <a v-bind:name="item.schema_code + '_' + item.uri"></a>  <!-- Anchor for page scrolling -->

            <!--
                 The line with "v-bind:is" dynamically dispatches to the appropriate specialized component.

                 All signals from descendant components get relayed (with v-on="$listeners")
                 to the parent of this component,
                 while some (originating from the 'vue-controls' component) ALSO get listened to here - namely:

                    v-on:delete-content-item
                    v-on:add-content
                    v-on:edit-tags
            -->
            <component
                v-bind:is="plugin_component_name(item, registered_plugins)"

                v-bind:item_data="item"
                v-bind:allow_editing="expose_controls"
                v-bind:category_id="category_uri"
                v-bind:index="index"
                v-bind:item_count="item_count"
                v-bind:schema_data="schema_data"

                v-on="$listeners"

                v-on:delete-content-item="highlight_item(item)"
                v-on:add-content="add_content_below"
                v-on:edit-tags="edit_tags"
            >
            </component>

            <p v-if="show_button" class="confirm-question">Confirm DELETE (item {{item.uri}})?
                <button button @click="confirm_delete" class='confirm-button'>OK</button>
                <button button @click="cancel_delete" class='cancel-button'>Cancel</button>
            </p>

            <p v-if="insert_box" class="insert-box">
                <!-- TODO: should be merged with counterpart ("Add at the bottom of page") on page_viewer.htm -->
                <img @click="insert_box = false" src="/BA/pages/static/graphics/close_box_16_red.png"
                     class="control" style="float: right" title="Close" alt="Close">

                <span style="margin-right:10px">Add new:</span>
                <button @click="add_new_item_below('h')" style="margin-right:10px">Header</button>
                <button @click="add_new_item_below('n')" style="margin-right:10px">Note</button>
                <button @click="add_new_item_below('sl', 'Site Link')" style="margin-right:10px">Site Link (Bookmark)</button>
                <button @click="add_new_item_below('cd')" style="margin-right:10px">Code Documentation</button>

                <!-- All leaf Classes that are instances of "Records" -->
                <br>Add new record of type:
                <button v-for="(class_name, index) in records_types"
                    @click="add_new_item_below('r', class_name)"
                    class="record-picker"
                    v-bind:style="{'color': color_picker(index)}">
                    {{class_name}}
                </button>
            </p>

            <div v-if="tag_edit_box" class="insert-box">
                <img @click="tag_edit_box = false" src="/BA/pages/static/graphics/close_box_16_red.png"
                     class="control" style="float: right" title="Close" alt="Close">

                <span class="tag-header">Current Category Tags for this Item:</span><br>
                <!-- DISPLAY ALL CURRENT CATEGORY TAGS -->
                <span style="margin-left:20px; color:gray; font-style:italic">(last tag cannot be deleted)</span><br>
                <template v-for='category_name in this.categories_linked_to'>
                    <span style="font-weight:bold; margin-left:15px; border:1px solid black; background-color:#DDD">&nbsp; {{category_name}} &nbsp;</span>
                </template >
                <br><br>

                <b>ADD CATEGORY TAG: </b>
                <!-- Pulldown menu to add tags -->
                <form style='display:inline-block; margin-left:3px'>
                    <select @change='add_tag(item.uri, category_uri_to_add)' v-model="category_uri_to_add"
                            v-bind:title="'Add Category tags to this Content Item'">
                        <option value="" selected>[Select new tag]</option>
                        <option v-for="cat in all_categories"
                                v-if="cat.uri != category_uri"
                                v-bind:value="cat.uri">{{cat.name}}</option>
                    </select>
                </form>
                <!-- Status info -->
                <span v-if="waiting" class="waiting">Performing the requested operation...</span>
                <span v-bind:class="{'error-message': error, 'status-message': !error }">{{status_message}}</span>
            </div>
            
            </div>		<!-- End of outer container -->
            `,


        data: function() {
            return {
                tag_edit_box: false,    // Whether to display a box used to edit the Category tags of this Content Item

                highlight: false,       // Whether to highlight this Content Item (e.g. prior to deleting it)
                show_button: false,
                insert_box: false,      // Whether to display a box used to insert a new Content Item below this one

                categories_linked_to: [],   // Array of names of Categories to which this Content Item is attached to
                category_uri_to_add: "",    // URI of the Category chosen to tag this Content Item with ("" means "not chosen yet")

                waiting: false,         // Whether any server request is still pending
                error: false,           // Whether the last server communication resulted in error
                status_message: ""      // Message for user about status of last operation upon server response (NOT for "waiting" status)
            }
        }, // data


        // ---------------------------  METHODS  ---------------------------
        methods: {
            color_picker(index)
            // Rotate among a pre-picked color palette based on the given index
            {
                const color_arr = ["#ae9cd6", "#8bb9d4","#a6cfa1", "#dad6a1", "#e1b298", "#e59ca0", "gray"];

                const number_colors = color_arr.length;

                const module_index = index % number_colors;

                return color_arr[module_index];
            },


            add_content_below()
            // Expose a box below the Item, to let the user enter a new Content Item
            {
                console.log(`'vue-content-items' component received Event 'add-content'. Showing box to adding new content below Item with URI: ${this.item.uri}`);
                this.insert_box = true;
            },


            edit_tags()
            // Expose a box below the Item, to let the user view/add/remove Category tags for this Content Item
            {
                console.log(`'vue-content-items' component received Event 'edit-tags'.  Showing editing box for the tags of Item with URI: ${this.item.uri}`);
                //console.log(this.item);
                this.tag_edit_box = true;
                this.populate_category_links();     // Query the server, if needed
            },


            add_tag(item_uri, category_uri)
            // Invoked when the user chooses an entry from the "ADD CATEGORY TAG" menu
            {
                console.log(`add_tag(): will be sending request to server to tag Content Item '${item_uri}' with Category '${category_uri}'`);
                const url_server_api = `/BA/api/link_content_at_end/${category_uri}/${item_uri}`;
                console.log(`About to contact the server at ${url_server_api}`);

                this.waiting = true;        // Entering a waiting-for-server mode
                this.error = false;         // Clear any error from the previous operation
                this.status_message = "";   // Clear any message from the previous operation

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server(url_server_api,
                            {callback_fn: this.finish_add_tag
                            });
            },

            finish_add_tag(success, server_payload, error_message, custom_data)
            // Callback function to wrap up the action of add_tag() upon getting a response from the server
            {
                console.log("Finalizing the add_tag() operation...");
                if (success)  {     // Server reported SUCCESS
                    console.log("    server call was successful; it returned: ", server_payload);
                    this.status_message = `Operation completed`;
                    this.categories_linked_to.push("NEW CATEGORY NAME TBA");    // TODO: fix!
                }
                else  {             // Server reported FAILURE
                    this.error = true;
                    this.status_message = `FAILED operation: ${error_message}`;
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;           // Make a note that the asynchronous operation has come to an end
                this.category_uri_to_add = "";  // Return pulldown menu to ask user to SELECT
            },


            populate_category_links()
            /* Query the server, if needed, to find out which Categories this Content Item is attached to
             */
            {
                if (this.categories_linked_to.length > 0)  {
                    // If the variable is already populated
                    console.log("populate_category_links(): no need to invoke the server");
                    return;
                }

                // Send the request to the server, using a GET
                const url_server_api = `/BA/api/get_categories_linked_to/${this.item.uri}`;
                console.log(`About to contact the server at ${url_server_api}`);

                this.waiting = true;        // Entering a waiting-for-server mode
                this.error = false;         // Clear any error from the previous operation
                this.status_message = "";   // Clear any message from the previous operation

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server(url_server_api,
                            {callback_fn: this.finish_populate_category_links
                            });
            },

            finish_populate_category_links(success, server_payload, error_message, custom_data)
            // Callback function to wrap up the action of populate_category_links() upon getting a response from the server
            {
                console.log("Finalizing the populate_category_links() operation...");
                if (success)  {     // Server reported SUCCESS
                    console.log("    server call was successful; it returned: ", server_payload);
                    this.status_message = `Operation completed`;
                    var name_arr = [];
                    // For now, discard the "remarks" - and only utilize the Category names
                    for (i in server_payload) {     // i is a numeric index over the array
                        name_arr.push(server_payload[i][0]);
                    }
                    this.categories_linked_to = name_arr;
                }
                else  {             // Server reported FAILURE
                    this.error = true;
                    this.status_message = `FAILED operation: ${error_message}`;
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;      // Make a note that the asynchronous operation has come to an end
            },



            add_new_item_below(schema_code, class_name)
            /*  Add a new Content Item of the specified type, placed at the bottom of the page (past the last Item);
                class_name is an OPTIONAL argument, only used for Content Item of type 'r'.
             */
            {
                console.log(`In 'vue-content-items' component, add_new_item_below().`);
                console.log(`    Request to insert new Content Item below Item with ID ${this.item.uri}`);
                console.log(`    New item - schema_code: ${schema_code}, class_name (optional): ${class_name}`);
                console.log("    `vue-content-items` component is sending 'insert-new-item' signal to its parent");
                // This signal will be handled in the root component
                this.$emit('insert-new-item', {
                                                schema_code: schema_code,
                                                class_name: class_name
                                              });
                this.insert_box = false;    // Hide the box that was used for the selection of the type of new Content
            },


            confirm_delete()
            {
                console.log("Confirming delete");
                console.log("`vue-content-items` component is sending 'delete-content-item-highlighted' signal to its parent");
                this.$emit('delete-content-item-highlighted');
            },


            cancel_delete()
            {
                console.log("Cancelling delete");
                this.highlight = false;
                this.show_button = false;
            },


            highlight_item(item)
            {
                console.log(`'vue-content-items' component received Event 'delete-content-item'`);
                this.highlight = true;
                this.show_button = true;
            },


            plugin_component_name(item, registered_plugins)
            /* This is where the DISPATCHING (to specialized Vue components) gets set up.
               Compose and return the name of the plugin-provided
               Vue component to handle the given item (based on its type, stored in item.schema_code)

               IMPORTANT: if no handler is registered, default to the generic "r" (general records) handler

               :param item:                 An object representing a Content Item
               :param registered_plugins:   A list of item codes for which a plugin exists
               :return:                     A string.   EXAMPLE:  "vue-plugin-n"
             */
            {
                if (registered_plugins.includes(item.schema_code))
                    return "vue-plugin-" + item.schema_code;
                else
                    return "vue-plugin-r"
            }

        }  // METHODS

    }
); // end component