from BrainAnnex.modules.media_manager.media_manager import MediaManager
from BrainAnnex.modules.full_text_indexing.full_text_indexing import FullTextIndexing
from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema
from typing import Set
import fitz                     # For PDF parsing
#from pypdf import PdfReader    # Alternate library for PDF parsing; currently not in use


class Documents:
    """
    Plugin-provided custom interface for "documents"
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
    def parse_pdf(cls, full_file_name :str) -> Set:
        """
        Using pyMupdf, parse the given PDF document, and extract all its text;
        then assemble and return a set of "non-trivial" unique words in the text

        :return:        A list of unique words
        """
        doc = fitz.open(full_file_name)     # Note: PyCharm complains about the "open" but it's fine

        unique_words = set()                # Running list of unique words across all pages

        for p_number in range(doc.page_count):
            page = doc.load_page(p_number)
            body = page.get_text(flags = fitz.TEXT_PRESERVE_WHITESPACE | fitz.TEXT_MEDIABOX_CLIP | fitz.TEXT_DEHYPHENATE)
            # TEXT_DEHYPHENATE re-forms any word that was split at the end of the line by hyphenation; not clear if the other flags are needed
            new_unique_words = FullTextIndexing.extract_unique_good_words(body)
            print(f"    Page {p_number} - PyMuPDF found {len(new_unique_words)} unique words: {new_unique_words}")

            unique_words = unique_words.union(new_unique_words)
            #print(f"--------------- unique_words_alt (size {len(unique_words_alt)}): ", unique_words_alt)

        return unique_words



    @classmethod
    def new_content_item_successful(cls, item_id: int, pars: dict, mime_type: str) -> None:
        """
        Invoked after a new Content Item of this type gets successfully added

        :param item_id:     An integer with the URI of the Content Item
        :param pars:        Dict with the various properties of this Content Item
        :param mime_type:   Standardize string representing the type of the document
                                EXAMPLES: 'text/plain', 'application/pdf'
        :return:            None
        """
        filename = pars["basename"] + "." + pars["suffix"]  # EXAMPLE: "my_file.txt"
        path = MediaManager.lookup_file_path(class_name="Documents")

        # Obtain the body of the document
        if mime_type == "text/plain":
            body = MediaManager.get_from_text_file(path, filename=filename)
            unique_words = FullTextIndexing.extract_unique_good_words(body)

        elif mime_type == "application/pdf":    # TODO: also include EPUB
            # TODO: this ought to be done in a separate thread
            full_file_name = path + filename

            unique_words = cls.parse_pdf(full_file_name)

            #print(f"\n  Found {len(unique_words)} unique words : {unique_words}\n")

            #TODO: also store in database the doc.page_count and non-trivial values in doc.metadata

        else:
            # TODO: handle mime_types such as 'application/msword'
            return


        n_words = len(unique_words)
        if n_words < 10:
            print(f"new_content_item_successful(): CREATING INDEXING for item {item_id}.  Found {n_words} unique words: {unique_words}")
        else:
            print(f"new_content_item_successful(): CREATING INDEXING for item {item_id}.  Found {n_words} unique words; first few: {list(unique_words)[:10]}")


        # Carry out the actual indexing
        content_id = NeoSchema.get_data_node_internal_id(item_id=item_id)
        FullTextIndexing.new_indexing(content_item_id=content_id, unique_words=unique_words)
        print("Documents.new_content_item_successful(): Completed the indexing")



    @classmethod
    def update_content_item_successful(cls, item_id: int, pars: dict) -> None:
        """
        Invoked after a Content Item of this type gets successfully updated

        :param item_id: An integer with the URI of the Content Item
        :param pars:
        :return:        None
        """
        pass    # Nothing to do
