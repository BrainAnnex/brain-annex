/*  Vue component to display and edit Content Items of ANY type.  Based on the specific type,
    it DISPATCHES to components specialized for that type.

    IMPORTANT: if no handler is registered - as described by the argument 'registered_plugins' -
               it will default to be treated as a generic record, managed by the general "r" handler
 */

Vue.component('vue-content-items',
    {
        props: ['item', 'expose_controls', 'category_id', 'index', 'item_count', 'registered_plugins', 'records_types', 'schema_data'],
        /*  item:       EXAMPLE: {item_id:52, pos:10, schema_code:"h", text:"MY NEW SECTION", class_name: "Headers"}
                                 (if item_id is -1, it means that it's a newly-created header, not yet registered with the server)
            expose_controls: Flag indicating whether in edit mode
            category_id:    Indicating which Category-viewer page is using this component
            index:          The zero-based position of this Content Items on the page
            item_count:     The total number of Content Items (of all types) on the page
            registered_plugins: A list of codes of Content Items that have a dedicated Vue plugin
                                    EXAMPLE: ["n", "i", "h", "cd", "d"]
            records_types:  A list of all the Classes that can be used for new Records
                                (i.e. classes that are INSTANCE_OF the "Records" class)
            schema_data:    Only used for Content Items of type Record (schema_code "r"). A list of field names, in order.
                                EXAMPLE: ["French", "English", "notes"]

            NOTE: some of the data is just passed thru by the child components, on its way to the grand-child 'vue-controls'
                  (TODO: bundle that data into an object)
         */

        template: `
            <div v-bind:class="{'highlight': highlight }">	<!-- Outer container, serving as Vue-required template root  -->

            <a v-bind:name="item.schema_code + '_' + item.item_id"></a>  <!-- Anchor for page scrolling -->

            <!--
                 The line with "v-bind:is" dynamically dispatches to the appropriate specialized component.

                 All signals from descendant components get relayed (with v-on="$listeners")
                 to the parent of this component,
                 and some also get listened to here - namely:
                    v-on:delete-content-item
                    v-on:add-content            (from the 'vue-controls' component)
            -->
            <component
                v-bind:is="plugin_component_name(item, registered_plugins)"

                v-bind:item_data="item"
                v-bind:allow_editing="expose_controls"
                v-bind:category_id="category_id"
                v-bind:index="index"
                v-bind:item_count="item_count"
                v-bind:schema_data="schema_data"

                v-on="$listeners"

                v-on:delete-content-item="highlight_item(item)"
                v-on:add-content="add_content_below(item)"
            >
            </component>

            <p v-if="show_button" class="confirm-question">Confirm DELETE (item {{item.item_id}})?
                <button button @click="confirm_delete" class='confirm-button'>OK</button>
                <button button @click="cancel_delete" class='cancel-button'>Cancel</button>
            </p>

            <p v-if="insert_box" class="insert-box">
                <span style="margin-right:10px">Add new:</span>
                <button @click="add_new_item_below('h')" style="margin-right:10px">Header</button>
                <button @click="add_new_item_below('n')" style="margin-right:10px">Note</button>
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

            </div>		<!-- End of outer container -->
            `,


        data: function() {
            return {
                highlight: false,       // Whether to highlight this Content Item (e.g. prior to deleting it)
                show_button: false,
                insert_box: false
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


            add_content_below(item)
            // Expose a box below the Item, to let the user enter a new Content Item
            {
                console.log(`'vue-content-items' component received Event 'add-content'. Adding new content Item below Item ID: ${item.item_id}`);
                //console.log(item);
                this.insert_box = true;
            },


            add_new_item_below(schema_code, class_name)
            /*  Add a new Content Item of the specified type, placed at the bottom of the page (past the last Item);
                class_name is an OPTIONAL argument, only used for Content Item of type 'r'.
             */
            {
                console.log(`In 'vue-content-items' component, add_new_item_below().`);
                console.log(`    Request to insert new Content Item below Item with ID ${this.item.item_id}`);
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