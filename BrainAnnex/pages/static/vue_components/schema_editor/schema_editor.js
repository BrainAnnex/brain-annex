Vue.component('vue-schema-editor',
    {
        props: [],  <!-- NOTE:  Only lower cases in props names! -->
        /*  some_data_a:
            some_data_b:
         */

        template: `
            <div>  <!-- Outer container, serving as Vue-required template root.  OK to use a <section> instead -->

            <span class='title'>CREATE A NEW SCHEMA CLASS :</span><br><br>


            <table border='0' cellspacing='5' cellpadding='0'>
                <tr>
                    <td height="40px">Name</td>
                    <td style='padding-left:5px'><input type='text' v-model="new_class_name" size='30' maxlength='40'></td>
                </tr>

                <tr v-for="i in number_properties">
                    <td>Property {{i}}</td>
                    <td style='padding-left:5px'><input type='text'  v-model="property_list[i-1]" size='30' maxlength='40'></td>
                </tr>

                <tr>
                    <td colspan="2" align="right">
                        <img @click="number_properties++" src='/BA/pages/static/graphics/plus_green_32_41688.png'
                             alt='Add an extra property' title='Add an extra property'>
                    </td>
                </tr>
            </table>



            <br>
            <button @click="add_class()" v-bind:disabled="!new_class_name" style='padding: 15px'>
                <template v-if="new_class_name">
                    Add New "{{new_class_name}}" Class
                </template>
                <template v-else>
                  Must specify a Class name
                </template>
            </button>
                <span v-if="waiting" class="waiting">Adding the subcategory...</span>
                <span v-bind:class="{'error-message': error, 'status-message': !error }">{{status_message}}</span>
            <br><br>

            </div>		<!-- End of outer container -->
            `,



        data: function() {
            return {
                new_class_name: "",

                number_properties: 3,

                property_list: [],

                property_1: "",

                status_message: "",          // Message for the user about the status of the last operation (NOT used for "waiting" status)
                error: false,                // Whether the last server communication resulted in error
                waiting: false               // Whether any server request is still pending
            }
        },



        // ----------------  COMPUTED  -----------------
        computed: {

        },



        // ----------------  METHODS  -----------------
        methods: {
            add_class() {
                alert("add_class foo");     // . some_data_a= " + this.some_data_a);
            }

        }  // METHODS

    }
); // end component