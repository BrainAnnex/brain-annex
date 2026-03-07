class Utilities
{

    static find_item_by_uri(entity_id, content_array)
    /*  Locate the specified object, identified by its entity_id property,
        in the given array of objects.
        If found, return its index in the array; otherwise, return -1
        (No check is done as to whether there might be more than one match; the first one is returned.)
        TODO: consider using Lodash library (https://lodash.com/docs/4.17.15#findIndex)
     */
    {
        //console.log(`Attempting to locate content item with entity_id "${entity_id}"`);

        for (var i = 0; i < content_array.length; i++) {
            if (content_array[i].entity_id == entity_id)
                return i;          //  Found it
        }

        return -1;    // Didn't find it
    }

}