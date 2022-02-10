Vue.component('vue-category-navbox',
    {
        props: ['category_name', 'parent_categories', 'subcategories', 'all_categories'],
        /*  category_name:
            parent_categories:
            subcategories:
            all_categories:
         */

        template: `
            <div>  <!-- Outer container, serving as Vue-required template root.  OK to use a <section> instead -->


                <!--
                    EXPANDED (normal) version of sidebox
                  -->
                <div v-show='show_sidebox'  class='sidebox'>
                    <img v-on:click='show_sidebox = false'  src='/BA/pages/static/graphics/thin_left_arrow_32.png'
                         class='clickable-icon'
                         align='right' title='Click to collapse sidebox' alt='Click to collapse sidebox'>

                    <span class="sidebox-section">PINNED</span>
                    <br>&bull; <a href='/BA/pages/viewer/TBA' title="TBA">TBA</a>

                    <hr>

                    <span class="sidebox-section">RELATED</span>
                    <br>
                    <!-- All parent categories -->
                    <span style='color:#BBBBBB; font-size:8px; font-style:italic'>Parent Categories:</span>
                    <template v-for="category in parent_categories">
                        <br>&deg; <a v-bind:href="'/BA/pages/viewer/' + category['item_id']">{{category.name}}</a>
                    </template>
                    <br><br>

                    <!-- The current category -->
                    <div style='color:brown; font-weight:bold; font-size:12px; background-color:#F3F3F3; text-align: center'>
                        {{category_name}}
                    </div>

                    <br>

                    <!-- All sibling categories -->
                    <div style='border:1px solid #AAA; padding:2px'>
                        <span style='color:#BBBBBB; font-size:8px; font-style:italic'>Sibling Categories:</span>
                        <br>TBA
                    </div>

                    <br>

                    <!-- All subcategories -->
                    <span style='color:#BBBBBB; font-size:8px; font-style:italic'>Sub-categories:</span>
                    <template v-for="category in subcategories">
                        <br>&deg; <a v-bind:href="'/BA/pages/viewer/' + category['id']">{{category.name}}</a>
                    </template>

                    <hr>

                    <!-- The category listing -->
                    <span class="sidebox-section">
                        <a  @click.prevent="filter=false"  href="#"
                            title='Show ALL categories' alt='Show ALL categories'>ALL</a>
                    </span>
                    <br>
                    <a v-for="letter in alphabet"  @click.prevent="set_filter(letter)"  href="#">
                        {{letter}}
                    </a>
                    <br>

                    <!-- UN-filtered listing of all categories -->
                    <template v-if="!filter" v-for="category in all_categories">
                        <br>&diams; <a v-bind:href="'/BA/pages/viewer/' + category['id']">{{category.name}}</a>
                    </template>

                    <!-- FILTERED listing of categories with names starting with a particular letter -->
                    <template v-if="filter">
                        <br><span style="font-weight:bold">{{filter}}:</span><br>
                        <template v-for="category in categories_to_show">
                            <br>&diams; <a v-bind:href="'/BA/pages/viewer/' + category['id']">{{category.name}}</a>
                        </template>
                        <template v-if="categories_to_show.length == 0">
                            <br><span style="color:gray; font-style: italic">No categories names start with this letter</span>
                        </template>
                        <br><br>
                        <img @click="filter=false" class="clickable-icon"
                              title='Show ALL categories (or click on ALL)' alt='Show ALL categories (or click on ALL)'
                              src='/BA/pages/static/graphics/filter_remove_16.gif'>
                    </template>

                    <br>
                    <br>

                </div>  <!-- END of (expanded version of) sidebox -->



                <!--
                    COLLAPSED version of sidebox
                  -->
                <div v-show='!show_sidebox' class='sidebox_collapsed' style='display:none'>
                    <img v-on:click='show_sidebox = true'  src='/BA/pages/static/graphics/thin_right_arrow_32.png'
                         class='clickable-icon'
                         align='left' title='Click to expand sidebox' alt='Click to expand sidebox'>
                </div>  <!-- END of collapsed version of sidebox -->


            </div>		<!-- End of outer container -->
            `,



        data: function() {
            return {
                show_sidebox: true,  // Indicating whether to show or collapse the right sidebox (with the Category navigation)

                alphabet: ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                           'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'],

                filter: false,

                categories_to_show: this.all_categories
            }
        },



        // ----------------  METHODS  -----------------
        methods: {
            set_filter(l) {
                //alert(`Filtering for category names starting with ${l} : sorry, not yet implemented!`);
                this.categories_to_show = this.all_categories.filter( cat => cat.name[0] == l);
                this.filter = l;
            }

        }  // METHODS

    }
); // end component