/*  Standard controls for a Content Item to edit, move, delete, etc,
    If the 'edit_mode' prop is true, this component generates
        a DIV element with a row of controls;
        the DIV is an inline-block, so that the parent component
        may easily add extra controls at the start and/or end of its standard row.
    If the 'edit_mode' prop is false, nothing is generated

    TODO: maybe rename 'vue-standard-controls'
 */

Vue.component('vue-controls',
    {
        props: {
            edit_mode:  Boolean,        // Indicating whether in editing mode
            index:      Number,         // The zero-based position of the Content Item on the page
            item_count: Number,         // The total number of Content Items on the page
            controls_to_hide: {         // [OPTIONAL] Array of names of standard controls to omit;
                type: Array,            //            currently supported are 'edit' and 'tag'
                default: () => []
            }
        },



        template: `
            <div v-if="edit_mode"
                style='display:inline-block; margin:0px'>	<!-- Outer container box, serving as Vue-required template root  -->

                <img @click="delete_item" src="/BA/pages/static/graphics/delete_16.png"
                     class="control" title="DELETE" alt="DELETE">

                <img @click="move_up" src="/BA/pages/static/graphics/up_arrow_16_1303891.png"
                     class="control" title="Move UP" alt="Move UP">

                <!-- Pulldown menu to move the Item after a specified position on the page -->
                <form style='display:inline-block; margin-left:0px'>
                    <span class="index">{{ index + 1 }}</span>
                    <select @change='move_item' v-model="move_after"
                            v-bind:title="'Move this item (currently in position ' + (index+1) + ' on the page) to just after a specified position'">
                        <option value='-1' selected>Re-position after:</option>
                        <option v-for="n in item_count+1" v-if="(n != index+1) && (n != index+2)" v-bind:value="n-1">{{n-1}}</option>
                    </select>
                    <input type='hidden' name='elementToMove' value='contentID_TBA'>
                </form>

                <img @click="move_down" src="/BA/pages/static/graphics/down_arrow_16_1303877.png"
                     class="control" title="Move DOWN" alt="Move DOWN">

                <img v-show="!controls_to_hide.includes('tag')" @click="edit_tags" src="/BA/pages/static/graphics/tag_16.png"
                     class="control" title="Edit TAGS/Metadata" alt="Edit TAGS/Metadata">

                <img @click="add_content_below" src="/BA/pages/static/graphics/plusCircle3_16_183316.png"
                     class="control" title="Add new item below" alt="Add new item below">

                <img v-show="!controls_to_hide.includes('edit')" @click="edit" src="/BA/pages/static/graphics/edit_16_pencil2.png"
                     class="control" title="EDIT" alt="EDIT">

            </div>		<!-- End of outer container box -->
            `,


        // --------------------  DATA  ---------------------
        data: function() {
            return {
                move_after: -1      // Index of the chosen Content Item to move an Item after (in a move operation)
            }
        },



        // --------------------  METHODS  ---------------------
        methods: {

            /* Note: the controls send individual signals that get handled by various ancestral components,
                     possibly including the Vue root element.
                     Typically, the 'edit-content-item' signal is handled by the parent (the plugin-specific component),
                     while the other signals are handled by the `vue-content-items` grandparent component,
                     or by the Vue root element
             */

            add_content_below() {
                // Note: this signal will get intercepted by the `vue-content-items` ancestor component
                console.log("`vue-controls` component is sending an 'add-content' signal to its parent");
                this.$emit('add-content');
            },

            delete_item() {
                // Note: this signal will get intercepted by any listening ancestor component
                console.log("`vue-controls` component is sending a 'delete-content-item' signal to its parent");
                this.$emit('delete-content-item');
            },

            move_up() {
                // Note: this signal gets ultimately intercepted by the GRAND-parent component
                console.log("`vue-controls` component is sending a 'move-up-content-item' signal to its parent");
                this.$emit('move-up-content-item');
            },

            move_down() {
                // Note: this signal gets ultimately intercepted by the GRAND-parent component
                console.log("`vue-controls` component is sending a 'move-down-content-item' signal to its parent");
                this.$emit('move-down-content-item');
            },

            move_item() {
                // Invoked when the user chooses an entry from the move-to menu
                // Note: this signal gets ultimately intercepted by the GRAND-parent component (the Vue root element)
                console.log("`vue-controls` component is sending a 'relocate-content-item' signal to its parent, with argument: ", this.move_after);
                this.$emit('relocate-content-item', this.move_after);
            },

            edit_tags() {
                /* Invoked when the user clicks on the "Edit TAGS/Metadata" icon.
                    Send a signal meant for the GRAND-parent component `vue-content-items`
                 */
                console.log("`vue-controls` component is sending an 'edit-tags' signal to its parent");
                this.$emit('edit-tags');
            },


            edit() {
                // Note: this signal, UNLIKE the other ones, is meant for the PARENT component (the plugin-provided component)
                console.log("`vue-controls` component is sending an 'edit-content-item' signal to its parent");
                this.$emit('edit-content-item');
            }

        } // METHODS

    }
); // end component