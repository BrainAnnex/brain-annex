from brainannex.media_manager import MediaManager
from brainannex.full_text_indexing import FullTextIndexing
from brainannex.neo_schema.neo_schema import NeoSchema


class Notes:
    """
    Plugin-provided handlers for "notes"  (HTML-formatted text)
    """

    @classmethod
    def delete_content_before(cls, uri :str) -> None:
        """
        Invoked just prior to deleting the data node

        :param uri: A string with the URI ("item ID") of the Content Item
        :return:    None.  If index isn't found, an Exception is raised
        """
        #print(f"***** DELETING INDEXING for item {uri}")
        # TODO: maybe the Core can take care of this,
        #       for all Content Items that make use of word indexing
        content_id = NeoSchema.get_data_node_internal_id(uri=uri)
        FullTextIndexing.remove_indexing(content_id)



    @classmethod
    def delete_content_successful(cls, uri :str) -> None:
        pass    # No action needed



    @classmethod
    def add_content(cls, uri :str, data_binding: dict) -> dict:
        """
        Special handling for Notes (ought to be specified in its Schema):
               the "body" value is to be stored in a file named "notes-ID.htm", where ID is the uri,
               and NOT be stored in the database.  Instead, store in the database:
                       basename: "notes-ID"
                       suffix: "htm"

        :param uri:         A string with the URI of the Content Item
        :param data_binding:
        :return:            The altered data_binding dictionary.  In case of error, an Exception is raised.
        """
        # Save and ditch the "body" attribute - which is not to be stored in the database
        body = data_binding["body"]
        del data_binding["body"]

        # Create a file
        basename = f"notes-{uri}"   # TODO: change this convention
                                    #       also needs changing in notes.js
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
    def before_update_content(cls, data_binding :dict, set_dict :dict) -> dict:
        """
        Invoked before a Content Item of this type gets updated in the database

        Special handling for Notes:
        the "body" value is to be stored in an HTML file,
        and NOT be stored in the database.
        What's stored in the database are the basename and suffix (extension) of the file;
        EXAMPLE:
               basename: "n-123"
               suffix: "htm"

        :param data_binding:    A dict with various metadata fields
        :param set_dict:        A dict of field values to eventually set into the database
        :return:                The altered data_binding dictionary
        """
        # TODO: perhaps a special handling of a "body" for media-based Content Items
        #       could be a standard service by the Core module, based on a Schema spec
        body = data_binding["body"]
        basename = data_binding["basename"]

        #uri = data_binding["uri"]

        if basename == "undefined":
            raise Exception("before_update_content(): got passed the value 'undefined' "
                            "for the `basename` key")

        # Overwrite the HTML file with the body of the notes
        #basename = f"notes-{uri}"      # Old hack!
        filename = basename + ".htm"
        print(f"Overwriting file named `{filename}`")
        #print("    File contents:")
        #print(body)
        MediaManager.save_into_file(body, filename)

        # Ditch the "body" attribute - which is not to be stored in the database
        #del data_binding["body"]
        del set_dict["body"]

        return set_dict



    @classmethod
    def new_content_item_successful(cls, uri :str, pars: dict) -> None:
        """
        Invoked after a new Content Item of this type gets successfully added

        :param uri:     A string with the URI of the Content Item
        :param pars:    Dict with the various properties of this Content Item
        :return:        None
        """
        body = pars.get("body")

        # TODO: do in separate thread or process
        # TODO: maybe the Core can take care of this,
        #       for all Content Items that make use of word indexing
        unique_words = FullTextIndexing.extract_unique_good_words(body)
        content_id = NeoSchema.get_data_node_internal_id(uri=uri)
        n_words = len(unique_words)
        print(f"new_content_item_successful(): CREATING INDEXING for item `{uri}`. "
              f"Found {n_words} unique words; first few: {list(unique_words)[:10]}")
        FullTextIndexing.new_indexing(internal_id=content_id, unique_words=unique_words)



    @classmethod
    def update_content_item_successful(cls, uri :str, pars :dict) -> None:
        """
        Invoked after a Content Item of this type gets successfully updated in the database

        :param uri:     A string with the URI of the Content Item
        :param pars:    Dict with the various properties of this Content Item
        :return:        None
        """
        body = pars.get("body")

        # TODO: do in separate thread or process
        # TODO: maybe the Core can take care of this,
        #       for all Content Items that make use of word indexing
        unique_words = FullTextIndexing.extract_unique_good_words(body)
        content_id = NeoSchema.get_data_node_internal_id(uri=uri)
        n_words = len(unique_words)
        print(f"update_content_item_successful(): UPDATING INDEXING for item `{uri}`. "
              f"Found {n_words} unique words; first few: {list(unique_words)[:10]}")
        FullTextIndexing.update_indexing(content_uri=content_id, unique_words=unique_words)
