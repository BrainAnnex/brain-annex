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
                    'now', 'late', 'early', 'soon', 'later', 'earlier',
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
                    'com', 'www', 'http', 'https',
                    'one', 'two']



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

        print("The word list for the index is: ", word_list)

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
