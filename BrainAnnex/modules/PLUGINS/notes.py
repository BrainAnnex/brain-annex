from BrainAnnex.modules.media_manager.media_manager import MediaManager
from BrainAnnex.modules.full_text_indexing.full_text_indexing import FullTextIndexing
from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema


class Notes:
    """
    Plugin-provided handlers for "notes"  (HTML-formatted text)
    """

    @classmethod
    def delete_content_before(cls, uri: int) -> None:
        """
        Invoked just prior to deleting the data node

        :param uri: An integer with the URI ("item ID") of the Content Item
        :return:        None.  If index isn't found, an Exception is raised
        """
        #print(f"***** DELETING INDEXING for item {uri}")
        content_id = NeoSchema.get_data_node_internal_id(uri=uri)
        FullTextIndexing.remove_indexing(content_id)



    @classmethod
    def delete_content_successful(cls, uri: int) -> None:
        pass    # No action needed



    @classmethod
    def add_content(cls, uri: int, data_binding: dict) -> dict:
        """
        Special handling for Notes (ought to be specified in its Schema):
               the "body" value is to be stored in a file named "notes-ID.htm", where ID is the uri,
               and NOT be stored in the database.  Instead, store in the database:
                       basename: "notes-ID"
                       suffix: "htm"

        :param uri:     An integer with the URI of the Content Item
        :param data_binding:
        :return:            The altered data_binding dictionary.  In case of error, an Exception is raised.
        """
        # Save and ditch the "body" attribute - which is not to be stored in the database
        body = data_binding["body"]
        del data_binding["body"]

        # Create a file
        basename = f"notes-{uri}"
        suffix = "htm"
        filename = basename + "." + suffix
        print(f"Creating file named `{filename}`")
        #print("    File contents:")
        #print(body)
        MediaManager.save_into_file(body, filename)

        # Introduce new attributes, "basename" and "suffix", to be stored in the database
        data_binding["basename"] = basename
        data_binding["suffix"] = suffix

        return data_binding



    @classmethod
    def update_content(cls, data_binding: dict, set_dict: dict) -> dict:
        """
        Special handling for Notes (ought to be specified in its Schema):
        the "body" value is to be stored in a file named "notes-ID.htm", where ID is the uri,
        and NOT be stored in the database.  Instead, store in the database:
               basename: "notes-ID"
               suffix: "htm"

        :param data_binding:
        :param set_dict:
        :return:            The altered data_binding dictionary
        """
        body = data_binding["body"]
        uri = data_binding["uri"]


        # Overwrite the a file
        basename = f"notes-{uri}"
        filename = basename + ".htm"
        print(f"Overwriting file named `{filename}`")
        #print("    File contents:")
        #print(body)
        MediaManager.save_into_file(body, filename)

        # Ditch the "body" attribute - which is not to be stored in the database
        #del data_binding["body"]
        del set_dict["body"]
        # In its place, introduce 2 new attributes, "basename" and "suffix"
        #data_binding["basename"] = basename
        #data_binding["suffix"] = "htm"

        return set_dict



    @classmethod
    def new_content_item_successful(cls, uri: int, pars: dict) -> None:
        """
        Invoked after a new Content Item of this type gets successfully added

        :param uri: An integer with the URI of the Content Item
        :param pars:     Dict with the various properties of this Content Item
        :return:        None
        """
        body = pars.get("body")

        unique_words = FullTextIndexing.extract_unique_good_words(body)
        content_id = NeoSchema.get_data_node_internal_id(uri=uri)
        print(f"new_content_item_successful(): CREATING INDEXING for item {uri}. Words: {unique_words}")
        FullTextIndexing.new_indexing(content_uri=content_id, unique_words=unique_words)



    @classmethod
    def update_content_item_successful(cls, uri: int, pars: dict) -> None:
        """
        Invoked after a Content Item of this type gets successfully updated

        :param uri: An integer with the URI of the Content Item
        :param pars:     Dict with the various properties of this Content Item
        :return:        None
        """
        body = pars.get("body")

        unique_words = FullTextIndexing.extract_unique_good_words(body)
        content_id = NeoSchema.get_data_node_internal_id(uri=uri)
        print(f"update_content_item_successful(): UPDATING INDEXING for item {uri}. Words: {unique_words}")
        FullTextIndexing.update_indexing(content_uri=content_id, unique_words=unique_words)
