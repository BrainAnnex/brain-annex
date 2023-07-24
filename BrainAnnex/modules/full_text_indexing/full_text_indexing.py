import re
import html


class FullTextIndexing:
    """
    Indexing-related methods.  In early development stage
    """
    # The "db" class properties gets set by InitializeBrainAnnex.set_dbase()

    db = None           # Object of class "NeoAccess".  MUST be set before using this class!


    TAG_RE = re.compile(r'<[^>]+>')         # Use regex to strip off all HTML

    # List of common English words to skip from indexing (stopword list)
    # See https://github.com/Alir3z4/stop-words
    # TODO: allow over-ride in config file
    COMMON_WORDS = ['and', 'or', 'either', 'nor', 'neither',
                    'the', 'an', 'with', 'without', 'within',
                    'in', 'out', 'on', 'at', 'of', 'from', 'to', 'into', 'not', 'but', 'by',
                    'if', 'whether', 'then', 'else',
                    'me', 'my', 'mine', 'he', 'she', 'it', 'him', 'his', 'her', 'its',
                    'we', 'our', 'you', 'your', 'yours', 'they', 'them', 'their',
                    'why', 'because', 'since', 'how', 'for', 'both', 'indeed',
                    'help', 'helps', 'let', 'lets',
                    'go', 'goes', 'going', 'gone', 'became', 'become',
                    'be', 'is', 'isn', 'am', 'are', 'aren', 'been', 'was', 'wasn', 'being',
                    'can', 'could', 'might', 'may', 'do', 'does', 'did', 'didn', 'done', 'doing',
                    'make', 'made', 'making',
                    'have', 'haven', 'has', 'had', 'hadn', 'having',
                    'must', 'need', 'seem', 'seems', 'want', 'wants', 'should', 'shouldn',
                    'will', 'would',
                    'get', 'gets', 'got', 'take', 'takes',
                    'ask', 'asks', 'answer', 'answers',
                    'when', 'where', 'which', 'who', 'why', 'what',
                    'no', 'yes', 'maybe', 'ok', 'oh',
                    'ie', 'i.e', 'eg', 'e.g',
                    'll', 've', 'so',
                    'good', 'better', 'best', 'great', 'well', 'bad',  'worse', 'worst',
                    'just', 'about', 'above', 'again', 'ago',
                    'times', 'date', 'dates', 'today', 'day', 'month', 'year', 'yr', 'days', 'months', 'years',
                    'hour', 'hr', 'minute', 'min', 'second', 'sec',
                    'now', 'currently', 'late', 'early', 'soon', 'later', 'earlier', 'already',
                    'after', 'before', 'yet', 'whenever', 'while', 'during', 'ever',
                    'never', 'occasionally', 'sometimes', 'often', 'always', 'eventually',
                    'really', 'approximately',
                    'old', 'older', 'new', 'newer',
                    'begin', 'began', 'start', 'starting', 'started',
                    'in', 'out', 'here', 'there',
                    'up', 'down', 'over', 'above', 'under', 'below', 'between', 'among', 'wherever',
                    'next', 'previous', 'other', 'another', 'thing', 'things',
                    'like', 'as', 'such', 'fairly', 'actual', 'actually',
                    'simple', 'simpler', 'simplest',
                    'each', 'any', 'all', 'some', 'more', 'most', 'less', 'least', 'than', 'extra', 'enough',
                    'everything', 'nothing',
                    'few', 'fewer', 'many', 'multiple', 'much', 'same', 'different', 'equal',
                    'full', 'empty', 'lot', 'very', 'around', 'vary', 'varying',
                    'approximately', 'approx', 'certain', 'uncertain',
                    'part', 'parts', 'wide', 'narrow', 'side',
                    'hence', 'therefore', 'thus', 'whereas',
                    'whom', 'whoever', 'whose',
                    'this', 'that', 'these', 'those',
                    'too', 'also',
                    'related', 'issues', 'issue',
                    'use', 'used',
                    'com', 'www', 'http', 'https',
                    'one', 'two',
                    'include', 'including', 'incl', 'except', 'test', 'testing', 'sure', 'according', 'accordingly',
                    'basically', 'essentially', 'called', 'named', 'consider', 'considering', 'however', 'especially', 'etc',
                    'happen', 'happens',
                    'small', 'smaller', 'smallest', 'big', 'bigger', 'biggest', 'large', 'larger', 'largest',

                    'data', 'value', 'values']



    @classmethod
    def extract_unique_good_words(cls, text: str) -> [str]:
        """
        From the given text, zap HTML, HTML entities (such as &ndash;) and punctuation;
        then, turn into lower case, and break up into individual words.

        Next, eliminate "words" that are 1 character long, or that are numbers,
        or that are in a list of common words.

        Finally, eliminate duplicates, and return the list of acceptable, unique words.

        Note: no stemming is done.

        EXAMPLE - given '<p>Mr. Joe&amp;sons<br>A Long&ndash;Term business! Find it at &gt; (http://example.com/home)<br>Visit Joe&#39;s &quot;NOW!&quot;</p>'
                  it returns:
                  ['mr', 'joe', 'sons', 'long', 'term', 'business', 'find', 'example', 'home', 'visit']

        :param text:   A string with the text to analyze and index
        :return:       A list of strings containing "acceptable", unique words in the text
        """

        assert type(text) == str, \
            f"extract_unique_good_words(): the argument must be a string; instead, it was of type {type(text)}"

        #if text is None:
            #raise Exception("FullTextIndexing: unable to index the contents because None was passed")

        #print("The original string is : \n" +  text)

        # Extract words from string, and convert them to lower case
        split_text = cls.split_into_words(text, to_lower_case=True)
        #print("The split text is : ", split_text)

        # Eliminate "words" that are 1 character long, or that are numbers,
        # or that are in a list of common words.  Don't include duplicates
        word_list = []

        for word in split_text:
            if len(word) > 1 \
                    and not word.isnumeric() \
                    and word not in cls.COMMON_WORDS \
                    and word not in word_list:
                word_list.append(word)

        #print("The word list for the index is: ", word_list)

        return word_list



    @classmethod
    def split_into_words(cls, text: str, to_lower_case=True) ->[str]:
        """
        Zap HTML, HTML entities (such as &ndash;) and punctuation from the given text;
        then, break it up into individual words.  If requested, turn it all to lower case.

        Care is taken to make sure that the stripping of special characters does NOT fuse words together;
        e.g. avoid turning 'Long&ndash;Term' into a single word as 'LongTerm';
        likewise, avoid turning 'One<br>Two' into a single word as 'OneTwo'

        EXAMPLE.  Given:
            '<p>Mr. Joe&amp;sons<br>A Long&ndash;Term business! Find it at &gt; (http://example.com/home)<br>Visit Joe&#39;s &quot;NOW!&quot;</p>'
            It will return (if to_lower_case is False):
            ['Mr', 'Joe', 'sons', 'A', 'Long', 'Term', 'business', 'Find', 'it', 'at', 'http', 'example', 'com', 'home', 'Visit', 'Joe', 's', 'NOW']

        :param text:            A string with the text to parse
        :param to_lower_case:   If True, all text is converted to lower case
        :return:                A list of words in the text,
                                    free of punctuation, HTML and HTML entities such as &ndash;
        """
        unescaped_text = html.unescape(text)    # Turn HTML entities such as "&ndash;" into text
        #print(unescaped_text)  # <p>Mr. Joe&sons<br>A Long–Term business! Find it at > (http://example.com/home)<br>Visit Joe's "NOW!"</p>

        stripped_text = cls.TAG_RE.sub(' ', unescaped_text) # Use regex to strip off all HTML and turn each occurrence into a blank
        #print(stripped_text)   # Mr. Joe&sons A Long–Term business! Find it at > (http://example.com/home) Visit Joe's "NOW!"    <- Note: blank space at end

        if to_lower_case:
            stripped_text = stripped_text.lower()   # If requested, turn everything to lower case

        result = re.findall(r'\w+', stripped_text)  # Use regex to split off the string into individual words
                                                    # (note that the "&" in the original string is treated as blank space)
        # EXAMPLE:  ['Mr', 'Joe', 'sons', 'A', 'Long', 'Term', 'business', 'Find', 'it', 'at', 'http', 'example', 'com', 'home', 'Visit', 'Joe', 's', 'NOW']

        return result



    @classmethod
    def new_indexing(cls, content_id : int, word_list: [str]):
        """

        :param content_id:
        :param word_list:
        :return:
        """
        # Create a node of type "Indexer" (or "indexer"?)


        # Locate or create a "Word" node for each word in word_list
        for word in word_list:
            word_node = FullTextIndexing.prepare_word_node(word)

        # Link all the above "Word" nodes to the "Indexer" node, with an "occurs" relationship
        # (in the future, to also perhaps store a count property)

        # Link the "Indexer" node to the given Content-Item node



    @classmethod
    def prepare_word_node(cls, word: str) -> int:
        """
        Locate or create a "Word" node for the given word

        :param word:    A string with a word suitable for indexing
        :return:        The internal database ID of a "Word" node (either pre-existing or just created)
                            representing the given word
        """
        pass