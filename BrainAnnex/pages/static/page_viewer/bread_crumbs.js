/*  MIT License.  Copyright (c) 2021 Julian A. West
 */

Vue.component('vue-bread-crumbs',
    {
        props: ['category_id', 'bread_crumbs'],
        /*  bread_crumbs:
         */

        template: `
            <div v-html="generate_breadcrumbs_html(bread_crumbs)">	<!-- Outer container box, serving as Vue-required template root  -->

            </div>		<!-- End of outer container box -->
            `,


        data: function() {
            return {

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
                    //console.log("-- CHECKING ITEM TYPE --");
                    //console.log(item);
                    //console.log(typeof item);
                    if ((typeof item) == "string")  {
                        //console.log("Processing a string");
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
                        else
                            bread_crumbs_str += " [UNKNOWN BREAD CRUMB ELEMENT - try refreshing page!] ";
                    }
                    else if ((typeof item) == "number")  {
                        //console.log("Processing a number");
                        if (item == this.category_id)
                            bread_crumbs_str += `<span class='br_nav'>${item}</span>`;
                        else
                            bread_crumbs_str += `<span class='br_nav'><a href='${item}'>${item}</a></span>`;
                    }
                    else
                        bread_crumbs_str += this.generate_breadcrumbs_html(item);      // Recursive call
                }

                //console.log(`returning ${bread_crumbs_str}`);
                return bread_crumbs_str;
            }

        }  // METHODS

    }
); // end component