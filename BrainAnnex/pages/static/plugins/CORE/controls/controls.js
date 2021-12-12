/* Standard controls for Content Items to edit, move, etc,  */

Vue.component('vue-controls',
    {
        props: ['allow_editing', 'index', 'item_count'],
        /*  index:      the zero-based position of the Record on the page
            item_count: the total number of Content Items on the page
         */

        template: `
            <div class='content-controls'>	<!-- Outer container box, serving as Vue-required template root  -->

            <template v-if="allow_editing" >
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

                <img @click="add_content_below" src="/BA/pages/static/graphics/plusCircle3_16_183316.png"
                     class="control" title="Add new item below" alt="Add new item below">

                <img @click="edit" src="/BA/pages/static/graphics/edit_16_pencil2.png"
                     class="control" title="EDIT" alt="EDIT">
            </template>

            \n</div>\n		<!-- End of outer container box -->
            `,

        data: function() {
            return {
                move_after: -1      // Index of the chosen Content Item to move an Item after (in a move operation)
            }
        },


        // --------------------  METHODS  ---------------------
        methods: {

            /* The controls are handled by various ancestral components, including the Vue root element
             */

            add_content_below() {
                // Note: this signal will get intercepted by the `vue-content-items` ancestor component
                console.log("`vue-controls` component is sending 'add-content' signal to its parent");
                this.$emit('add-content');
            },

            delete_item() {
                // Note: this signal will get intercepted by any listening ancestor component
                console.log("`vue-controls` component is sending 'delete-content-item' signal to its parent");
                this.$emit('delete-content-item');
            },

            move_up() {
                // Note: this signal gets ultimately intercepted by the GRAND-parent component
                console.log("`vue-controls` component is sending 'move-up-content-item' signal to its parent");
                this.$emit('move-up-content-item');
            },

            move_down() {
                // Note: this signal gets ultimately intercepted by the GRAND-parent component
                console.log("`vue-controls` component is sending 'move-down-content-item' signal to its parent");
                this.$emit('move-down-content-item');
            },

            move_item() {
                // Invoked when the user chooses an entry from the move-to menu
                // Note: this signal gets ultimately intercepted by the GRAND-parent component
                console.log("`vue-controls` component is sending 'relocate-content-item' signal to its parent, with argument: ", this.move_after);
                this.$emit('relocate-content-item', this.move_after);
            },

            /* Controls handled by the PARENT component
             */
            edit() {
                // Note: this signal, UNLIKE the other ones, is meant for the PARENT component
                console.log("`vue-controls` component is sending 'edit-content-item' signal to its parent");
                this.$emit('edit-content-item');
            }

        } // METHODS

    }
); // end component