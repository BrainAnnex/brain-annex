/*  Vue component to display and edit Content Items of type "Image Gallery"
 */

Vue.component('vue-plugin-image-gallery',
    {
        props: ['item_fields', 'item_metadata',
                'edit_mode', 'category_id', 'index', 'item_count']
        /*  item_fields:    An object with the editable properties of this Image Gallery item.
                                EXAMPLE: {}

            item_metadata:  An object with the metadata of this Image Gallery item.
                                For a newly-created Content Item, not yet registered with the server,
                                the value of `entity_id` will be a negative number (unique on the page),
                                and there will be the additional keys `insert_after_uri` and `insert_after_class`
                                EXAMPLE of existing Image Gallery item:
                                        {"class_name":"Image Gallery",
                                        "pos":0,
                                        "schema_code":"timer",
                                        "entity_id":"8809"
                                        }

         */

    }
); // end component