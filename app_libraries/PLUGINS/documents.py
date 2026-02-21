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
    COVERS_FOLDER = "_covers/"      # TODO: for now, this must be matched to BA_api_routing.py


    @classmethod
    def default_folder(cls):
        """
        Specify the desired name for the default subfolder (of the media folder) to contain document media
        """
        return "documents"



    @classmethod
    def add_to_schema(cls) -> None:
        """
        Create, as needed, the database Schema needed by this plugin

        :return:    None
        """
        assert GraphSchema.is_valid_class_name(cls.SCHEMA_CLASS_NAME), \
            f"initialize_schema(): attempting to create a Schema Class with an invalid name: '{cls.SCHEMA_CLASS_NAME}'"

        if not GraphSchema.class_name_exists("Media") or not GraphSchema.class_name_exists("Directory"):
            MediaManager.add_to_schema()

        if not GraphSchema.class_name_exists(cls.SCHEMA_CLASS_NAME):
            GraphSchema.create_class_with_properties(name=cls.SCHEMA_CLASS_NAME, strict=False, code="d",  handler="documents",
                                                 properties=["caption", "date_created", "url", "comments", "year", "month", "read", "rating", "authors"],
                                                 class_to_link_to="Media", link_name="INSTANCE_OF", link_dir="OUT")


        # Take care of Indexing

        if not GraphSchema.class_name_exists("Indexer"):
            FullTextIndexing.add_to_schema()

        if not GraphSchema.class_relationship_exists(from_class=cls.SCHEMA_CLASS_NAME, to_class="Indexer", rel_name="has_index"):
            GraphSchema.create_class_relationship(from_class=cls.SCHEMA_CLASS_NAME, to_class="Indexer", rel_name="has_index")




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
    def before_update_content(cls, entity_id :str, item_data :dict) -> dict:
        """
        Invoked before a Document's metadata gets updated in the database

        :param entity_id:   String with a unique identifier (within the given Class) for the Content Item to update
        :param item_data:   A dict with various fields for this Document
        :return:            Just pass thru the `item_data` dictionary
        """
        print(f"In Documents.before_update_content() - entity_id: `{entity_id}` | item_data: {item_data}")
        new_basename = item_data.get("basename")
        new_suffix =   item_data.get("suffix")

        folder, old_basename, old_suffix = \
                MediaManager.get_media_item_file(class_name=cls.SCHEMA_CLASS_NAME, entity_id=entity_id)

        print(f"folder: {folder}, old_basename: {old_basename}, old_suffix: {old_suffix}")

        MediaManager.rename_media_file(folder=folder,
                                       old_basename=old_basename, old_suffix=old_suffix,
                                       new_basename=new_basename, new_suffix=new_suffix)

        # Also rename the cover image (always a jpg file), if present
        # TODO: in case of failure, catch error and restore old name of main file,
        #       prior to throwing an Exception
        MediaManager.rename_media_file(folder=folder+cls.COVERS_FOLDER,
                                       old_basename=old_basename, old_suffix="jpg",
                                       new_basename=new_basename,
                                       ignore_missing=True)

        return item_data



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
    def new_content_item_successful(cls, uri :str, pars :dict,
                                    mime_type :str, upload_folder :str, index_pdf=True) -> None:
        """
        Invoked after a new Content Item of this type (Document) gets successfully added to the database.
        Only text and PDF are currently supported.

        :param uri:         A string with the URI of the Content Item
        :param pars:        Dict with the various properties of this Content Item
                                For Document, "basename" and "suffix" keys are expected
        :param mime_type:   Standardized string representing the type of the document
                                EXAMPLES: 'text/plain', 'application/pdf'
        :param upload_folder:If an empty string or None, it means the default folder for Document;
                                otherwise, it's the name of the folder where this Document was uploaded
                                (*exclusive* of the common path and of the final "/")
                                EXAMPLE: 'documents/Ebooks & Articles'
        :param index_pdf:       [OPTIONAL] If True (default), the contents of PDF files will be indexed
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
            if not index_pdf:
                print("new_content_item_successful(): PDF file will NOT get indexed, as requested")
                return
                
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
        content_id = GraphSchema.get_data_node_internal_id(class_name=cls.SCHEMA_CLASS_NAME, entity_id=uri)

        # TODO: this ought to be done in a separate execution thread or process
        FullTextIndexing.new_indexing(internal_id=content_id, unique_words=unique_words)

        print("Documents.new_content_item_successful(): Completed the indexing")



    @classmethod
    def update_content_item_successful(cls, entity_id :str, pars: dict) -> None:
        """
        Invoked after a Content Item of this type gets successfully updated

        :param entity_id:   A string to identify this Document
        :param pars:        Dict with the various properties of this Content Item
        :return:            None
        """
        pass    # Nothing to do



    @classmethod
    def api_endpoint(cls, parameters):
        """
        EXPERIMENTAL : not in current use.

        Optional function to provide web API endpoint management for this plugin

        :param parameters:  Data that was passed to the web API endpoint for this plugin
        :return:
        """
        print("In Documents.api_endpoint().  parameters: ", parameters)
        return "ok"
