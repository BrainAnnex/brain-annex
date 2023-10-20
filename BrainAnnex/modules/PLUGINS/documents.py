from BrainAnnex.modules.media_manager.media_manager import MediaManager
from BrainAnnex.modules.full_text_indexing.full_text_indexing import FullTextIndexing
from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema
import fitz                     # For PDF parsing
from pypdf import PdfReader     # For PDF parsing


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

            doc = fitz.open(full_file_name)     # Using pymupdf
            reader = PdfReader(full_file_name)  # Using pypdf

            unique_words = set()        # Running list over all pages
            for p_number in range(doc.page_count):
                page = doc.load_page(p_number)
                body = page.get_text(flags = fitz.TEXT_PRESERVE_WHITESPACE | fitz.TEXT_MEDIABOX_CLIP | fitz.TEXT_DEHYPHENATE)
                # TEXT_DEHYPHENATE re-forms any word that was split at the end of the line by hyphenation; not clear if the other flags are needed
                new_unique_words = FullTextIndexing.extract_unique_good_words(body)
                print(f"    Page {p_number} - PyMuPDF found {len(new_unique_words)} unique words: {new_unique_words}")

                # Repeat, with pypdf
                p = reader.pages[p_number]
                s = p.extract_text()
                body_alt = s.replace("-\n", "")     # A more sophisticated dehyphenate could be used, if needed
                                                    # For example, as shown in https://pypdf.readthedocs.io/en/stable/user/post-processing-in-text-extraction.html
                ligatures = {
                    "ﬀ": "ff",
                    "ﬁ": "fi",
                    "ﬂ": "fl",
                    "ﬃ": "ffi",
                    "ﬄ": "ffl",
                    "ﬅ": "ft",
                    "ﬆ": "st",
                    # "Ꜳ": "AA",
                    # "Æ": "AE",
                    "ꜳ": "aa",
                }
                for search, replace in ligatures.items():
                    body_alt = body_alt.replace(search, replace)

                new_unique_words_alt = FullTextIndexing.extract_unique_good_words(body_alt)
                diff1 = new_unique_words_alt - new_unique_words
                diff2 = new_unique_words - new_unique_words_alt
                if diff1 != set():
                    print(f"    ************** DISCREPANCY: words found by pypdf but missing in PyMuPDF : {diff1}\n")
                if diff2 != set():
                    print(f"    ************** DISCREPANCY: words found by PyMuPDF but missing in pypdf : {diff2}\n")


                unique_words = unique_words.union(new_unique_words)


            #TODO: also store in database the doc.page_count and non-trivial values in doc.metadata

        else:
            # TODO: handle mime_types such as 'application/msword'
            return


        content_id = NeoSchema.get_data_node_internal_id(item_id=item_id)

        n_words = len(unique_words)
        if n_words < 100000:    # TODO: restore to 10
            print(f"new_content_item_successful(): CREATING INDEXING for item {item_id}.  Found {n_words} unique words: {unique_words}")
        else:
            print(f"new_content_item_successful(): CREATING INDEXING for item {item_id}.  Found {n_words} unique words; first few: {list(unique_words)[:10]}")

        # Carry out the actual indexing
        #FullTextIndexing.new_indexing(content_item_id=content_id, unique_words=unique_words)   # *** TODO: RESTORE!!!!!!!!!!! ***********
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
