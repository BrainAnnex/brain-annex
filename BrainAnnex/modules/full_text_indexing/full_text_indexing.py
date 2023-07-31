import re
import html
from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema


class FullTextIndexing:
    """
    Indexing-related methods, for full-text searching.

    NOTE: no stemming nor lemmatizing is done.
          Therefore, for best results, all word searches should be done on stems;
          for example, search for "learn" rather than "learning" or "learns" - to catch all 3
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
                    'can', 'cannot', 'could', 'might', 'may', 'do', 'does', 'did', 'didn', 'done', 'doing',
                    'make', 'made', 'making',
                    'have', 'haven', 'has', 'had', 'hadn', 'having',
                    'must', 'need', 'seem', 'seems', 'want', 'wants', 'should', 'shouldn',
                    'will', 'would', 'shall',
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



    ##########   STRING METHODS   ##########

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

        return word_list    # TODO: turn into a SET



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



    ##########   GRAPH METHODS   ##########

    @classmethod
    def initialize_schema(cls, content_item_class_id=None) -> None:
        """
        Initialize the graph-database Schema used by this Indexer module:

        1) It will create a new "Word" Class linked to a new "Indexer" Class,
        by means of an outbound "occurs" relationship.
        The newly-created "Word" Class will be given one Property: "name".

        2) It will add a relationship named "has_index" from an existing (or newly created)
        "Content Item" Class to the new "Indexer" Class.

        NOTE: if an existing Class named "Content Item" is not found,
              it will be created with some default values

        :param content_item_class_id: (OPTIONAL) The internal database ID of an existing "Content Item" Class;
                                            if not passed, it gets looked up
        :return:                None
        """

        if content_item_class_id is None:     # Look it up, if not passed
            if NeoSchema.class_name_exists("Content Item"):
                content_item_class_id = NeoSchema.get_class_internal_id(class_name="Content Item")
            else:
                content_item_class_id, _ = NeoSchema.create_class(name="Content Item", schema_type="L")

        indexer_class_id, _ = NeoSchema.create_class(name="Indexer", schema_type="S")

        NeoSchema.create_class_with_properties(class_name="Word", schema_type="S",
                                               property_list=["name"],
                                               class_to_link_to="Indexer", link_name="occurs", link_dir="OUT")

        NeoSchema.create_class_relationship(from_class=content_item_class_id, to_class=indexer_class_id, rel_name="has_index")



    @classmethod
    def new_indexing(cls, content_item_id: int, unique_words: [str]):
        """
        Used to create a new index, linking the given list of unique words
        to the specified "Content Item" data node.
        
        Create a data node of type "Indexer",
        with inbound relationships named "occurs" from "Word" data nodes (pre-existing or newly-created)
        for all the words in the given list.
        Also, create a relationship named "has_index" from an existing "Content Item" data node to the new "Indexer" node.

        :param content_item_id: The internal database ID of an existing "Content Item" data node
        :param unique_words:    A list of strings containing unique words
                                    - for example as returned by extract_unique_good_words()
        :return:                None
        """
        # Create a data node of type "Indexer", and link it up to the passed Content Item
        indexer_id = NeoSchema.add_data_point_with_links(class_name = "Indexer",
                                                          links =[{"internal_id": content_item_id, "rel_name": "has_index",
                                                                  "rel_dir": "IN"}])

        cls.populate_index(indexer_id=indexer_id, unique_words=unique_words)



    @classmethod
    def populate_index(cls, indexer_id: int, unique_words: [str]) -> None:
        """

        :param indexer_id:
        :param unique_words:
        :return:            None
        """
        # Locate (if already present), or create, a "Word" data node for each word in the list unique_words
        class_db_id = NeoSchema.get_class_internal_id(class_name="Word")
        result = NeoSchema.add_data_column_merge(class_internal_id=class_db_id,
                                                 property_name="name", value_list=unique_words)
        #print("result: ", result)

        word_node_list = result['old_nodes'] + result['new_nodes']      # Join the 2 lists

        # Link all the "Word" nodes (located or created above) to the "Indexer" node,
        # with an "occurs" outbound relationship
        # (in the future, to also perhaps store a count property)
        for word_node_id in word_node_list:
            NeoSchema.add_data_relationship_fast(from_neo_id=word_node_id, to_neo_id=indexer_id, rel_name="occurs")



    @classmethod
    def update_indexing(cls, content_item_id : int, unique_words: [str]):
        """
        Used to update an index, linking the given list of unique words
        to the specified "Indexer" data node, which was created by a call to new_indexing()
        at the time the index was first created.
        
        From the given data node of type "Indexer",
        add inbound relationships named "occurs" from "Word" data nodes (pre-existing or newly-created)
        for all the words in the given list.
        Also, create a relationship named "has_index" from an existing "Content Item" data node to the new "Indexer" node.

        :param content_item_id: The internal database ID of an existing "Content Item" data node
        :param unique_words:    A list of strings containing unique words
                                    - for example as returned by extract_unique_good_words()
        :return:
        """
        indexer_id = cls.get_indexer_node_id(content_item_id)
        print(indexer_id)


        # Sever all the existing "occurs" relationships to the "Indexer" data node
        # i.e. give a "clean slate" to the "Indexer" data node
        NeoSchema.remove_multiple_data_relationships(node_id=indexer_id, rel_name="occurs", rel_dir="IN", labels="Word")


        cls.populate_index(indexer_id=indexer_id, unique_words=unique_words)



    @classmethod
    def get_indexer_node_id(cls, content_item_id: int) -> int:
        """

        :param content_item_id: The internal database ID of an existing "Content Item" data node
        :return:                The internal database ID of the corresponding "Indexer" data node
        """
        q = '''
            MATCH (ci:`Content Item`)-[:has_index]->(i:Indexer)-[:SCHEMA]->(:CLASS {name: "Indexer"})
            WHERE id(ci) = $content_item_id
            RETURN id(i) AS indexer_id
            '''
        return cls.db.query(q, data_binding={"content_item_id": content_item_id}, single_cell="indexer_id")



    @classmethod
    def remove_indexing(cls, content_item_id : int):
        """
        Drop the "Indexer" node linked to the given Content Item node
        :param content_item_id: The internal database ID of an existing "Content Item" data node
        :return:
        """
        pass        # TODO



    @classmethod
    def count_indexed_words(cls, content_item_id : int) -> int:
        """
        Determine and return the number of words attached to the index
        of the given Content Item data node

        :param content_item_id: The internal database ID of an existing "Content Item" data node
        :return:                The number of indexed words associated to the above node
        """
        q = '''
            MATCH (wc:CLASS {name:"Word"})<-[:SCHEMA]-(w:Word)-[:occurs]->(i:Indexer)<-[:has_index]
            -(ci:`Content Item`) WHERE id(ci)=$content_item_id 
            RETURN count(w) AS word_count
            '''
        return cls.db.query(q, data_binding={"content_item_id": content_item_id}, single_cell="word_count")



    @classmethod
    def prepare_word_node_OBSOLETE(cls, word: str) -> int:   # TODO: no longer needed
        """
        Locate or create a "Word" node for the given word

        :param word:    A string with a word suitable for indexing
        :return:        The internal database ID of a "Word" node (either pre-existing or just created)
                            representing the given word
        """
        # TODO: for now, we're always creating rather than first checking if already there
        return NeoSchema.add_data_point(class_name="Word", properties={"name": word})
