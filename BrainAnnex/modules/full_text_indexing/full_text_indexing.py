import re
import html
from typing import Union, List, Set
from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema


class FullTextIndexing:
    """
    Indexing-related methods, for full-text searching.

    For more info and background info, please see:
        https://julianspolymathexplorations.blogspot.com/2023/08/full-text-search-neo4j-indexing.html

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
    # Note: 2-letter words could be dropped because those don't get indexed
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
                    'must', 'need', 'needs', 'seem', 'seems', 'seemed', 'want', 'wants', 'should', 'shouldn',
                    'will', 'would', 'shall',
                    'get', 'gets', 'got', 'give', 'gives', 'gave',
                    'take', 'takes', 'took', 'taking', 'put', 'bring', 'brings', 'bringing',
                    'see', 'sees', 'given', 'end', 'start', 'starts', 'starting',
                    'ask', 'asks', 'answer', 'answers',
                    'when', 'where', 'which', 'who', 'why', 'what',
                    'no', 'non', 'not', 'yes', 'maybe', 'ok', 'oh',
                    'ie', 'i.e', 'eg', 'e.g',
                    'll', 've', 'so',
                    'good', 'better', 'best', 'well', 'bad',  'worse', 'worst',
                    'just', 'about', 'above', 'again', 'ago',
                    'times', 'date', 'dates', 'today', 'day', 'month', 'year', 'yr', 'days', 'months', 'years',
                    'hour', 'hr', 'minute', 'min', 'second', 'sec', 'pm',
                    'now', 'currently', 'late', 'early', 'soon', 'later', 'earlier', 'already',
                    'after', 'before', 'yet', 'whenever', 'while', 'during', 'ever',
                    'follow', 'follows', 'following', 'along',
                    'never', 'seldom', 'occasionally', 'sometimes',
                    'often', 'always', 'usually', 'eventually', 'typical', 'typically',
                    'almost', 'quite',
                    'frequent', 'ubiquitous', 'usual', 'common', 'commonly',
                    'remarkable', 'impressive',
                    'really', 'approximately',
                    'allow', 'allows', 'allowing',
                    'old', 'older', 'new', 'newer', 'recent', 'recently',
                    'begin', 'began', 'start', 'starting', 'started',
                    'in', 'out', 'here', 'there',
                    'instead', 'alternative', 'alternatively', 'case', 'cases', 'extent',
                    'up', 'down', 'over', 'above', 'under', 'below', 'between', 'among', 'wherever',
                    'next', 'previous', 'other', 'others', 'another', 'thing', 'things',
                    'like', 'as', 'aka', 'akin', 'such', 'fairly', 'actual', 'actually',
                    'likewise', 'similar', 'similarly',
                    'simple', 'simpler', 'simplest',
                    'each', 'any', 'all', 'everyone', 'anyone', 'anybody', 'anything', 'something', 'someone', 'some',
                    'more', 'most', 'mostly', 'additional', 'extra',
                    'less', 'least', 'than', 'enough', 'only', 'further',
                    'everything', 'nothing',
                    'few', 'fewer', 'many', 'multiple', 'much', 'same', 'different', 'equal',
                    'full', 'empty', 'lot', 'very', 'around', 'vary', 'varying',
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
                    'one', 'ones', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine',
                    'first', 'second', 'third', 'last',
                    'include', 'including', 'incl', 'except', 'sure', 'according', 'accordingly',
                    'example', 'examples', 'define', 'defined',
                    'basically', 'essentially', 'called', 'named', 'consider', 'considering', 'however', 'especially', 'etc',
                    'happen', 'happens', 'happening', 'continue', 'continues', 'continuing',
                    'change', 'changes', 'changing', 'changed',
                    'small', 'smaller', 'smallest', 'little', 'brief', 'briefly',
                    'big', 'bigger', 'biggest', 'large', 'larger', 'largest',
                    'low', 'lower', 'lowest', 'high', 'higher', 'highest', 'limited',
                    'increase', 'increased', 'decrease', 'decreased', 'vary', 'varies', 'varying',
                    'consist', 'consists', 'consisting', 'result', 'results', 'resulting',
                    'description', 'descriptions', 'describe', 'describing',
                    'hello', 'hi',
                    're', 'vs', 'ex',
                    'data', 'value', 'values',
                    'obvious', 'obviously', 'clearly',
                    'show', 'shows', 'showing', 'find', 'finds', 'found', 'finding', 'findings', 'respectively']


    # TODO: allow user-specific words, from a configuration file.  For example, for German: ich, du, er, sie, wir, ihr


    ##########   STRING METHODS   ##########

    @classmethod
    def split_into_words(cls, text: str, to_lower_case=True, drop_html=True) -> [str]:
        """
        Lower-level function to index text that may contain HTML.

        Given a string, optionally zap HTML tags, HTML entities (such as &ndash;)
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
        TODO: maybe eliminate the decimal numbers while leaving the integers alone, to allow indexing of (some) integer numbers such as dates
        TODO: consider treating underscores as blanks (maybe optionally?)

        :param text:            A string with the text to parse
        :param to_lower_case:   If True, all text is converted to lower case
        :param drop_html:       Use True if passing HTML text
        :return:                A (possibly empty) list of words in the text,
                                    free of punctuation, HTML and HTML entities such as &ndash;
        """
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
        Higher-level function to index text that may contain HTML.

        From the given text, zap HTML, HTML entities (such as &ndash;) and punctuation;
        then, turn into lower case, and break up into individual words.

        Next, eliminate "words" that match at least one of these EXCLUSION test:
            * are 1 or characters long
            * are numbers
            * contain a digit anywhere (e.g. "50m" or "test2")
            * are in a list of common words

        Finally, eliminate duplicates, and return the set of acceptable, unique words.

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

        # Eliminate "words" that are 1 character long, or that are numbers,
        # or that are in a list of common words.  Don't include duplicates
        word_set = set()    # Empty set

        # Define a regular expression pattern to match numeric characters
        pattern = r"\d"

        for word in split_text:
            if len(word) > 2 \
                    and not word.isnumeric() \
                    and word not in cls.COMMON_WORDS \
                    and not re.search(pattern, word):
                word_set.add(word)      # Add the element to the set, if it passed all the exclusions

        #print("The word set for the index is: ", word_set)

        return word_set




    #############   GRAPH METHODS   #############

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

        TODO: manage indexing.  If done in Cypher:
                                CREATE TEXT INDEX word_lookup FOR (n:Word) ON (n.name)

        :param content_item_class_id: (OPTIONAL) The internal database ID of an existing "Content Item" Class;
                                            if not passed, it gets looked up
        :return:                None
        """

        if content_item_class_id is None:     # Look it up, if not passed
            if NeoSchema.class_name_exists("Content Item"):
                content_item_class_id = NeoSchema.get_class_internal_id(class_name="Content Item")
            else:
                content_item_class_id, _ = NeoSchema.create_class(name="Content Item", strict=False)

        indexer_class_id, _ = NeoSchema.create_class(name="Indexer", strict=True)

        NeoSchema.create_class_with_properties(name="Word", strict=True,
                                               property_list=["name"],
                                               class_to_link_to="Indexer", link_name="occurs", link_dir="OUT")

        NeoSchema.create_class_relationship(from_class=content_item_class_id, to_class=indexer_class_id, rel_name="has_index")



    @classmethod
    def new_indexing(cls, content_item_id :int, unique_words :Set[str], to_lower_case=True) -> None:
        """
        Used to create a new index, linking the given list of unique words
        to the specified data node that represents a "Content Item".
        
        Create a data node of type "Indexer",
        with inbound relationships named "occurs" from "Word" data nodes (pre-existing or newly-created)
        for all the words in the given list.
        Also, create a relationship named "has_index" from an existing "Content Item" data node to the new "Indexer" node.
        TODO: consider combining new_indexing() and update_indexing()

        :param content_item_id: The internal database ID of an existing data node that represents a "Content Item"
        :param unique_words:    A list of strings containing unique words
                                    - for example as returned by extract_unique_good_words()
        :param to_lower_case:   If True, all text is converted to lower case
        :return:                None
        """
        indexer_id = cls.get_indexer_node_id(content_item_id)
        assert indexer_id is None, \
            f"new_indexing(): an index ALREADY exists for the given Content Item node (internal id {content_item_id})"

        # Create a data node of type "Indexer", and link it up to the passed Content Item
        indexer_id = NeoSchema.add_data_node_with_links(class_name ="Indexer",
                                                        links =[{"internal_id": content_item_id, "rel_name": "has_index",
                                                                  "rel_dir": "IN"}])

        cls.populate_index(indexer_id=indexer_id, unique_words=unique_words, to_lower_case=to_lower_case)



    @classmethod
    def populate_index(cls, indexer_id :int, unique_words :Set[str], to_lower_case :bool) -> None:
        """

        :param indexer_id:      Internal database ID of a data node used to hold all the "occurs" relationships
                                    to the various Word nodes
        :param unique_words:    Set of strings, with unique words for the index
        :param to_lower_case:   If True, all text is converted to lower case
        :return:                None
        """
        if to_lower_case:
            unique_words = list(map(str.lower, unique_words))
        else:
            unique_words = list(unique_words)

        # TODO: make more efficient; maybe combine the creation and linking to the Word nodes

        # Locate (if already present), or create, a "Word" data node for each word in the list unique_words
        class_db_id = NeoSchema.get_class_internal_id(class_name="Word")
        result = NeoSchema.add_data_column_merge(class_internal_id=class_db_id,
                                                 property_name="name", value_list=unique_words)
        #print("result: ", result)      # A dict with 2 keys: 'old_nodes' and 'new_nodes'

        word_node_list = result['old_nodes'] + result['new_nodes']      # Join the 2 lists

        # Link all the "Word" nodes (located or created above) to the "Indexer" node,
        # with an "occurs" outbound relationship
        # (in the future, to also perhaps store a count property)
        for word_node_id in word_node_list:
            NeoSchema.add_data_relationship(from_id=word_node_id, to_id=indexer_id, rel_name="occurs")



    @classmethod
    def update_indexing(cls, content_item_id :int, unique_words :Set[str], to_lower_case=True) -> None:
        """
        Used to update an index, linking the given list of unique words
        to the specified "Indexer" data node, which was created by a call to new_indexing()
        at the time the index was first created.
        
        From the given data node of type "Indexer",
        add inbound relationships named "occurs" from "Word" data nodes (pre-existing or newly-created)
        for all the words in the given list.
        Also, create a relationship named "has_index" from an existing "Content Item" data node to the new "Indexer" node.

        Note: if no index exist, an Exception is raised

        :param content_item_id: The internal database ID of an existing "Content Item" data node
        :param unique_words:    A list of strings containing unique words
                                    - for example as returned by extract_unique_good_words()
        :param to_lower_case:   If True, all text is converted to lower case
        :return:                None
        """
        indexer_id = cls.get_indexer_node_id(content_item_id)
        assert indexer_id is not None, \
                    f"update_indexing(): unable to find an index for the given Content Item " \
                    f" (internal id {content_item_id}).  Did you first create an index for it?"

        # Sever all the existing "occurs" relationships to the "Indexer" data node
        # i.e. give a "clean slate" to the "Indexer" data node
        NeoSchema.remove_multiple_data_relationships(node_id=indexer_id, rel_name="occurs", rel_dir="IN", labels="Word")

        cls.populate_index(indexer_id=indexer_id, unique_words=unique_words, to_lower_case=to_lower_case)



    @classmethod
    def get_indexer_node_id(cls, content_item_id :int) -> Union[int, None]:
        """
        Retrieve and return the internal database ID of the "Indexer" data node
        associated to the given Content Item data node.
        If not found, None is returned

        :param content_item_id: The internal database ID of an existing data node
                                    (either of Class "Content Item", or of a Class that is ultimately
                                    an INSTANCE_OF a "Content Item" Class)
        :return:                The internal database ID of the corresponding "Indexer" data node.
                                    If not found, None is returned
        """
        # Prepare a Cypher query
        q = '''
            MATCH (ci)-[:has_index]->(i:Indexer)-[:SCHEMA]->(:CLASS {name: "Indexer"})
            WHERE id(ci) = $content_item_id
            RETURN id(i) AS indexer_id
            '''

        return cls.db.query(q, data_binding={"content_item_id": content_item_id},
                            single_cell="indexer_id")       # Note: will be None if no record found



    @classmethod
    def remove_indexing(cls, content_item_id :int) -> None:
        """
        Drop the "Indexer" node linked to the given Content Item node.
        If no index exists, an Exception is raised

        :param content_item_id: The internal database ID of an existing "Content Item" data node
        :return:                None
        """
        indexer_id = cls.get_indexer_node_id(content_item_id)

        assert indexer_id is not None, \
            f"remove_indexing(): unable to find an index for the given Content Item node" \
            f" (internal id {content_item_id}).  Maybe you already removed it?"

        NeoSchema.delete_data_node(node_id=indexer_id, labels="Indexer", class_node="Indexer")



    @classmethod
    def count_indexed_words(cls, content_item_id :int) -> int:
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
        from BrainAnnex.modules.media_manager.media_manager import MediaManager

        file_list = os.listdir(directory)
        print(f"Total number of files: {len(file_list)}")

        # Index the content of all the files
        i = 1
        for filename in file_list:
            print(f"\n {i} -------------------------\n", filename)
            (basename, suffix) = os.path.splitext(filename)
            q = f"MATCH (n:Notes) WHERE n.basename='{basename}' AND n.suffix='htm' RETURN ID(n) AS node_int_id"
            node_int_id = cls.db.query(q, single_cell="node_int_id")
            print("    node's integer ID: ", node_int_id)
            path = "TBA"
            file_contents = MediaManager.get_from_text_file(path, filename)
            #print(file_contents)
            word_list = FullTextIndexing.extract_unique_good_words(file_contents)
            print(word_list)
            FullTextIndexing.new_indexing(content_item_id = node_int_id, unique_words = word_list)
            i += 1




    #########################   SEARCHING   #########################

    @classmethod
    def search_word(cls, word :str, all_properties=False) -> Union[List[int], List[dict]]:
        """
        Look up in the index for any stored words that contains the requested string
        (ignoring case and leading/trailing blanks.)

        Then locate the Content nodes that are indexed by any of those words.
        Return a (possibly empty) list of either the internal database ID's of all the found nodes,
        or a list of their full attributes.

        :param word:    A string, typically containing a word or word fragment;
                            case is ignored, and so are leading/trailing blanks
        :param all_properties:
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
            return_statement = "RETURN DISTINCT c"
        else:
            return_statement = "RETURN DISTINCT id(c) AS content_id"

        q = f'''MATCH (:CLASS {{name:"Word"}})<-[:SCHEMA]-
             (w:Word)-[:occurs]->(:Indexer)<-[:has_index]-(c)
             WHERE w.name CONTAINS toLower('{clean_term}')
             {return_statement} 
             '''

        #print(q)

        if all_properties:
            result = cls.db.query_extended(q, flatten=True)
        else:
            result = cls.db.query(q, single_column="content_id")
        return result
