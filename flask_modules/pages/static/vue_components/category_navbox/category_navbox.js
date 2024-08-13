Vue.component('vue-category-navbox',
/*  Listing of all Categories, including the "pinned" ones,
    and the parents/children/siblings of the current category.
    Option to FILTER the listing of categories to names starting with a particular letter
*/
    {
        props: ['category_name', 'current_category_uri',
                'parent_categories', 'subcategories', 'siblings_categories',
                'all_categories',
                'show_right_sidebox'],
        /*  category_name:          Name of the Category currently being viewed
            current_category_uri:   A string with the URI of the Category currently being viewed
            parent_categories:      List of the parent categories of the Current Category;
                                        each item is an object, whose keys include
                                        "uri" and "name" (among others)
            subcategories:          List of the subcategories of the Current Category
            siblings_categories:    List of the sibling categories of the Current Category;
                                    each item is an object, whose keys include
                                    "uri" and "name", "remarks" and "internal_id" (among others)
            all_categories:         EXAMPLE:
                                        [{"uri": "1", "name": "HOME", "remarks": "ROOT NODE"},
                                         {"uri": "523", "name": "work", 'pinned': True}]
            show_right_sidebox:     Flag indicating whether the sidebar is expanded (true) or contracted (false)
         */

        template: `
            <div>  <!-- Outer container, serving as Vue-required template root.  OK to use a <section> instead -->


                <!--
                    EXPANDED (normal) version of sidebox
                  -->
                <div v-show='show_right_sidebox'  class='sidebox'>
                    <img @click='set_sidebox_state(false)'  src='/BA/pages/static/graphics/thin_left_arrow_32.png'
                         class='clickable-icon  fixed-collapse-icon'
                         align='right' title='Click to collapse sidebox' alt='Click to collapse sidebox'>

                    <span class="sidebox-section">PINNED</span>
                    <br>
                    <!-- All pinned categories -->
                    <template v-for="category in all_categories">
                        <template v-if="category.pinned"><br>&bull; <a v-bind:href="'/BA/pages/viewer/' + category['uri']">{{category.name}}</a></template>
                    </template>


                    <hr>

                    <span class="sidebox-section">RELATED</span>
                    <br>
                    <!-- All parent categories -->
                    <span class='category-relatives'>Parent Categories:</span>
                    <span class='category-relatives' v-if="parent_categories.length === 0">None</span>
                    <template v-for="category in parent_categories">
                        <br>&deg; <a v-bind:href="'/BA/pages/viewer/' + category['uri']">{{category.name}}</a>
                    </template>
                    <br><br>

                    <!-- The current category -->
                    <div style='color:brown; font-weight:bold; font-size:12px; background-color:#F3F3F3; text-align: center'>
                        {{category_name}}
                    </div>

                    <br>

                    <!-- All sibling categories -->
                    <div style='border:1px solid #AAA; padding:2px'>
                        <span class='category-relatives'>Sibling Categories:</span>
                        <span class='category-relatives' v-if="siblings_categories.length === 0">None</span>
                        <template v-for="category in siblings_categories">
                            <br>&deg; <a v-bind:href="'/BA/pages/viewer/' + category['uri']">{{category.name}}</a>
                        </template>
                    </div>

                    <br>

                    <!-- All subcategories -->
                    <span class='category-relatives'>Sub-categories:</span>
                    <span class='category-relatives' v-if="subcategories.length === 0">None</span>
                    <template v-for="category in subcategories">
                        <br>&deg; <a v-bind:href="'/BA/pages/viewer/' + category['uri']">{{category.name}}</a>
                    </template>

                    <hr>

                    <!-- The category listing -->
                    <span class="sidebox-section">
                        <!-- One way to unset the filter -->
                        <a  @click.prevent="remove_filter()"  href="#"
                            title='Show ALL categories' alt='Show ALL categories'>ALL</a>
                    </span>

                    <br>
                    <!-- Option to set a filter when clicking on any of the letters -->
                    <a v-for="letter in alphabet"  @click.prevent="set_filter(letter)"  href="#"  class="alphabet-letters">
                        {{letter}}
                    </a>
                    <br>

                    <!-- If the filter is applied, show its name (1 or more letters) -->
                    <p v-if="filter" style="font-weight: bold; font-size: 16px; margin-bottom: 0">
                        <span v-if="filter.length >= 3">&ndash;</span>{{filter}}&ndash;
                        <!-- Another way to unset the filter -->
                        <img @click="remove_filter()" class="clickable-icon" style="margin-left: 10px"
                              title='Show ALL categories (or click on ALL)' alt='Show ALL categories (or click on ALL)'
                              src='/BA/pages/static/graphics/filter_remove_16.gif'>
                    </p>
                    <br>

                    <!-- Listing of all the categories allowed by the filter.  All but the current category will show links  -->
                    <ul style=''>
                    <template v-for="category in categories_to_show">
                        <li>
                        <a v-if="current_category_uri != category.uri" v-bind:href="'/BA/pages/viewer/' + category['uri']">{{category.name}}</a>
                        <span v-else class="current-category">{{category.name}}</span>
                        </li>
                    </template>
                    </ul>

                    <!-- If the filter is applied, show more info -->
                    <template v-if="filter">
                        <template v-if="categories_to_show.length == 0">
                            <br><span style="color:gray; font-style: italic">No categories names start with this letter</span>
                        </template>
                        <br><br>
                        <!-- Another way to unset the filter -->
                        <img @click="remove_filter()" class="clickable-icon"
                              title='Show ALL categories (or click on ALL)' alt='Show ALL categories (or click on ALL)'
                              src='/BA/pages/static/graphics/filter_remove_16.gif'>
                    </template>

                    <br>

                </div>  <!-- END of (expanded version of) sidebox -->



                <!--
                    COLLAPSED version of sidebox
                  -->
                <div v-show='!show_right_sidebox' class='sidebox_collapsed' style='display:none'>
                    <img @click='set_sidebox_state(true)'  src='/BA/pages/static/graphics/thin_right_arrow_32.png'
                         class='clickable-icon  fixed-expand-icon'
                         align='left' title='Click to expand sidebox' alt='Click to expand sidebox'>
                </div>  <!-- END of collapsed version of sidebox -->


            </div>		<!-- End of outer container -->
            `,



        data: function() {
            return {
                alphabet: ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                           'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'],

                filter: false,      // Either false, or a string

                categories_to_show: this.all_categories // List of Categories to show in the legend
            }
        },



        // ----------------  METHODS  -----------------
        methods: {
            set_sidebox_state(state)
            {
                console.log("Component 'vue-category-navbox' sending `adjust-right-sidebox` signal to its parent, with parameter: ", state);
                this.$emit('adjust-right-sidebox', state);
            },

            set_filter(l)
            /* Invoked when the user click on a particular letter, in the alphabet of choices.
               The argument is a capital letter
             */
            {
                //alert(`Filtering for letter ${l}`);

                if (!this.filter)
                    this.filter = l;    // Start a new filter
                else
                    this.filter += l;   // Append to existing filter

                if (this.filter.length < 3)
                    this.categories_to_show = this.all_categories.filter( cat => cat.name.toUpperCase().startsWith(this.filter) );
                else
                    this.categories_to_show = this.all_categories.filter( cat => cat.name.toUpperCase().includes(this.filter) );

                //this.categories_to_show = this.all_categories.filter( cat => cat.name[0] == l );
                //this.filter = l;
            },

            remove_filter()
            {
                this.categories_to_show = this.all_categories;
                this.filter = false;
            }

        }  // METHODS

    }
); // end component