from app_libraries.media_manager import MediaManager
from brainannex import GraphSchema, FullTextIndexing
from typing import Set
import fitz                     # For PDF parsing
#from pypdf import PdfReader    # Alternate library for PDF parsing; currently not in use


class Documents:
    """
    Plugin-provided custom interface for "documents"
    """

    SCHEMA_CLASS_NAME = "Document"


    @classmethod
    def default_folder(cls):
        """
        Specify the desired name for the default subfolder (of the media folder) to contain document media
        """
        return "documents"



    @classmethod
    def add_to_schema(cls) -> None:
        """
        Initialize the Schema needed by this plugin

        :return:    None
        """
        pass    # TODO: follow the example in Images



    @classmethod
    def delete_content_before(cls, uri: int) -> None:
        """
        Invoked just prior to deleting the data node

        :param uri: An integer with the URI ("item ID") of the Content Item
        :return:    None.  If index isn't found, an Exception is raised
        """
        pass    # No action needed



    @classmethod
    def delete_content_successful(cls, uri: int) -> None:
        pass    # No action needed



    @classmethod
    def add_content(cls, uri: int, data_binding: dict) -> dict:
        """

        :param uri:         An integer with the URI of the Content Item
        :param data_binding:
        :return:            The altered data_binding dictionary.  In case of error, an Exception is raised.
        """
        pass    # No action needed



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

            '''
            n_words = len(new_unique_words)
            if n_words < 10:    # Give a more verbose feedback
                print(f"    Page {p_number} - PyMuPDF found {n_words} unique words: {new_unique_words}")
            else:               # Give abridged feedback
                print(f"    Page {p_number} - PyMuPDF found {n_words} unique words; first few: {list(new_unique_words)[:10]}")
            '''
            unique_words = unique_words.union(new_unique_words)
            #print(f"--------------- unique_words_alt (size {len(unique_words_alt)}): ", unique_words_alt)

        return unique_words



    @classmethod
    def new_content_item_successful(cls, uri :str, pars :dict, mime_type :str, upload_folder :str) -> None:
        """
        Invoked after a new Content Item of this type (Document) gets successfully added to the database

        :param uri:         A string with the URI of the Content Item
        :param pars:        Dict with the various properties of this Content Item
                                For Document, "basename" and "suffix" keys are expected
        :param mime_type:   Standardized string representing the type of the document
                                EXAMPLES: 'text/plain', 'application/pdf'
        :param upload_folder:If an empty string or None, it means the default folder for Document;
                                otherwise, it's the name of the folder where this Document was uploaded
                                (*exclusive* of the common path and of the final "/")
                                EXAMPLE: 'documents/Ebooks & Articles'
        :return:            None
        """
        filename = pars["basename"] + "." + pars["suffix"]      # EXAMPLE: "my_file.txt"

        if not upload_folder:     # Document was uploaded to standard location
            path = MediaManager.retrieve_full_path(uri=uri)         # Incl. the final "/"
        else:
            # Link the new document to its specific directory node
            q = '''
                MATCH (doc :Document {uri: $uri}),
                      (dir :Directory {name: $upload_folder}) 
                MERGE (doc)-[:BA_stored_in]->(dir)
                '''
            #GraphSchema.db.debug_query_print(q, data_binding={"uri": uri, "upload_folder": upload_folder})
            GraphSchema.db.query(q, data_binding={"uri": uri, "upload_folder": upload_folder})
            path = MediaManager.MEDIA_FOLDER + upload_folder + "/"


        # Extract the individual words "worthy" of being indexed in the document
        full_file_name = path + filename

        if mime_type == "text/plain":
            body = MediaManager.get_from_text_file(full_file_name)
            unique_words = FullTextIndexing.extract_unique_good_words(body)

        elif mime_type == "application/pdf":    # TODO: also include EPUB
            unique_words = cls.parse_pdf(full_file_name)
            #TODO: also store in database the doc.page_count and non-trivial values in doc.metadata

        else:
            # TODO: handle other mime_types such as 'application/msword'
            return


        n_words = len(unique_words)
        if n_words < 10:    # Give a more verbose feedback
            print(f"new_content_item_successful(): CREATING INDEXING for document `{uri}`.  "
                  f"Found {n_words} unique words: {unique_words}")
        else:               # Give abridged feedback
            print(f"new_content_item_successful(): CREATING INDEXING for document `{uri}`.  "
                  f"Found {n_words} unique words; first few: {list(unique_words)[:10]}")


        # Carry out the actual indexing in the database
        content_id = GraphSchema.get_data_node_internal_id(uri=uri)

        # TODO: this ought to be done in a separate execution thread or process
        FullTextIndexing.new_indexing(internal_id=content_id, unique_words=unique_words)

        print("Documents.new_content_item_successful(): Completed the indexing")



    @classmethod
    def update_content_item_successful(cls, uri: int, pars: dict) -> None:
        """
        Invoked after a Content Item of this type gets successfully updated

        :param uri: An integer with the URI of the Content Item
        :param pars:Dict with the various properties of this Content Item
        :return:    None
        """
        pass    # Nothing to do
