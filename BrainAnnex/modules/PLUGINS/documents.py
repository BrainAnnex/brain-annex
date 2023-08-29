from BrainAnnex.modules.media_manager.media_manager import MediaManager
from BrainAnnex.modules.full_text_indexing.full_text_indexing import FullTextIndexing
from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema


class Documents:
    """
    Plugin-provided handlers for "documents"
    """

    @classmethod
    def delete_content_before(cls, item_id: int) -> None:
        """
        Invoked just prior to deleting the data node

        :param item_id: An integer with the URI ("item ID") of the Content Item
        :return:        None.  If index isn't found, an Exception is raised
        """
        pass



    @classmethod
    def delete_content_successful(cls, item_id: int) -> None:
        pass    # No action needed



    @classmethod
    def add_content(cls, item_id: int, data_binding: dict) -> dict:
        """

        :param item_id:     An integer with the URI of the Content Item
        :param data_binding:
        :return:            The altered data_binding dictionary.  In case of error, an Exception is raised.
        """
        pass


    @classmethod
    def update_content_NOT_SUPPORTED(cls, data_binding: dict, set_dict: dict) -> dict:
        """

        :param data_binding:
        :param set_dict:
        :return:            The altered data_binding dictionary
        """

        return {}



    @classmethod
    def new_content_item_successful(cls, item_id: int, pars: dict, mime_type: str) -> None:
        """
        Invoked after a new Content Item of this type gets successfully added

        :param item_id:     An integer with the URI of the Content Item
        :param pars:        Dict with the various properties of this Content Item
        :param mime_type:   Standardize string representing the type of the document
        :return:            None
        """
        filename = pars["basename"] + "." + pars["suffix"]
        path = MediaManager.lookup_file_path(class_name="Documents")

        # Obtain the body of the document
        if mime_type == "text/plain":
            body = MediaManager.get_from_text_file(path, filename=filename)
        else:
            # TODO: handle mime_types 'application/pdf' and 'application/msword'
            return

        unique_words = FullTextIndexing.extract_unique_good_words(body)
        content_id = NeoSchema.get_data_node_internal_id(item_id=item_id)
        print(f"new_content_item_successful(): CREATING INDEXING for item {item_id}. Words: {unique_words}")
        FullTextIndexing.new_indexing(content_item_id=content_id, unique_words=unique_words)



    @classmethod
    def update_content_item_successful(cls, item_id: int, pars: dict) -> None:
        """
        Invoked after a Content Item of this type gets successfully updated

        :param item_id: An integer with the URI of the Content Item
        :param pars:
        :return:        None
        """
        pass    # Nothing to do
