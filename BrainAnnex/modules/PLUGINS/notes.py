import re
import html
from BrainAnnex.modules.media_manager.media_manager import MediaManager


class Notes:


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
        print(f"Creating file named `{filename}`")
        #print("    File contents:")
        #print(body)
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
    def new_content_item_in_category_SUCCESSFUL(cls, item_id: int, pars: dict) -> None:
        """

        :param item_id:
        :param pars:
        :return:
        """
        body = pars.get("body")
        FullTextIndexing.index_text(body)


    @classmethod
    def update_content_item_SUCCESSFUL(cls, item_id: int, pars: dict) -> None:
        """

        :param item_id:
        :param pars:
        :return:
        """
        body = pars.get("body")
        FullTextIndexing.index_text(body)




###################################################################################################################

class FullTextIndexing:
    """
    Indexing-related methods
    """

    TAG_RE = re.compile(r'<[^>]+>')         # Used to strip off all HTML

    # List of common English words to skip from indexing (stopword list)
    # See https://github.com/Alir3z4/stop-words
    # TODO: allow over-ride in config file
    COMMON_WORDS = ['and', 'or', 'either', 'nor', 'neither',
                    'the', 'an', 'with', 'without', 'within',
                    'in', 'on', 'at', 'of', 'from', 'to', 'into', 'not', 'but', 'by',
                    'if', 'whether', 'then', 'else',
                    'me', 'my', 'mine', 'he', 'she', 'it', 'him', 'his', 'her', 'its',
                    'we', 'our', 'you', 'your', 'yours', 'they', 'them', 'their',
                    'why', 'because', 'since', 'how', 'for', 'both', 'indeed',
                    'help', 'helps', 'let', 'lets',
                    'go', 'goes', 'going', 'gone', 'became', 'become',
                    'be', 'is', 'isn', 'am', 'are', 'aren', 'been', 'was', 'wasn',
                    'can', 'could', 'might', 'may', 'do', 'does', 'did', 'didn', 'done', 'make', 'made', 'making',
                    'have', 'haven', 'has', 'had', 'hadn', 'having',
                    'must', 'need', 'seem', 'seems', 'want', 'wants', 'should', 'shouldn',
                    'will', 'would',
                    'get', 'gets', 'got',
                    'ask', 'asks', 'answer', 'answers',
                    'when', 'where', 'which', 'who', 'why', 'what',
                    'no', 'yes', 'maybe', 'ok', 'oh',
                    'll', 've', 'hr', 'ie', 'so', 'min',
                    'good', 'better', 'best', 'great', 'well', 'bad',  'worse', 'worst',
                    'just', 'about', 'above', 'again', 'ago',
                    'times', 'date', 'dates', 'today', 'day', 'month', 'year', 'days', 'months', 'years',
                    'after', 'before', 'yet', 'whenever', 'while', 'ever', 'never', 'often', 'sometimes', 'occasionally',
                    'old', 'older', 'new', 'newer', 'begin', 'began',
                    'up', 'down', 'over', 'above', 'under', 'below', 'between', 'wherever',
                    'next', 'previous', 'other', 'thing', 'things',
                    'like', 'as', 'fairly',
                    'each', 'any', 'all', 'some', 'more', 'most', 'less', 'least', 'than',
                    'full', 'empty', 'lot', 'very',
                    'part', 'parts', 'wide', 'narrow', 'side',
                    'hence', 'therefore', 'whereas',
                    'whom', 'whoever', 'whose',
                    'this', 'that',
                    'too', 'also',
                    'related', 'issues', 'issue',
                    'com', 'www',
                    'one', 'two']



    @classmethod
    def index_text(cls, text: str) -> None:
        """

        :param text:   A string with the text to analyze and index
        :return:       None
        """

        if text is None:
            raise Exception("FullTextIndexing: unable to index the contents because none were passed")

        #print("The original string is : \n" +  text)

        # Extract words from string
        split_text = cls.split_into_words(text)
        #print("The split text is : ", split_text)

        word_list = []


        for word in split_text:
            if len(word) > 1 \
                    and not word.isnumeric() \
                    and word not in cls.COMMON_WORDS \
                    and word not in word_list:
                word_list.append(word)

        print("The word list for the index is: ", word_list)


        # TODO: Continue the indexing



    @classmethod
    def split_into_words(cls, text: str, to_lower_case=True) ->[str]:
        """
        Zap HTML, HTML entities (such as &ndash;) and punctuation; then, break up into individual words.

        Care is taken to make sure that the stripping of special characters does NOT fuse words together;
        e.g. avoid turning 'Long&ndash;Term' into a single word as 'LongTerm';
        likewise, avoid turning 'One<br>Two' into a single word as 'OneTwo'

        EXAMPLE demonstrated in the code, below:
            '<p>Mr. Joe&amp;sons<br>A Long&ndash;Term business! Find it at &gt; (http://example.com/home)<br>Visit Joe&#39;s &quot;NOW!&quot;</p>'

        :param text:            A string with the text to parse
        :param to_lower_case:   If True, all text is converted to lower case
        :return:                A list of words in the text,
                                    free of punctuation, HTML and HTML entities (such as &ndash;)
        """
        unescaped_text = html.unescape(text)
        #print(unescaped_text)  # <p>Mr. Joe&sons<br>A Long–Term business! Find it at > (http://example.com/home)<br>Visit Joe's "NOW!"</p>

        stripped_text = cls.TAG_RE.sub(' ', unescaped_text)
        #print(stripped_text)   # Mr. Joe&sons A Long–Term business! Find it at > (http://example.com/home) Visit Joe's "NOW!"

        if to_lower_case:
            stripped_text = stripped_text.lower()   # If requested, turn everything to lower case

        result = re.findall(r'\w+', stripped_text)
        # EXAMPLE:  ['Mr', 'Joe', 'sons', 'A', 'Long', 'Term', 'business', 'Find', 'it', 'at', 'http', 'example', 'com', 'home', 'Visit', 'Joe', 's', 'NOW']
        return result
