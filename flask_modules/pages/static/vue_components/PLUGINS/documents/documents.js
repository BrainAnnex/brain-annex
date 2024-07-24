/*  Vue component to display and edit Content Items of type "d" (Documents)
 */

Vue.component('vue-plugin-d',
    {
        props: ['item_data', 'edit_mode', 'category_id', 'index', 'item_count'],
        /*  item_data:      EXAMPLE: {"basename": "test", "caption": "My first document", "class_name": "Documents",
                                      "uri": 4849, "pos": 0, "schema_code": "d", "suffix": "txt"}
                                      (if uri is -1, it means that it's a newly-created header, not yet registered with the server)

            edit_mode:      A boolean indicating whether in editing mode
            category_id:    The URI of the Category page where this document is displayed (used when creating new documents)
            index:          The zero-based position of this Document on the page
            item_count:     The total number of Content Items (of all types) on the page [passed thru to the controls]
         */

        template: `
            <div>	<!-- Outer container box, serving as Vue-required template root  -->

            <!-- Document container -->
            <div class='doc'>
                <img src="/BA/pages/static/graphics/document_48_8168668.png" style="float: left; margin-right: 5px">

                <input v-show="edit_metadata" v-model="current_caption">
                <span v-show="!edit_metadata" style='font-weight:bold; font-size:12px'>&ldquo;{{item_data.caption}}&rdquo;</span>

                <br><br>

                <a href v-bind:href="document_url(item_data)"
                        v-bind:title="item_data.caption" v-bind:alt="item_data.caption"
                        target="_blank"
                >
                    {{item_data.basename}}.{{item_data.suffix}}
                </a>
                <br><br>

                <!-- Controls to edit the document metadata -->
                <p v-show="edit_metadata" style="text-align: right">
                    <span @click="cancel_edit" class="clickable-icon" style="color:blue">CANCEL</span>
                    <button @click="save_edit" style="margin-left: 15px; font-weight: bold; padding: 10px">SAVE</button>
                </p>
            </div>		<!-- End of Document container -->


            <!--  STANDARD CONTROLS (a <SPAN> element that can be extended with extra controls)
                  Signals from the Vue child component "vue-controls" below
                  get relayed to the parent of this component,
                  but some get intercepted and handled here, namely:

                          v-on:edit-content-item
            -->
            <!-- OPTIONAL MORE CONTROLS to the LEFT of the standard ones would go here -->

            <vue-controls v-bind:edit_mode="edit_mode"  v-bind:index="index"  v-bind:item_count="item_count"
                          v-on="$listeners"
                          v-on:edit-content-item="edit_content_item">
            </vue-controls>

            <!-- OPTIONAL MORE CONTROLS to the RIGHT of the standard ones would go here -->

            \n</div>\n		<!-- End of outer container box -->
            `,


        // ------------------------------   DATA   ------------------------------
        data: function() {
            return {
                // This object contains the values bound to the editing field, cloned from the prop data;
                //      it'll change in the course of the edit-in-progress
                current_data: Object.assign({}, this.item_data),

                // Clone, used to restore the data in case of a Cancel or failed save
                original_data: Object.assign({}, this.item_data),

                edit_metadata: false,

                current_caption: this.item_data.caption,
                original_caption: this.item_data.caption
            }
        }, // data


        // ------------------------------   METHODS   ------------------------------
        methods: {
            document_url(item_data)
            // Return the URL of the full documents
            {
                return '/BA/api/serve_media/' + item_data.uri;           // Invoke the file server
             },


            edit_content_item()
            {
                //console.log(`Documents component received signal to edit document`);
                this.edit_metadata = true;
            },

            cancel_edit()
            {
                //console.log(`In cancel_edit()`);
                this.current_caption = this.original_caption;
                this.edit_metadata = false;
            },

            save_edit()
            {
                console.log(`In save_edit(): attempting to save the new caption (${this.current_caption}) , for document with URI '${this.item_data.uri}'`);
                alert("Saving is not yet implemented, sorry!");
            },

        }  // methods

    }
); // end component