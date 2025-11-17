/*  Vue component to display and edit a Content Item of ANY type.

    Depending on the specific type of the Content Item,
    it DISPATCHES to Vue component customized for that type.

    If in "insert_box" mode, display (below the Vue component for this Content Item) a box
    used to insert a new Content Item below this one.  This special box also includes a "dropzone" element,
    to upload media.
    TODO: possibly shift this responsibility to the parent (root) element.
          A potential design:   just like currently being done, add entries with negative uri's
                                to the `content_array` of page_viewer.html

    IMPORTANT: if no handler is registered - as described by the argument 'registered_plugins' -
               it will default to be treated as a generic record, managed by the general "r" handler
 */

Vue.component('vue-content-items',
    {
        props: ['item', 'expose_controls', 'category_uri', 'index', 'item_count',
                'registered_plugins', 'records_types', 'schema_data', 'all_categories'],
        /*  item:           EXAMPLE: {uri:"52", pos:10, schema_code:"h", text:"MY NEW SECTION", class_name: "Header"}

                            If this is a a newly-created Content Item, not yet registered with the server,
                            then the `uri` will be a negative number,
                            and there will be additional fields such as `insert_after_uri` and `insert_after_class`
                            EXAMPLE: {uri: -2, insert_after_uri: "i-123", "insert_after_class": "Image"}

                            TODO: Maybe rename to item_data

            expose_controls:    Flag indicating whether in edit mode
            category_uri:       A string indicating which Category-viewer page is using this component
            index:              The zero-based position of this Content Items on the above Category-specific page
            item_count:         The total number of Content Items (of all types) on the above Category-specific page
            registered_plugins: A list of codes of Content Items that have a dedicated Vue plugin
                                    EXAMPLE: ["n", "i", "h", "cd", "d", "sl", "rs"]
            records_types:      A list of all the Classes that can be used for new Records
                                    (i.e. classes that are INSTANCE_OF the "Records" class)
            schema_data:        Only used for Content Items of type Record (schema_code "r"). A list of field names, in order.
                                    EXAMPLE: ["French", "English", "notes"]
            all_categories:     A list of dicts.  Note that the 'remarks' and 'pinned' keys may or may not be present.
                                    EXAMPLE:
                                      [{"uri": "1", "name": "HOME"},
                                       {"uri": "523", "name": "Work at Acme", "remarks": "at main branch", "pinned": True}]

            NOTE: some of the data is just passed thru by the child components, on its way to the grand-child 'vue-controls'
                  (TODO: bundle that data into an object)
         */

        template: `
            <!-- Outer container, serving as Vue-required template root -->
            <div v-bind:class="{'highlight': highlight, 'content-item': !use_separate_line, 'content-item-separate-line': use_separate_line}">

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
                v-bind:edit_mode="expose_controls"
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

            <p v-if="show_button" class="confirm-question">Confirm DELETE (item URI '{{item.uri}}' of Class '{{item.class_name}}')?
                <button button @click="confirm_delete" class='confirm-button'>OK</button>
                <button button @click="cancel_delete" class='cancel-button'>Cancel</button>
            </p>



            <!-- BOX FOR INSERTION OF NEW CONTENT BELOW -->
            <div v-show="insert_box" class="item-insert-box">
                <!-- TODO: should be merged with counterpart ("Add at the bottom of page") on page_viewer.htm -->
                <img @click="insert_box = false" src="/BA/pages/static/graphics/close_box_16_red.png"
                     class="control" style="float: right" title="Close" alt="Close">

                <span style="margin-right:10px">Add new:</span>
                <!-- TODO: automate these choices, based on Schema.  Merge with similar box in page_viewer.htm -->
                <button @click="add_new_item_below('h', 'Header')" style="margin-right:10px">Header</button>
                <button @click="add_new_item_below('n', 'Note')" style="margin-right:10px">Note</button>
                <button @click="add_new_item_below('sl', 'Site Link')" style="margin-right:10px">Site Link (Bookmark)</button>
                <button @click="add_new_item_below('rs', 'Recordset')" style="margin-right:10px">Recordset</button>
                <button @click="add_new_item_below('cd', 'Code Documentation')" style="margin-right:10px">Code Documentation (deprecated)</button>
                &nbsp;&nbsp;&nbsp;
                <button @click="add_new_item_below('timer', 'Timer Widget')" style="margin-right:10px">Timer Widget</button>

                <!-- All leaf Classes that are instances of "Records" -->
                <br>Add new record of type:
                <button v-for="(class_name, index) in records_types"
                    @click="add_new_item_below('r', class_name)"
                    class="record-picker"
                    v-bind:style="{'color': color_picker(index)}">
                    {{class_name}}
                </button>


                <br><br>
                <b>UPLOAD IMAGES or DOCUMENTS</b>:<br>

                <!-- Provide a drag-and-drop area, which makes use of the "Dropzone" module.
                    The "id" and the "class" attributes of the FORM element below
                    are meant for use by the JS package "Dropzone" -->
                <form  class='dropzone'
                       v-bind:id="'myDropzone_' + item.uri"
                       action='/BA/api/upload_media'
                       style='padding-top:5px; margin-bottom:8px'
                >
                    <input v-bind:value="category_uri" type='hidden' name='category_id'>
                    <input v-bind:value="item.uri" type='hidden' name='insert_after_uri'>
                    <input v-bind:value="item.class_name" type='hidden' name='insert_after_class'>
                </form>


                <!--  The "DONE" button (a link made to look like a button) simply reloads the viewer page -->
                <button v-if="uploads_in_progress"  disabled  style='padding:4px'>
                    Upload in progress. WAITING until all uploads are complete...
                </button>
                <a v-else href=''
                    style='font-size:18px; border:1px solid #660000; background-color:#00cc00; text-decoration:none; color:#fff; border-radius:5px; padding:4px'
                >
                    Done
                </a>

                <span style='color:gray; margin-left:20px; font-size:10px'>Press the "Done" button when all uploads are complete, to reload the page</span><br>
                <br><b>Uploads</b> &nbsp; started: {{upload_started}} &nbsp;&nbsp;&nbsp;
                completed: <span style="color:green">{{upload_completed}}</span> &nbsp;&nbsp;&nbsp;
                errors: <span style="color:red">{{upload_errors}}</span>

            </div>



            <div v-if="tag_edit_box" class="insert-box">
                <img @click="tag_edit_box = false" src="/BA/pages/static/graphics/close_box_16_red.png"
                     class="control" style="float: right" title="Close" alt="Close">

                <span class="tag-header">Current Category Tags for this Item:</span><br><br>
                <!-- DISPLAY ALL CURRENT CATEGORY TAGS for this Content Item -->
                <template v-for='category in this.categories_linked_to'>
                    <span style="font-weight:bold; margin-left:20px; border:1px solid black; background-color:#DDD">&nbsp; {{category.name}} &nbsp;</span>
                    <span v-if="! is_last_tag">
                        <img @click="untag_category(category.uri, category.name)"
                             src="/BA/pages/static/graphics/delete_12_1493279.png">
                    </span>
                    <span v-else style="margin-left:15px; color:gray; font-style:italic">
                        (last tag cannot be deleted)
                    </span>
                </template>
                <br><br>

                <b>ADD CATEGORY TAG: </b>
                <!-- Pulldown menu to add tags: show all categories -->
                <form style='display:inline-block; margin-left:3px'>
                    <select @change='add_tag' v-model="category_to_add"
                            v-bind:title="'Add Category tags to this Content Item'">
                        <option disabled value="">[Select new tag]</option>
                        <option v-for="cat in all_categories"
                                v-if="cat.uri != category_uri"
                                v-bind:value="{uri: cat.uri , name: cat.name}">
                            {{cat.name}}
                        </option>
                    </select>
                </form>

                <!-- STATUS INFO -->
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
                insert_box: false,      // Whether to display, at the bottom, a box used to insert a new Content Item below this one

                categories_linked_to: [],   // Array of objects representing Categories to which this Content Item is attached to;
                                            //      each object contains the attributes "uri", "name", "remarks"

                category_to_add: "",        // Object with data about the Category chosen to tag this Content Item with
                                            //      Attributes are "uri" and "name" (Note: "" indicates no selection in the menu)

                //dropzone_id: "form#myDropzone_12345",     // This did NOT work

                uploads_in_progress: false, // Flag indicating whether any uploaded started but have not yet completed
                upload_started: 0,          // Number of file upload started
                upload_completed: 0,        // Number of file upload completed
                upload_errors: 0,           // Number of errors in file uploads

                waiting: false,         // Whether any server request is still pending
                error: false,           // Whether the last server communication resulted in error
                status_message: ""      // Message for user about status of last operation upon server response (NOT for "waiting" status)
            }
        }, // data



        computed: {
            is_last_tag()
            // Return true if the current Content Item is down to just 1 Category tag
            {
                return this.categories_linked_to.length == 1;
            },


            use_separate_line()
            /*  Return true if the current Content Item is meant to be shown on its own separate line -
                as opposed to possibly fitting multiple ones on a line, if the page is wide enough
             */
            {
                // TODO: make more general; store the "separate_line" flag in the Schema Class nodes
                //       Currently, we're covering some specific class, and the general "records" (which
                //       lack registered plugins)
                return (this.item.class_name == "Header") || (this.item.class_name == "Site Link")
                            || (this.item.class_name == "Recordset")
                            || !this.registered_plugins.includes(this.item.schema_code);
            }
        },


        // ---------------------------  METHODS  ---------------------------
        methods: {

            insert_dropzone_element()
            /* Invoked when a signal is received from the Vue controls component, to expose the box to add a new Content Item.
               Creating a "dropzone" object must be done programmatically, because the form containing the
               dropzone object was not present at page load.
               This object is used for the upload of media files.
             */
            {
                console.log(`About to dynamically create a 'Dropzone' object, `
                            + `immediately below Content Item URI '${this.item.uri}' of Class '${this.item.class_name}'`);

                // Note that the ID of the Dropzone FORM element makes reference to the PREVIOUS Content Item; this ID is not actually used, but should be unique
                // (if attempting to create it a second time, an error "Dropzone already attached" is generated - but it seems to cause no harm!)

                //const uuid = crypto.randomUUID();                 // This approach did NOT work
                //this.dropzone_id = "form#myDropzone_" + uuid;
                //const dropzone_form_id = this.dropzone_id;

                const dropzone_form_id = "form#myDropzone_" + this.item.uri;    // EXAMPLE: "form#myDropzone_h-86"   TODO: this ID might not be unique on a page; the URI might contain blanks
                                                                                // TODO: try to switch to the Internal Database ID instead
                                                                                // MUST match the value in the "v-bind:id" variable in form definition

                // If the Dropzone form element dropzone_form_id already exists (for example, if the insert box had previously been opened and then closed),
                // then don't create it.  TODO: alternatively, destroy the Dropzone object  when the insert box is closed
                if (! document.getElementById(dropzone_form_id)) {
                    console.log(`    will create a 'Dropzone' element with ID: '${dropzone_form_id}'`);
                    var myDropzone = new Dropzone(dropzone_form_id);
                    // IMPORTANT: for the above line to work, the DIV element that contains it must use
                    //            Vue conditional rendering with "v-show" rather than "v-if"

                    // Register a number of event handlers with the newly-created Dropzone object
                    myDropzone.on("addedfile", this.dropzoneHandler_addedfile);          // A new file gets added to the to-upload list
                    myDropzone.on("success", this.dropzoneHandler_success);              // The file has been uploaded successfully
                    myDropzone.on("queuecomplete", this.dropzoneHandler_queuecomplete);  // All files in the queue finish uploading
                    myDropzone.on("error", this.dropzoneHandler_error);                  // If the server returns anything other than a normal status
                }
            },


            /***********************************
                    DROPZONE-RELATED
             ***********************************/

            /*	TODO: perhaps provide a listing of the files being uploaded - and a handy way to change their metadata */

            dropzoneHandler_addedfile(evt)
            /* Handler for the Dropzone event "addedfile" :  generated as soon as each file is dragged and released (one per file), BEFORE upload;
               i.e. whenever a new file gets added to the to-upload list
             */
            {
                /* The event object for "addedfile" includes:
                    lastModifiedDate
                    name (filename)
                    size (bytes)
                    previewTemplate.innerText  (for example "500 b\nmyFile.txt")
                    upload.bytesSent
                    upload.progress
                    upload.total
                */
                console.log(`Dropzone event: 'addedfile'.  File name: "${evt.name}" | size:  ${evt.size} bytes`);
                //alert("Dropzone event: 'addedfile'.  File name: '" + evt.name + "' | size:  " + evt.size + " bytes");

                // Inactivate the "Done" button
                this.uploads_in_progress = true;

                // Update the number of "Uploads started"
                this.upload_started += 1;
            },


            dropzoneHandler_error(evt)
            /* Handler for the Dropzone event "error" : apparently activated if the server returns anything other than a normal status
               Update the count of upload errors
             */
            {
                /* The event object for error includes:

                    name
                    size (bytes)
                    xhr.status  (server error status code; e.g. 415)
                    xhr.statusText   (server error status text; e.g. "Unsupported Media Type")
                    xhr.responseText   (anything output in the body of the server response)
                */
                alert("***ERROR: FAILED UPLOAD of file \"" + evt.name + "\".  Reason: " + evt.xhr.responseText);

                // Update the number of "Upload errors"
                this.upload_errors += 1;
            },

            dropzoneHandler_success(evt)
            /* Handler for the Dropzone event "success" : the file has been uploaded successfully; gets the server response as second argument (not tried)
               Update the count of completed successful uploads
             */
            {
                console.log("Dropzone event: 'success'");

                // Update the number of "Uploads completed"
                this.upload_completed += 1;
            },

            dropzoneHandler_queuecomplete(evt)
            /* Handler for the Dropzone event "queuecomplete": called when all files in the queue finish uploading,
               i.e. ALL pending uploads are complete
             */
            {
                console.log("Dropzone event: 'queuecomplete'");

                // Restore the "Done" button
                this.uploads_in_progress = false;
            },





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
                console.log(`'vue-content-items' component received Event 'add-content'. Showing the box for adding new content below Item with URI: '${this.item.uri}' and Class '${this.item.class_name}'`);
                this.insert_box = true;
                this.insert_dropzone_element();
            },


            edit_tags()
            // Expose a box below the Item, to let the user view/add/remove Category tags for this Content Item
            {
                console.log(`'vue-content-items' component received Event 'edit-tags'.  Showing editing box for the tags of Item with URI: ${this.item.uri}`);
                //console.log(this.item);
                this.tag_edit_box = true;
                this.populate_category_links();     // Query the server, if needed
            },


            add_tag()
            // Invoked when the user chooses an entry from the "ADD CATEGORY TAG" menu
            {
                const category_uri = this.category_to_add.uri;
                const category_name = this.category_to_add.name;
                const item_uri = this.item.uri;

                //console.log(`add_tag(): requesting server to tag Item '${item_uri}' with Category '${category_name}' (URI '${category_uri}')`);
                const url_server_api = `/BA/api/link_content_at_end/${category_uri}/${item_uri}`;
                //console.log(`About to contact the server at ${url_server_api}`);

                this.waiting = true;        // Entering a waiting-for-server mode
                this.error = false;         // Clear any error from the previous operation
                this.status_message = "";   // Clear any message from the previous operation

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server_OLD(url_server_api,
                            {callback_fn: this.finish_add_tag,
                             custom_data: [category_uri, category_name]
                            });
            },

            finish_add_tag(success, server_payload, error_message, custom_data)
            // Callback function to wrap up the action of add_tag() upon getting a response from the server
            {
                console.log("Finalizing the add_tag() operation...");
                if (success)  {     // Server reported SUCCESS
                    //console.log("    server call was successful; it returned: ", server_payload);
                    this.status_message = `Operation completed`;
                    const [category_uri, category_name] = custom_data;       // Unpack URI and name of the Category that was added to the tags
                    this.categories_linked_to.push({name: category_name, uri: category_uri});       // To update the UI
                }
                else  {             // Server reported FAILURE
                    this.error = true;
                    this.status_message = `FAILED operation: ${error_message}`;
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;           // Make a note that the asynchronous operation has come to an end
                this.category_to_add = "";      // Return pulldown menu to ask user to SELECT
            },



            untag_category(category_uri, category_name)
            // Detach the current Content Item from the specified Category
            {
                const item_uri = this.item.uri;

                console.log(`Untag Item (URI ${item_uri}) from Category '${category_name}' (URI '${category_uri}') : Not yet implemented`);

                // Send the request to the server, using a GET
                const url_server_api = `/BA/api/detach_from_category/${category_uri}/${item_uri}`;
                console.log(`About to contact the server at ${url_server_api}`);

                this.waiting = true;        // Entering a waiting-for-server mode
                this.error = false;         // Clear any error from the previous operation
                this.status_message = "";   // Clear any message from the previous operation

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server_OLD(url_server_api,
                            {callback_fn: this.finish_untag_category,
                             custom_data: category_uri
                            });
            },

            finish_untag_category(success, server_payload, error_message, custom_data)
            // Callback function to wrap up the action of untag_category() upon getting a response from the server
            {
                console.log("Finalizing the untag_category() operation...");
                console.log(`Custom data passed: ${custom_data}`)
                if (success)  {     // Server reported SUCCESS
                    console.log("    server call was successful; it returned: ", server_payload);
                    this.status_message = `Operation completed`;
                    // Update the UI : drop the just-removed Category from the array categories_linked_to
                    const unlinked_uri = custom_data;
                    for (i in this.categories_linked_to) {   // Note:  i is the index, not an array element!
                        if (this.categories_linked_to[i]["uri"] == unlinked_uri)
                            this.categories_linked_to.splice(i, 1); // Deletes 1 element from the i-th position in array.
                                                                    //      Note: Vue automatically detect splice() ops
                    }
                }
                else  {             // Server reported FAILURE
                    this.error = true;
                    this.status_message = `FAILED operation: ${error_message}`;
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;      // Make a note that the asynchronous operation has come to an end
            },



            populate_category_links()
            /* Query the server, if needed, to find out which Categories this Content Item is attached to
             */
            {
                /*
                // Commented out : It may be good to refresh the list whenever re-opening the box...
                if (this.categories_linked_to.length > 0)  {
                    // If the variable is already populated
                    console.log("populate_category_links(): no need to invoke the server");
                    return;
                }
                */

                // Send the request to the server, using a GET
                const url_server_api = `/BA/api/get_categories_linked_to/${this.item.uri}`;
                console.log(`About to contact the server at ${url_server_api}`);

                this.waiting = true;        // Entering a waiting-for-server mode
                this.error = false;         // Clear any error from the previous operation
                this.status_message = "";   // Clear any message from the previous operation

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server_OLD(url_server_api,
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
                    this.categories_linked_to = server_payload;    // Update the UI
                }
                else  {             // Server reported FAILURE
                    this.error = true;
                    this.status_message = `FAILED operation: ${error_message}`;
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;      // Make a note that the asynchronous operation has come to an end
            },



            add_new_item_below(schema_code, class_name)
            /*  Add a new Content Item of the specified type, placed just below the current Item.
                TODO: consider an "add immediately" option, as done in v. 4 of BA
             */
            {
                // Send a signal to the parent (the Category Page) to insert a new blank item of the specified type, below this one
                console.log(`In 'vue-content-items' component, add_new_item_below().`);
                console.log(`    Request to insert new Content Item below the Item with URI '${this.item.uri}' and class name '${this.item.class_name}'`);
                console.log(`    New item - schema_code: '${schema_code}', class_name: '${class_name}'`);
                console.log("    `vue-content-items` component is sending 'insert-new-item-after' signal to its parent");

                // This signal will be handled by the root component: it contains the basic information (known so far) of the new Content Item
                this.$emit('insert-new-item-after', {
                                                schema_code: schema_code,
                                                class_name: class_name
                                              });
                // Note: after the signal is processed, the new Content Item will
                //       appear in editing mode in its handler Vue component,
                //       but not yet added to the database; it will be the Vue component's responsibility to save it,
                //       or cancel the operation

                this.insert_box = false;    // Hide the box that was used for the selection of the type of new Content
            },


            confirm_delete()
            // Invoked when the user clicks on the "Confirm DELETE" button
            {
                // Send a signal to the Vue root component
                console.log("Confirming delete");
                console.log("    `vue-content-items` component is sending 'delete-content-item-highlighted' signal to its parent");
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

               TODO: "schema_code" attribute ought to be stored on the Class nodes, not on the Data nodes

               :param item:                 An object representing a Content Item
               :param registered_plugins:   A list of item codes for which a plugin exists
               :return:                     A string.   EXAMPLE:  "vue-plugin-n"
             */
            {
                if (registered_plugins.includes(item.schema_code))
                    return "vue-plugin-" + item.schema_code;
                else
                    return "vue-plugin-r";      // Default to the generic "r" (general records) handler
            }

        }  // METHODS

    }
); // end component