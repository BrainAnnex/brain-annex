import re
import html
from typing import Union, List, Set
from brainannex import CypherUtils, NeoSchema
import brainannex.exceptions as exceptions



class FullTextIndexing:
    """
    Indexing-related methods, for full-text searching.

    For more info and background info, please see:
        https://julianspolymathexplorations.blogspot.com/2023/08/full-text-search-neo4j-indexing.html

    NOTE: no "stemming" nor "lemmatizing" is done.
          Therefore, for best results, all word searches should be done on stems;
          for example, search for "learn" rather than "learning" or "learns" - to catch all 3
    """

    # The "db" class properties gets set by InitializeBrainAnnex.set_dbase()
    db = None           # Object of class "NeoAccess".  MUST be set before using this class!
                        # TODO: add a method set_database(), as done for NeoSchema


    TAG_RE = re.compile(r'<[^>]+>')         # Use regex to strip off all HTML

    # List of common English words to skip from indexing (stopword list)
    # See https://github.com/Alir3z4/stop-words
    # TODO: allow over-ride in config file
    # Note: 2-letter words are redundant from the list below, because those don't get indexed
    COMMON_WORDS = ['and', 'or', 'either', 'nor', 'neither',
                    'the', 'an', 'with', 'without', 'within',
                    'in', 'out', 'on', 'off', 'at', 'of', 'from', 'to', 'into', 'not', 'but', 'by', 'upon',
                    'if', 'whether', 'then', 'else',
                    'me', 'my', 'mine', 'he', 'she', 'it', 'him', 'his', 'her', 'its',
                    'we', 'us', 'our', 'you', 'your', 'yours', 'they', 'them', 'their',
                    'why', 'because', 'due', 'since', 'until', 'through', 'thru',
                    'how', 'for', 'both', 'indeed',
                    'help', 'helps', 'let', 'lets',
                    'go', 'goes', 'going', 'gone', 'went',
                    'became', 'become', 'becomes', 'come', 'comes', 'came',
                    'be', 'is', 'isn', 'am', 'are', 'aren', 'were', 'been', 'was', 'wasn', 'being',
                    'can', 'cannot', 'could', 'might', 'may', 'do', 'does', 'doesn', 'did', 'didn', 'done', 'doing',
                    'make', 'made', 'making',
                    'have', 'haven', 'has', 'had', 'hadn', 'having',
                    'must', 'need', 'needs', 'needed', 'seem', 'seems', 'seemed', 'want', 'wants', 'should', 'shouldn', 'ought',
                    'will', 'would', 'shall',
                    'get', 'gets', 'got', 'give', 'gives', 'gave', 'giving',
                    'take', 'takes', 'took', 'taking', 'put', 'bring', 'brings', 'bringing',
                    'see', 'sees', 'given', 'end', 'start', 'starts', 'starting',
                    'ask', 'asks', 'answer', 'answers', 'question', 'questions',
                    'when', 'where', 'which', 'who', 'why', 'what',
                    'no', 'non', 'not', 'yes', 'maybe', 'perhaps', 'ok', 'oh',
                    'ie', 'i.e', 'eg', 'e.g',
                    'll', 've', 'so',
                    'good', 'better', 'best', 'well', 'bad',  'worse', 'worst',
                    'just', 'about', 'above', 'again', 'ago',
                    'times', 'date', 'dates', 'today', 'day', 'month', 'year', 'yr', 'days', 'months', 'years',
                    'hour', 'hr', 'minute', 'min', 'second', 'sec', 'pm',
                    'now', 'currently', 'late', 'early', 'soon', 'later', 'earlier', 'already',
                    'after', 'before', 'prior', 'yet', 'whenever', 'while', 'during', 'ever',
                    'follow', 'follows', 'following', 'along',
                    'never', 'seldom', 'rarely', 'occasionally', 'sometimes',
                    'often', 'always', 'usually', 'eventually', 'typical', 'typically', 'everyday',
                    'almost', 'quite', 'nearly',
                    'frequent', 'ubiquitous', 'usual', 'common', 'commonly',
                    'remarkable', 'impressive',
                    'really', 'approximately',
                    'allow', 'allows', 'allowing',
                    'old', 'older', 'new', 'newer', 'recent', 'recently',
                    'begin', 'began', 'start', 'starting', 'started',
                    'in', 'out', 'here', 'there',
                    'instead', 'alternative', 'alternatively', 'otherwise', 'case', 'cases', 'extent',
                    'up', 'down', 'over', 'above', 'under', 'below', 'between', 'among', 'wherever',
                    'next', 'previous', 'other', 'others', 'another', 'thing', 'things',
                    'like', 'as', 'aka', 'akin', 'such', 'fairly', 'actual', 'actually',
                    'likewise', 'similar', 'similarly',
                    'simple', 'simpler', 'simplest', 'simply',
                    'each', 'per', 'any', 'all', 'every', 'everyone', 'anyone', 'anybody', 'anything', 'something', 'someone', 'some', 'various',
                    'more', 'most', 'mostly', 'additional', 'extra',
                    'less', 'least', 'than', 'enough', 'only', 'further',
                    'everything', 'nothing',
                    'few', 'fewer', 'many', 'multiple', 'several', 'much', 'same', 'equal', 'different', 'unlike',
                    'full', 'empty', 'lot', 'very', 'around', 'vary', 'varying',
                    'complete', 'incomplete', 'thorough', 'thoroughly',
                    'approximately', 'approx', 'somewhat', 'certain', 'uncertain',
                    'directly', 'indirectly',
                    'part', 'parts', 'wide', 'broad', 'narrow', 'side', 'across',
                    'hence', 'therefore', 'thus', 'whereas', 'nevertheless', 'notwithstanding',
                    'whom', 'whoever', 'whomever', 'whatever', 'whose',
                    'this', 'that', 'these', 'those',
                    'too', 'also',
                    'related', 'issues', 'issue', 'referred',
                    'type', 'types', 'instance', 'instances',
                    'use', 'uses', 'used', 'using',
                    'com', 'org', 'www', 'http', 'https',
                    'zero', 'one', 'ones', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine',
                    'first', 'second', 'third', 'fourth', 'last',
                    'iii',
                    'include', 'including', 'incl', 'except', 'sure', 'according', 'accordingly',
                    'example', 'examples', 'define', 'defined',
                    'basically', 'essentially', 'finally',
                    'called', 'named', 'name', 'consider', 'considering', 'however', 'especially', 'etc',
                    'happen', 'happens', 'happening', 'continue', 'continues', 'continuing',
                    'change', 'changes', 'changing', 'changed',
                    'small', 'smaller', 'smallest', 'little', 'brief', 'briefly',
                    'short', 'shorter', 'shortest',
                    'big', 'bigger', 'biggest', 'large', 'larger', 'largest', 'huge',
                    'long', 'longer', 'longest',
                    'great', 'greater', 'greatest',
                    'low', 'lower', 'lowest', 'high', 'higher', 'highest', 'limited',
                    'increase', 'increased', 'decrease', 'decreased', 'vary', 'varies', 'varying',
                    'consist', 'consists', 'consisting', 'result', 'results', 'resulting',
                    'description', 'descriptions', 'describe', 'describing',
                    'hello', 'hi', 'info',
                    're', 'vs', 'ex',
                    'data', 'value', 'values',
                    'obvious', 'obviously', 'clearly',
                    'show', 'shows', 'showing', 'find', 'finds', 'found', 'finding', 'findings', 'respectively',
                    'still', 'size', 'pre', 'inc', 'comfortably', 'look', 'approach',
                    'exact', 'exactly', 'likely', 'probable', 'probably', 'avg', 'total', 'misc',
                    'require', 'requires', 'requiring', 'quick', 'quickly', 'rather',
                    'know', 'knows', 'knowing', 'say', 'says', 'saying']


    # TODO: allow user-specific words, from a configuration file.  For example, for German: ich, du, er, sie, wir, ihr



    ##########   STRING METHODS   ##########

    @classmethod
    def split_into_words(cls, text: str, to_lower_case=True, drop_html=True) -> [str]:
        """
        Lower-level function used in the larger context of indexing text that may contain HTML.

        Given a string, optionally zap HTML tags and HTML entities, such as &ndash;
        then ditch punctuation from the given text;
        finally, break it up into individual words, returned as a list.  If requested, turn it all to lower case.

        Care is taken to make sure that the stripping of special characters does NOT fuse words together;
        e.g. avoid turning 'Long&ndash;Term' into a single word as 'LongTerm';
        likewise, avoid turning 'One<br>Two' into a single word as 'OneTwo'

        EXAMPLE.  Given:
            '<p>Mr. Joe&amp;sons<br>A Long&ndash;Term business! Find it at &gt; (http://example.com/home)<br>Visit Joe&#39;s &quot;NOW!&quot;</p>'
            It will return (if to_lower_case is False):
            ['Mr', 'Joe', 'sons', 'A', 'Long', 'Term', 'business', 'Find', 'it', 'at', 'http', 'example', 'com', 'home', 'Visit', 'Joe', 's', 'NOW']

        Note about numbers:  * negative signs are lost  * numbers with decimals will get split into two parts

        :param text:            A string with the text to parse
        :param to_lower_case:   If True, all text is converted to lower case
        :param drop_html:       Use True if passing HTML text
        :return:                A (possibly empty) list of words in the text,
                                    free of punctuation, HTML and HTML entities such as &ndash;
        """
        # TODO: maybe eliminate the decimal numbers while leaving the integers alone, to allow indexing of (some) integer numbers such as years

        if drop_html:
            unescaped_text = html.unescape(text)    # Turn HTML entities into characters; e.g. "&ndash;" into "-"
            #print(unescaped_text)  # <p>Mr. Joe&sons<br>A Long–Term business! Find it at > (http://example.com/home)<br>Visit Joe's "NOW!"</p>

            stripped_text = cls.TAG_RE.sub(' ', unescaped_text) # Use regex to strip off all HTML and turn each occurrence into a blank
            #print(stripped_text)   # Mr. Joe&sons A Long–Term business! Find it at > (http://example.com/home) Visit Joe's "NOW!"    <- Note: blank space at end
        else:
            stripped_text = text


        if to_lower_case:
            stripped_text = stripped_text.lower()   # If requested, turn everything to lower case

        result = re.findall(r'\w+', stripped_text)  # Use regex to split off the string into individual words
        # (note that the "&" in the original string is treated as blank space/word separator)
        # EXAMPLE:  ['Mr', 'Joe', 'sons', 'A', 'Long', 'Term', 'business', 'Find', 'it', 'at', 'http', 'example', 'com', 'home', 'Visit', 'Joe', 's', 'NOW']

        return result



    @classmethod
    def extract_unique_good_words(cls, text :str, drop_html=True) -> Set[str]:
        """
        Higher-level function to prepare text for indexing;
        use the drop_html flag if the text contains HTML.

        From the given text, it returns the set of "acceptable", unique words.
        It does the following:

            1) zap punctuation
            2) if requested, HTML, HTML entities (such as &ndash;);
            3) turn into lower case
            4) break up into individual words
            5) strip off leading/trailing underscores
            6) eliminate "words" that match at least one of these EXCLUSION test:
                * are just 1 or 2 characters long
                * are numbers
                * start with digits (e.g. "50m" or "123plus")
                * are found in a list of common words

            7) eliminate duplicates

        Note: no stemming or other grammatical analysis is done.

        EXAMPLE - given
                  '<p>Mr. Joe&amp;sons<br>A Long&ndash;Term business! Find it at &gt; (http://example.com/home)<br>Visit Joe&#39;s &quot;NOW!&quot;</p>'
                  it returns:
                  ['mr', 'joe', 'sons', 'long', 'term', 'business', 'find', 'example', 'home', 'visit']

        :param text:        A string with the text to analyze and index
        :param drop_html:   Use True if passing HTML text
        :return:            A (possibly empty) set of strings containing "acceptable",
                                unique words in the text
        """

        assert type(text) == str, \
            f"extract_unique_good_words(): the argument must be a string; instead, it was of type {type(text)}"

        # Extract words from string, and convert them to lower case
        split_text = cls.split_into_words(text, to_lower_case=True, drop_html=drop_html)
        #print("The split text is : ", split_text)

        # Eliminate "words" that are 1 or 2 characters long, or that are numbers,
        # or that are in a list of common words.  Also eliminate duplicates
        word_set = set()    # Empty set

        # Define a regular expression pattern to match anything that STARTS with a numeric character
        pattern = r"^\d"        # Formerly: pattern = r"\d"

        for word in split_text:
            word = word.strip("_")
            if len(word) > 2 \
                    and not word.isnumeric() \
                    and word not in cls.COMMON_WORDS \
                    and not re.findall(pattern, word):
                word_set.add(word)      # Add the element to the set, if it passed all the exclusions

        #print("The word set for the index is: ", word_set)

        return word_set




    #############   GRAPH METHODS   #############

    @classmethod
    def initialize_schema(cls, content_item_class_name="Content Item") -> None:
        """
        Initialize the graph-database Schema used by this Indexer module:

        1) It will create a new "Word" Class linked to a new "Indexer" Class,
        by means of an outbound "occurs" relationship.
        The newly-created "Word" Class will be given one Property: "name".

        2) It will add a relationship named "has_index" from an existing (or newly created)
        "Content Item" Class to the new "Indexer" Class.

        NOTE: if an existing Class with the named specified by the argument `content_item_class_name`
              is not found, it will be created with some default values

        :param content_item_class_name: (OPTIONAL) The name of the Schema Class for Content Items,
                                            i.e. the Class of the Data Items to be indexed
                                            if not found, it gets created
                                            EXAMPLES: "Document", "Note", "Content Items" (default)
        :return:                        None
        """
        #         TODO: manage indexing.  If done in Cypher:
        #                                 CREATE TEXT INDEX word_lookup FOR (n:Word) ON (n.name)

        assert NeoSchema.is_valid_class_name(content_item_class_name), \
            "initialize_schema(): a non-empty string is required for argument `content_item_class_name`"

        if NeoSchema.class_name_exists(content_item_class_name):
            content_item_class_id = NeoSchema.get_class_internal_id(class_name=content_item_class_name)
        else:
            content_item_class_id, _ = NeoSchema.create_class(name=content_item_class_name, strict=False)


        indexer_class_id, _ = NeoSchema.create_class(name="Indexer", strict=True)

        NeoSchema.create_class_with_properties(name="Word", strict=True,
                                               properties=["name"],
                                               class_to_link_to="Indexer", link_name="occurs", link_dir="OUT")

        NeoSchema.create_class_relationship(from_class=content_item_class_id, to_class=indexer_class_id, rel_name="has_index")



    @classmethod
    def new_indexing(cls, internal_id :int, unique_words :Set[str], to_lower_case=True) -> None:
        """
        Used to create a new index in the database
        for the (single) specified data node that represents a "Content Item".
        The indexing will link that Content Item to the given list of unique words.

        An Exception is raised if the "Indexer" node already exists

        Details:
        1) Create a data node of class "Indexer",
            with inbound relationships named "occurs" from "Word" data nodes
            (pre-existing or newly-created as needed)
            for all the words in the given list
        2) create a relationship named "has_index" from an existing "Content Item" data node
            to the new "Indexer" node

        :param internal_id:  The internal database ID of an existing data node
                                    that represents a "Content Item" (not necessarily with that Schema name)
        :param unique_words:    A list of strings containing unique words "worthy" of indexing
                                    - for example as returned by extract_unique_good_words()
        :param to_lower_case:   If True, all text is converted to lower case
        :return:                None
        """
        # TODO: consider combining new_indexing() and update_indexing()

        indexer_id = cls.get_indexer_node_id(internal_id)
        assert indexer_id is None, \
            f"new_indexing(): an index ALREADY exists for the given Content Item node (internal id {internal_id})"

        # Create a data node of type "Indexer", and link it up to the passed Content Item data node
        '''
        indexer_id = NeoSchema.add_data_node_with_links(class_name ="Indexer",
                                                        links =[{"internal_id": internal_id, "rel_name": "has_index",
                                                                  "rel_dir": "IN"}])
        '''
        indexer_id = NeoSchema.create_data_node(class_name="Indexer",
                                                links =[{"internal_id": internal_id, "rel_name": "has_index",
                                                          "rel_dir": "IN"}])

        cls.add_words_to_index(indexer_id=indexer_id, unique_words=unique_words, to_lower_case=to_lower_case)



    @classmethod
    def add_words_to_index(cls, indexer_id :int, unique_words :Set[str], to_lower_case=True) -> int:
        """
        Add to the database "Word" nodes for all the given words, unless already present.
        Then link all the "Word" nodes, both the found and the newly-created ones,
        to the passed "Indexer" node with an "occurs" relationships

        :param indexer_id:      Internal database ID of an existing "Indexer" data node
                                    used to hold all the "occurs" relationships
                                    to the various Word nodes.
                                    If not present, an Exception gets raised.
        :param unique_words:    Set of strings, with unique words for the index
        :param to_lower_case:   If True, all text is converted to lower case
        :return:                The number of new "Word" Data Notes that were created
        """
        # Validate indexer_id
        CypherUtils.assert_valid_internal_id(indexer_id)
        q = '''
            MATCH (i :Indexer {`_SCHEMA`: "Indexer"})
            WHERE id(i) = $indexer_id 
            RETURN count(i) AS number_of_nodes
            '''
        result = cls.db.query(q, data_binding={"indexer_id": indexer_id},
                              single_cell="number_of_nodes")
        assert result > 0, \
            f"add_words_to_index(): there's no Indexer node with internal ID {indexer_id}"


        if to_lower_case:
            unique_words = list(map(str.lower, unique_words))
        else:
            unique_words = list(unique_words)

        # The following query locates (or creates if not found) a "Word" data node
        # for each word in the list unique_words,
        # and then (as needed) it links it up to the "Indexer" node (ind), with an "occurs" relationship,
        # and to the "Class" node named "Word" (wcl), with a "SCHEMA" relationship.
        # Note: any already-existing "Word" data node ALREADY possess a link to the common Class node;
        #       hence, the line   "MERGE (w :`Word` {name : word})-[:SCHEMA]->(wcl)"
        q = '''
            MATCH (ind :`Indexer`)
            WHERE id(ind) = $indexer_id
            WITH ind
            UNWIND $word_list AS word
            MERGE (w :`Word` {name : word, `_SCHEMA`: "Word"})
            MERGE (ind)<-[:occurs]-(w)
            '''

        data_binding = {"indexer_id": indexer_id, "word_list": unique_words}
        #print("add_words_to_index(): about to run the query to update the index")
        #cls.db.debug_query_print(q, data_binding)
        result = cls.db.update_query(q, data_binding)
        #print(result)
        # EXAMPLE of result:
        #   {'labels_added': 3, '_contains_updates': True, 'relationships_created': 6, 'nodes_created': 3, 'properties_set': 3, 'returned_data': []}
        number_word_nodes_added = result.get('nodes_created', 0)
        number_word_nodes_found = len(unique_words) - number_word_nodes_added

        assert result.get('labels_added', 0) == number_word_nodes_added, \
            f"add_words_to_index(): internal consistency error; " \
            f"the number of labels created ({result.get('labels_added', 0)}) should be equal the number of nodes created ({number_word_nodes_added})"

        assert result.get('properties_set', 0) == 2 * number_word_nodes_added, \
            f"add_words_to_index(): internal consistency error; " \
            f"the number of properties being set ({result.get('properties_set', 0)}) should be equal to twice the number of nodes created ({number_word_nodes_added})"
            # Note: this check requires a knowledge of the Schema layer internal organization!  Each new 'Word' node has 2 properties set: `name` and `_SCHEMA`

        # To determine a lower and upper bound on the the number of relationships added,
        # consider that ech newly-create Word data node adds 1 relationship (to the "Indexer" node);
        # by contrast, each found node only adds at most 1 relationship (to the "Indexer" node)
        lb = number_word_nodes_added
        ub =  lb + + number_word_nodes_found
        assert lb <= result.get('relationships_created', 0) <= ub, \
            f"add_words_to_index(): internal consistency error; " \
            f"the number of relationships_created should have been between {lb} and {ub}, inclusive; " \
            f"instead of result.get('relationships_created', 0)"

        return number_word_nodes_added



    @classmethod
    def update_indexing(cls, content_uri :int, unique_words :Set[str], to_lower_case=True) -> None:
        """
        Used to update an index, linking the given list of unique words
        to the specified "Indexer" data node, which was created by a call to new_indexing()
        at the time the index was first created.
        
        From the given data node of type "Indexer",
        add inbound relationships named "occurs" from "Word" data nodes (pre-existing or newly-created)
        for all the words in the given list.
        Also, create a relationship named "has_index" from an existing "Content Item" data node to the new "Indexer" node.

        Note: if no index exist, an Exception is raised

        :param content_uri: The internal database ID of an existing "Content Item" data node
        :param unique_words:    A list of strings containing unique words
                                    - for example as returned by extract_unique_good_words()
        :param to_lower_case:   If True, all text is converted to lower case
        :return:                None
        """
        indexer_id = cls.get_indexer_node_id(content_uri)
        assert indexer_id is not None, \
                    f"update_indexing(): unable to find an index for the given Content Item " \
                    f" (internal id {content_uri}).  Did you first create an index for it?"

        # Sever all the existing "occurs" relationships to the "Indexer" data node
        # i.e. give a "clean slate" to the "Indexer" data node
        NeoSchema.remove_multiple_data_relationships(node_id=indexer_id, rel_name="occurs", rel_dir="IN", labels="Word")

        try:
            #print("update_indexing(): about to calling add_words_to_index()")
            cls.add_words_to_index(indexer_id=indexer_id, unique_words=unique_words, to_lower_case=to_lower_case)
            #print("update_indexing(): returned from call to add_words_to_index()")
        except Exception as ex:
            err_details = f"Failure in FullTextIndexing.add_words_to_index().  {exceptions.exception_helper(ex)}"
            raise Exception(err_details)



    @classmethod
    def get_indexer_node_id(cls, internal_id :int) -> Union[int, None]:
        """
        Retrieve and return the internal database ID of the "Indexer" data node
        associated to the given Content Item data node.
        If not found, None is returned

        :param internal_id: The internal database ID of an existing data node
                                    (either of Class "Content Item", or of a Class that is ultimately
                                    an INSTANCE_OF a "Content Item" Class)
        :return:                The internal database ID of the corresponding "Indexer" data node.
                                    If not found, None is returned
        """
        # Prepare a Cypher query
        q = '''
            MATCH (ci)-[:has_index]->(i:Indexer {`_SCHEMA`: "Indexer"})
            WHERE id(ci) = $content_uri
            RETURN id(i) AS indexer_id
            '''

        return cls.db.query(q, data_binding={"content_uri": internal_id},
                            single_cell="indexer_id")       # Note: will be None if no record found



    @classmethod
    def remove_indexing(cls, content_uri :int) -> None:
        """
        Drop the "Indexer" node linked to the given Content Item node.
        If no index exists, an Exception is raised

        :param content_uri: The internal database ID of an existing "Content Item" data node
        :return:                None
        """
        indexer_id = cls.get_indexer_node_id(content_uri)

        assert indexer_id is not None, \
            f"remove_indexing(): unable to find an index for the given Content Item node" \
            f" (internal id {content_uri}).  Maybe you already removed it?"

        number_deleted = NeoSchema.delete_data_nodes(node_id=indexer_id, class_name="Indexer")
        #NeoSchema.delete_data_node_OLD(node_id=indexer_id, labels="Indexer", class_node="Indexer")
        assert number_deleted == 1, \
            f"remove_indexing(): failed to remove the Index node.  Number of nodes deleted: {number_deleted}"



    @classmethod
    def number_of_indexed_words(cls, internal_id=None, uri=None) -> int:
        """
        Determine and return the number of words attached to the index
        of the given data node (typically of a Class representing "Content Item" ,
        or instance thereof, such as "Document" or "Note")

        :param internal_id: The internal database ID of an existing Content Item data node
        :param uri:         Alternate way to specify the Content Item data node, with a string URI
        :return:            The number of indexed words associated to the above node
        """
        if internal_id is not None:
            assert type(internal_id) == int, "number_of_indexed_words(): argument `internal_id` must be an integer"
            clause = "WHERE id(ci) = $internal_id"
            data_binding = {"internal_id": internal_id}
        elif uri:
            assert type(uri) == str, "number_of_indexed_words(): argument `uri` must be a string"
            clause = "WHERE ci.uri = $uri"
            data_binding = {"uri": uri}
        else:
            raise Exception("number_of_indexed_words(): at least one argument must be specified")

        q = f'''
            MATCH (w :Word {{`_SCHEMA`: "Word"}})-[:occurs]->(i :Indexer)<-[:has_index]-(ci) 
            {clause}
            RETURN count(w) AS word_count
            '''
        return cls.db.query(q, data_binding=data_binding, single_cell="word_count")



    @classmethod
    def most_common_words_NOT_YET_USED(cls) -> [str]:    # TODO: finish implementing
        """
        Return the 200 or so most common words in the current index
        """
        q = '''
            MATCH (w:Word)-[:occurs]->(i:Indexer) 
            RETURN w.name, count(i) AS c
            ORDER by c DESC LIMIT 200
        '''

        return ["Not yet implemented"]



    @classmethod
    def word_occurrence_NOT_YET_USED(cls, word: str) -> int:    # TODO: finish implementing
        """
        Return the usage count of the given word in the current index
        :param word:
        :return:
        """
        q = '''
        MATCH (w:Word {name:$word})-[:occurs]->(i:Indexer) 
        RETURN count(i) AS word_occurrence
        '''

        return 0



    @classmethod
    def index_size_NOT_YET_USED(cls):    # TODO: finish implementing
        """
        Return the number of content items current being indexed

        :return:
        """
        q = '''
            MATCH (n:Indexer) RETURN count(n)
            '''



    @classmethod
    def number_word_NOT_YET_USED(cls):    # TODO: finish implementing
        """
        Return the number of words current being used in the indexing

        :return:
        """
        q = '''
            MATCH (n:Word) RETURN count(n)
            '''


    @classmethod
    def unused_word_NOT_YET_USED(cls):    # TODO: finish implementing
        """
        Return a list of words in the indexing that lack any usage

        :return:
        """
        pass



    @classmethod
    def rebuild_index_NOT_YET_USED(cls, directory :str):    # TODO: finish implementing
        """
        Rebuild the index from all the (text or HTML) files in the given directory.

        TODO: a version that looks up that list from the database

        :param directory:     EXAMPLE:  "D:/tmp/transfer"  (Use forward slashes even on Windows!)
        :return:
        """
        import os
        from brainannex.media_manager import MediaManager

        file_list = os.listdir(directory)
        #print(f"Total number of files: {len(file_list)}")

        # Index the content of all the files
        i = 1
        for filename in file_list:
            #print(f"\n {i} -------------------------\n", filename)
            (basename, suffix) = os.path.splitext(filename)
            q = f"MATCH (n:Note) WHERE n.basename='{basename}' AND n.suffix='htm' RETURN ID(n) AS node_int_id"
            node_int_id = cls.db.query(q, single_cell="node_int_id")
            #print("    node's integer ID: ", node_int_id)
            path = "TBA"
            file_contents = MediaManager.get_from_text_file(filename, path)
            #print(file_contents)
            word_list = FullTextIndexing.extract_unique_good_words(file_contents)
            #print(word_list)
            FullTextIndexing.new_indexing(internal_id= node_int_id, unique_words = word_list)
            i += 1




    #########################   SEARCHING   #########################

    @classmethod
    def search_word(cls, word :str, all_properties=False,
                    restrict_search=None, search_category=None) -> Union[List[int], List[dict]]:
        """
        Look up any database-stored words that contains the requested string
        (ignoring case and leading/trailing blanks.)

        Then locate the Content nodes that are indexed by any of those words.

        Return a (possibly empty) list of either the internal database ID's of all the found nodes,
        or a list of their full properties.

        :param word:            A string, typically containing a word or word fragment;
                                    case is ignored, and so are leading/trailing blanks
        :param all_properties:  If True, the properties of the located nodes are returned
                                    alongside their internal database ID's.
                                    Default is False: only return the internal database ID's
        :param restrict_search: If None or an empty list, ignored;
                                    otherwise, it should be a list of internal database ID's to which
                                    the search is to be limited to
        :param search_category: (OPTIONAL) URI of Category.  If supplied, all searching will
                                    be limited to Content Items in this Category
                                    or in any of its sub-categories

        :return:        If all_properties is False,
                            a (possibly empty) list of the internal database ID's
                            of all the found nodes
                        If all_properties is True,
                            a (possibly empty) list of dictionaries with all the data
                            of all the found nodes; each dict contain all of the nodes' attributes,
                            plus keys called 'internal_id' and 'neo4j_labels'
                            EXAMPLE: [{'filename': 'My_Document.pdf', 'internal_id': 66, 'neo4j_labels': ['Content Item']}]
        """
        clean_term = word.strip()   # Zap leading/trailing blanks

        if clean_term == "":
            # This is done as special handling because a blank string would match any word!
            return []

        if all_properties:
            return_statement = "RETURN DISTINCT ci"
        else:
            return_statement = "RETURN DISTINCT id(ci) AS content_id"


        where_additional_clause = ""
        data_binding = {}
        additional_matching = ""

        if restrict_search:
            #print("Restricting search to Content Items with internal ID's: ", restrict_search)
            where_additional_clause += " AND id(ci) IN $restrict_search"
            data_binding["restrict_search"] = restrict_search

        if search_category:
            #print("Restricting search to Content Items under Category with URI: ", search_category)
            additional_matching = "-[:BA_in_category]->(:Category)-[:BA_subcategory_of*0..]->(cat:Category)"
            where_additional_clause += " AND cat.uri = $search_category"
            data_binding["search_category"] = search_category


        q = f'''
            MATCH (w:Word {{`_SCHEMA`: "Word"}})-[:occurs]->(:Indexer)<-[:has_index]-(ci)
            {additional_matching}
            WHERE w.name CONTAINS toLower('{clean_term}')
            {where_additional_clause}
            {return_statement} 
            '''

        #cls.db.debug_query_print(q=q, data_binding=data_binding, method="search_word")


        if all_properties:
            result = cls.db.query_extended(q, data_binding=data_binding, flatten=True)
            NeoSchema.remove_schema_info(result)    # Zap any low-level Schema-related data
        else:
            result = cls.db.query(q, data_binding=data_binding, single_column="content_id")

        return result
