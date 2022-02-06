Vue.component('vue-category-navbox',
    {
        props: ['category_name', 'subcategories', 'all_categories'],
        /*  category_name:
            subcategories:
            all_categories:
         */

        my_optional_component_metadata: 123,   <!-- Available thru this.$options.metadata -->

        template: `
            <div>  <!-- Outer container, serving as Vue-required template root.  OK to use a <section> instead -->


                <!--
                    EXPANDED (normal) version of sidebox
                  -->
                <div v-show='show_sidebox'  class='sidebox'>
                <img v-on:click='show_sidebox = false'  src='/BA/pages/static/graphics/thin_left_arrow_32.png'
                     align='right' title='Click to collapse sidebox' alt='Click to collapse sidebox'>

                <span class="sidebox-section">PINNED</span>
                <br>&bull; <a href='/BA/pages/viewer/TBA' title="TBA">TBA</a>

                <hr>

                <span class="sidebox-section">RELATED</span>
                <br>
                <!-- All parent categories -->
                <span style='color:#BBBBBB; font-size:8px; font-style:italic'>Parent Categories:</span>
                <br>
                TBA
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

                <!-- All categories -->
                <span class="sidebox-section">ALL</span>
                <br>
                <template v-for="category in all_categories">
                    <br>&diams; <a v-bind:href="'/BA/pages/viewer/' + category['id']">{{category.name}}</a>
                </template>
                <br>
                <br>

                </div>  <!-- END of sidebox -->



                <!--
                    COLLAPSED version of sidebox
                  -->
                <div v-show='!show_sidebox' class='sidebox_collapsed' style='display:none'>
                <img v-on:click='show_sidebox = true'  src='/BA/pages/static/graphics/thin_right_arrow_32.png'
                     align='left' title='Click to expand sidebox' alt='Click to expand sidebox'>
                </div>  <!-- Collapsed version of sidebox -->


            </div>		<!-- End of outer container -->
            `,



        data: function() {
            return {
                show_sidebox: true  // Indicating whether to show or collapse the right sidebox (with the Category navigation)
            }
        },



        watch: {
        },



        mounted() {
           //console.log('The component is now mounted');
        },



        // ----------------  COMPUTED  -----------------
        computed: {
            example() {
            }
        },



        // ----------------  METHODS  -----------------
        methods: {
            foo() {
             }

        }  // METHODS

    }
); // end component