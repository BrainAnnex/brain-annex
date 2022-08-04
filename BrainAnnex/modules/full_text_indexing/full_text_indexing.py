import re
import html


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
                    'old', 'older', 'new', 'newer',
                    'begin', 'began', 'start', 'starting', 'started',
                    'in', 'out', 'here', 'there',
                    'up', 'down', 'over', 'above', 'under', 'below', 'between', 'among', 'wherever',
                    'next', 'previous', 'other', 'another', 'thing', 'things',
                    'like', 'as', 'such', 'fairly', 'actual', 'actually',
                    'simple', 'simpler', 'simplest',
                    'each', 'any', 'all', 'some', 'more', 'most', 'less', 'least', 'than', 'extra', 'enough',
                    'everything', 'nothing',
                    'few', 'fewer', 'many', 'multiple', 'much', 'same', 'different',
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
        Next, eliminate "words" that are 1 character long, or in a list of common words.
        Finally, eliminate duplicates, and return the list of acceptable, unique words.

        :param text:   A string with the text to analyze and index
        :return:       A list of strings containing "acceptable", unique words in the text
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

        #print("The word list for the index is: ", word_list)

        return word_list



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
