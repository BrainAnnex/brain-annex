/*  To provide a "bread crumbs" navigation strip at the top of category-viewer pages
 */

Vue.component('vue-bread-crumbs',
    {
        props: ['category_uri', 'bread_crumbs', 'all_categories'],
        /*  category_uri:       EXAMPLE: "123"
            bread_crumbs:       EXAMPLE: ['START_CONTAINER', ['1', 'ARROW', '544'], 'END_CONTAINER']
            all_categories:     EXAMPLE: [{"uri": "1", "name": "HOME", "remarks": "ROOT NODE"},
                                          {"uri": "523", "name": "work", 'pinned': True}]
         */

        template: `
            <div v-html="generate_breadcrumbs_html(bread_crumbs)">	<!-- Outer container box, serving as Vue-required template root  -->

            </div>		<!-- End of outer container box -->
            `,


        data: function() {
            return {
                 category_map: this.create_category_map()   // TODO: let this be handled by the Vue root, and passed as a prop
            }
        }, // data


        // ---------------------------  METHODS  ---------------------------
        methods: {
            generate_breadcrumbs_html(bread_crumbs_list)
            // Returns HTML
            {
                let bread_crumbs_str = "";

                for (let i = 0; i < bread_crumbs_list.length; i++) {
                    let item = bread_crumbs_list[i];
                    //console.log(item);
                    //console.log(typeof item);
                    if ((typeof item) == "string")  {
                        //console.log("Processing a string");
                        // First, consider whether the item is a special token
                        if (item == "START_CONTAINER")
                            bread_crumbs_str += "<div class='br_container'>";
                        else if (item == "END_CONTAINER")
                            bread_crumbs_str += "</div>";
                        else if (item == "START_BLOCK")
                            bread_crumbs_str += "<div class='br_block'>";
                        else if (item == "END_BLOCK")
                            bread_crumbs_str += "</div>";
                        else if (item == "START_LINE")
                            bread_crumbs_str += "<div class='br_line'>";
                        else if (item == "END_LINE")
                            bread_crumbs_str += "</div>";
                        else if (item == "CLEAR_RIGHT")
                            bread_crumbs_str += "<div style='clear:right'></div>";
                        else if (item == "ARROW")
                            bread_crumbs_str += " &raquo; ";
                        // If we get thus far, the item is regarded to be a Category URI
                        // NOTE: in principle, there's a risk that a URI could be equal to one of the tokens...
                        else if (item == this.category_uri)
                            bread_crumbs_str += `<span class='br_nav'>${this.category_map[item][0]}</span>`;
                        else
                            bread_crumbs_str += `<span class='br_nav'><a href='${item}' title='${this.category_map[item][1]}'>${this.category_map[item][0]}</a></span>`;
                    }
                    else   // If it's a list, we'll end up here
                        bread_crumbs_str += this.generate_breadcrumbs_html(item);      // Recursive call
                }

                //console.log(`returning ${bread_crumbs_str}`);
                return bread_crumbs_str;
            },



            create_category_map()
            // TODO: this seems overkill for just the bread crumbs, but may come in handy for multiple uses if moved to the Vue root
            /*  Create and return an object to map Category URI's to the pairs [Category name, remarks]
                EXAMPLE:  {
                                "1": ["HOME", "ROOT NODE"],
                                "123": ["Work", ""]
                          }
                Note that the keys are strings, not integers
             */
            {
                let category_map = {}
                for (let i in this.all_categories) {   // Note:  i will be an integer, not an array element!
                    let category_data = this.all_categories[i];
                    let key_int = category_data.uri;
                    let key_str = key_int.toString();

                    if ('remarks' in category_data)
                        category_map[key_str] = [category_data.name, category_data.remarks];
                    else
                        category_map[key_str] = [category_data.name, ""];   // If the `remarks` attribute isn't present
                }
                //console.log(category_map);

                return category_map;
            }

        }  // METHODS

    }
); // end component