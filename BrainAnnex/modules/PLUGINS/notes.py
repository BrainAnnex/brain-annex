import re
import html
from BrainAnnex.modules.media_manager.media_manager import MediaManager


class Notes:

    TAG_RE = re.compile(r'<[^>]+>')     # Used to strip off all HTML



    @classmethod
    def plugin_n_add_content(cls, item_id: int, data_binding: dict) -> dict:
        """
        Special handling for Notes (ought to be specified in its Schema):
               the "body" value is to be stored in a file named "notes-ID.htm", where ID is the item_id,
               and NOT be stored in the database.  Instead, store in the database:
                       basename: "notes-ID"
                       suffix: "htm"

        :return: The altered data_binding dictionary.  In case of error, an Exception is raised.
        """
        # Save and ditch the "body" attribute - which is not to be stored in the database
        body = data_binding["body"]
        del data_binding["body"]

        # Create a file
        basename = f"notes-{item_id}"
        suffix = "htm"
        filename = basename + "." + suffix
        print(f"Creating file named `{filename}`, with contents:")
        print(body)
        MediaManager.save_into_file(body, filename)

        # Introduce new attributes, "basename" and "suffix", to be stored in the database
        data_binding["basename"] = basename
        data_binding["suffix"] = suffix

        return data_binding



    @classmethod
    def plugin_n_update_content(cls, data_binding: dict, set_dict: dict) -> dict:
        """
        Special handling for Notes (ought to be specified in its Schema):
               the "body" value is to be stored in a file named "notes-ID.htm", where ID is the item_id,
               and NOT be stored in the database.  Instead, store in the database:
                       basename: "notes-ID"
                       suffix: "htm"

        :return: The altered data_binding dictionary
        """
        body = data_binding["body"]
        item_id = data_binding["item_id"]


        # Overwrite the a file
        basename = f"notes-{item_id}"
        filename = basename + ".htm"
        print(f"Overwriting file named `{filename}`, with contents:")
        print(body)
        MediaManager.save_into_file(body, filename)

        # Ditch the "body" attribute - which is not to be stored in the database
        #del data_binding["body"]
        del set_dict["body"]
        # In its place, introduce 2 new attributes, "basename" and "suffix"
        #data_binding["basename"] = basename
        #data_binding["suffix"] = "htm"

        return set_dict




    @classmethod
    def new_content_item_in_category_SUCCESSFUL(cls, item_id: int, pars: dict) -> None:
        cls.index_note_contents(item_id, pars)


    @classmethod
    def update_content_item_SUCCESSFUL(cls, item_id: int, pars: dict) -> None:
        cls.index_note_contents(item_id, pars)



    ############    INDEXING-RELATED METHODS (TODO: eventually move to own module)    ############
    @classmethod
    def index_note_contents(cls, item_id: int, pars: dict) -> None:
        """

        :param item_id:
        :param pars:
        :return:        None
        """
        body = pars.get("body")
        if body is None:
            raise Exception("The notes plugin in unable to index the contents because none were passed")

        # printing original string
        print("The original string is : " +  body)

        # Extract words from string
        res = cls.split_into_words(body)

        # printing result
        print("The list of words is : ", res)

        # TODO: Continue the indexing



    @classmethod
    def split_into_words(cls, text: str) ->[str]:
        """
        Zap HTML, HTML entities (such as &ndash;) and punctuation; then, break up into individual words.

        Care is taken to make sure that the stripping of special characters does NOT fuse words together;
        e.g. avoid turning 'Long&ndash;Term' into a single word as 'LongTerm';
        likewise, avoid turning 'One<br>Two' into a single word as 'OneTwo'

        EXAMPLE demonstrated in the code, below:
            '<p>Mr. Joe&amp;sons<br>A Long&ndash;Term business! Find it at &gt; (http://example.com/home)<br>Visit Joe&#39;s &quot;NOW!&quot;</p>'

        :param text:    A string with the text to parse
        :return:        A list of words in the text, free of punctuation, HTML and HTML entities (such as &ndash;)
        """
        unescaped_text = html.unescape(text)
        #print(unescaped_text)  # <p>Mr. Joe&sons<br>A Long–Term business! Find it at > (http://example.com/home)<br>Visit Joe's "NOW!"</p>

        stripped_text = cls.TAG_RE.sub(' ', unescaped_text)
        #print(stripped_text)   # Mr. Joe&sons A Long–Term business! Find it at > (http://example.com/home) Visit Joe's "NOW!"

        result = re.findall(r'\w+', stripped_text)
        # EXAMPLE:  ['Mr', 'Joe', 'sons', 'A', 'Long', 'Term', 'business', 'Find', 'it', 'at', 'http', 'example', 'com', 'home', 'Visit', 'Joe', 's', 'NOW']
        return result
