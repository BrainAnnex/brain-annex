import pytest
from neoaccess import NeoAccess
from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema
from BrainAnnex.modules.full_text_indexing.full_text_indexing import FullTextIndexing
from BrainAnnex.modules.utilities.comparisons import compare_unordered_lists, compare_recordsets



# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = NeoAccess(debug=False)
    NeoSchema.set_database(neo_obj)
    FullTextIndexing.db = neo_obj
    yield neo_obj



def setup_sample_index(db) -> int:
    """
    Set up a new indexing system, and create a sample Content node; return its internal database ID
    """
    db.empty_dbase()

    # Set up all the needed Schema
    NeoSchema.create_class_with_properties(name="Content Item", strict=True,
                                           property_list=["filename"])
    FullTextIndexing.initialize_schema()

    # Create a data node of type "Content Item"...
    content_id = NeoSchema.create_data_node(class_node="Content Item", properties={"filename": "My_Document.pdf"})

    return content_id



def test_split_into_words():
    # Tests of the lower-level function
    result = FullTextIndexing.split_into_words("Hello world!")
    assert result == ["hello", "world"]

    text = '<p>Mr. Joe&amp;sons<br>A Long&ndash;Term business! Find it at &gt; (http://example.com/home)<br>Visit Joe&#39;s &quot;NOW!&quot;</p>'

    result = FullTextIndexing.split_into_words(text, to_lower_case=False)
    assert result == ['Mr', 'Joe', 'sons', 'A', 'Long', 'Term', 'business', 'Find', 'it', 'at', 'http', 'example', 'com', 'home', 'Visit', 'Joe', 's', 'NOW']

    result = FullTextIndexing.split_into_words(text, to_lower_case=True)
    assert result == ['mr', 'joe', 'sons', 'a', 'long', 'term', 'business', 'find', 'it', 'at', 'http', 'example', 'com', 'home', 'visit', 'joe', 's', 'now']


    # Examples with no usable text
    assert FullTextIndexing.split_into_words("") == []
    assert FullTextIndexing.split_into_words("           ") == []
    assert FullTextIndexing.split_into_words(" + - / % <br> &amp; <h1>...</h1> ? ") == []


    # Explore numeric values, which are often not indexed
    text = "2.3 5 99 -99 0 4912.42"
    assert FullTextIndexing.split_into_words(text) == ['2', '3', '5', '99', '99', '0', '4912', '42']


    # Explore situations where we don't want to dropping HTML from non-HTML text
    text = " house price hopefully < 400000 but it is certainly > 200000     "
    assert FullTextIndexing.split_into_words(text, drop_html=False) == ["house", "price", "hopefully", "400000", "but", "it", "is", "certainly", "200000"]
    # If the text had been interpreted as HTML, tha part between "<" and ">" would have been dropped!
    assert FullTextIndexing.split_into_words(text, drop_html=True) == ["house", "price", "hopefully", "200000"]


    text = '''
        Seven key ideas that\nlie at the heart of present-day machine-learning algorithms and that\nmay apply equally well to our brains—seven different definitions of\nwhat “learning” means.\nLEARNING IS ADJUSTING THE PARAMETERS OF A MENTAL MODEL\nAdjusting a mental model is sometimes very simple. How, for\nexample, do we reach out to an object that we see? In the\nseventeenth century, René Descartes (1596–1650) had already\nguessed that our nervous system must contain processing loops that\ntransform visual inputs into muscular commands
        '''
    result = FullTextIndexing.split_into_words(text, to_lower_case=True)
    assert result == ['seven', 'key', 'ideas', 'that', 'lie', 'at', 'the', 'heart', 'of', 'present', 'day', 'machine', 'learning', 'algorithms',
            'and', 'that', 'may', 'apply', 'equally', 'well', 'to', 'our', 'brains', 'seven', 'different', 'definitions', 'of', 'what', 'learning',
            'means', 'learning', 'is', 'adjusting', 'the', 'parameters', 'of', 'a', 'mental', 'model', 'adjusting', 'a', 'mental', 'model', 'is',
            'sometimes', 'very', 'simple', 'how', 'for', 'example', 'do', 'we', 'reach', 'out', 'to', 'an', 'object', 'that', 'we', 'see', 'in',
            'the', 'seventeenth', 'century', 'rené', 'descartes', '1596', '1650', 'had', 'already', 'guessed', 'that', 'our', 'nervous', 'system',
            'must', 'contain', 'processing', 'loops', 'that', 'transform', 'visual', 'inputs', 'into', 'muscular', 'commands']



def test_extract_unique_good_words():
    # Tests of the higher-level function.
    # NOTE: subject to changes if the list of "Common Words" is altered
    with pytest.raises(Exception):
        FullTextIndexing.extract_unique_good_words(None)    # Not a string

    with pytest.raises(Exception):
        FullTextIndexing.extract_unique_good_words(123)     # Not a string

    result = FullTextIndexing.extract_unique_good_words("Hello world!")
    assert result == {"world"}

    result = FullTextIndexing.extract_unique_good_words("Hello to the world! And, YES - why not - let's say, hello again as well :)")
    assert result == {"world", "say"}

    result = FullTextIndexing.extract_unique_good_words("I shout, and shout - and REALLY, REALLY shout because I can!")
    assert result == {"shout"}

    result = FullTextIndexing.extract_unique_good_words("<span>OK, this is    just a very CRAZY related issue in two empty parts; and bad HTML format!")
    assert result == {"crazy", "html", "format"}

    text = '<p>Mr. Joe&amp;sons<br>A Long&ndash;Term business! Find it at &gt; (http://example.com/home)<br>Visit Joe&#39;s &quot;NOW!&quot;</p>'
    result = FullTextIndexing.extract_unique_good_words(text)
    assert result == {'joe', 'sons', 'long', 'term', 'business', 'home', 'visit'}


    # Examples with no usable text, returning an empty set
    assert FullTextIndexing.extract_unique_good_words("") == set()
    assert FullTextIndexing.extract_unique_good_words("           ") == set()
    assert FullTextIndexing.extract_unique_good_words(" + - / % <br> &amp; <h1>...</h1> ? ") == set()


    # Explore numeric values, which are not indexed
    text = "2.3 5 99 -99 0 4912.42 -124 100 2023"
    assert FullTextIndexing.extract_unique_good_words(text) == set()


    text = '''
        Seven key ideas that\nlie at the heart of present-day machine-learning algorithms and that\nmay 
        apply equally well to our brains—seven different definitions of\nwhat “learning” means.\nLEARNING 
        IS ADJUSTING THE PARAMETERS OF A MENTAL MODEL\nAdjusting a mental model is sometimes very simple. 
        How, for\nexample, do we reach out to an object that we see? In the\nseventeenth century, René 
        Descartes (1596–1650) had already\nguessed that our nervous system must contain processing 
        loops that\ntransform visual inputs into muscular commands
        '''
    result = FullTextIndexing.extract_unique_good_words(text, drop_html=False)
    assert result == {'learning', 'adjusting', 'visual', 'key', 'inputs', 'parameters', 'nervous', 'equally', 'object', 'model', 'heart',
            'descartes', 'definitions', 'system', 'algorithms', 'processing', 'commands', 'contain', 'ideas', 'mental', 'reach', 'brains',
            'rené', 'means', 'machine', 'lie', 'loops', 'century', 'apply', 'seventeenth', 'guessed', 'muscular', 'transform', 'present'}


    text = '''
        What Are the\xa0High-Clearance Drugs?\nHigh-clearance drugs are liver blood flow dependent. 
        The hepatic elimination of [...]\nDosing in\xa0Liver Disease\n• Antipsychotics\n• Beta-blockers 
        (most)\n• Calcium channel blockers\n• Lignocaine\n• Nitrates\n• Opioids (most)\n• SSRIs\n• For 
        severe liver dysfunction (albumin<30\xa0g/L, INR >1.2):\n (a) If the drug is a high-clearance drug 
        (liver blood flow dependent) \nreduce dose by 50%:\n1 General Pharmacology\n
        '''
    result = FullTextIndexing.extract_unique_good_words(text, drop_html=False)
    assert result == {"clearance", "drugs", "liver", "blood", "flow", "dependent", "hepatic", "elimination",
                    "dosing", "disease", "antipsychotics", "beta", "blockers",
                    "calcium", "channel", "lignocaine", "nitrates", "opioids", "ssris", "severe", "dysfunction",
                    "albumin", "inr", "drug", "reduce", "dose", "general", "pharmacology"}


    text = "A form with the field: Name______ .  My answer:  ___Julian____"
    result = FullTextIndexing.extract_unique_good_words(text, drop_html=False)
    assert result == {"form", "field", "julian"}



def test_initialize_schema(db):
    pass



def test_new_indexing(db):
    # Set up a new indexing system, and create a sample Content node
    content_id = setup_sample_index(db)
    # ...and then index some words to it
    FullTextIndexing.new_indexing(internal_id=content_id,
                                  unique_words={"lab", "research", "R/D"}, to_lower_case=True)

    with pytest.raises(Exception):
        # Cannot create a new index, when one already exists
        FullTextIndexing.new_indexing(internal_id=content_id, unique_words={"duplicate", "index"})

    assert NeoSchema.count_data_nodes_of_class(class_id="Word") == 3
    assert NeoSchema.count_data_nodes_of_class(class_id="Indexer") == 1
    assert NeoSchema.count_data_nodes_of_class(class_id="Content Item") == 1

    assert FullTextIndexing.number_of_indexed_words(content_id) == 3

    q = '''
        MATCH (w:Word)-[:SCHEMA]->(wc:CLASS {name: "Word"})-[:occurs]->(ic:CLASS {name:"Indexer"})
        <-[:SCHEMA]-(i:Indexer)<-[:occurs]-(w)
        RETURN w.name AS name
        '''
    res = db.query(q, single_column="name")
    #print(res)
    assert compare_unordered_lists(res, ["lab", "research", "r/d"])


    # Now test a scenario where some Word node already exist

    # Create a data node of type "Content Item"...
    content_id = NeoSchema.create_data_node(class_node="Content Item", properties={"filename": "My_Other_Document.txt"})
    # ...and then index some words to it
    FullTextIndexing.new_indexing(internal_id=content_id, unique_words={"research", "science"}, to_lower_case=True)

    assert NeoSchema.count_data_nodes_of_class(class_id="Word") == 4    # One word from earlier got re-used
    assert NeoSchema.count_data_nodes_of_class(class_id="Indexer") == 2
    assert NeoSchema.count_data_nodes_of_class(class_id="Content Item") == 2

    assert FullTextIndexing.number_of_indexed_words(content_id) == 2

    q = '''
        MATCH (ci_cl:CLASS {name:"Content Item"})-[:has_index]->(CLASS {name:"Indexer"})
        <-[:occurs]-(:CLASS {name:"Word"})
        <-[:SCHEMA]-(w:Word)-[:occurs]
        ->(:Indexer)
        <-[:has_index]-(:`Content Item`)-[:SCHEMA]
        ->(ci_cl)
        RETURN DISTINCT w.name AS name
        '''
    res = db.query(q, single_column="name")
    #print(res)
    assert compare_unordered_lists(res, ["lab", "research", "r/d", "science"])



def test_update_indexing(db):
    # Set up a new indexing system, and create a sample Content node
    content_id = setup_sample_index(db)

    with pytest.raises(Exception):
        # Cannot update an index that hasn't yet been created
        FullTextIndexing.update_indexing(content_uri=content_id, unique_words={"impossible"})

    # Index some words to or Content Item
    FullTextIndexing.new_indexing(internal_id=content_id, unique_words={"lab", "research", "R/D"})

    assert FullTextIndexing.number_of_indexed_words(content_id) == 3
    assert NeoSchema.count_data_nodes_of_class("Word") == 3
    assert NeoSchema.count_data_nodes_of_class(class_id="Indexer") == 1

    indexer_node_id = FullTextIndexing.get_indexer_node_id(content_id)


    # Now, change the indexing (of that same Content Item) to a new set of words
    FullTextIndexing.update_indexing(content_uri=content_id, unique_words={"closed", "renovation"})

    assert FullTextIndexing.number_of_indexed_words(content_id) == 2
    assert NeoSchema.count_data_nodes_of_class("Word") == 5
    assert NeoSchema.count_data_nodes_of_class(class_id="Indexer") == 1

    q = '''
        MATCH (w:Word)-[:SCHEMA]->(wc:CLASS {name: "Word"})-[:occurs]->(ic:CLASS {name:"Indexer"})
        <-[:SCHEMA]-(:Indexer)<-[:occurs]-(w)
        RETURN w.name AS name
        '''
    res = db.query(q, single_column="name")
    assert compare_unordered_lists(res, ["closed", "renovation"])
    assert FullTextIndexing.get_indexer_node_id(content_id) == indexer_node_id  # Still the same node


    # Now,again change the indexing (of that same Content Item) to a new set of words - this time,
    # partially overlapping with existing Word nodes
    FullTextIndexing.update_indexing(content_uri=content_id, unique_words={"research", "neuroscience"})

    assert FullTextIndexing.number_of_indexed_words(content_id) == 2
    assert NeoSchema.count_data_nodes_of_class("Word") == 6
    assert NeoSchema.count_data_nodes_of_class(class_id="Indexer") == 1

    q = '''
        MATCH (w:Word)-[:SCHEMA]->(wc:CLASS {name: "Word"})-[:occurs]->(ic:CLASS {name:"Indexer"})
        <-[:SCHEMA]-(:Indexer)<-[:occurs]-(w)
        RETURN w.name AS name
        '''
    res = db.query(q, single_column="name")
    assert compare_unordered_lists(res, ["research", "neuroscience"])
    assert FullTextIndexing.get_indexer_node_id(content_id) == indexer_node_id  # Still the same node



def test_remove_indexing(db):
    # Set up a new indexing system, and create a sample Content node
    content_id = setup_sample_index(db)

    with pytest.raises(Exception):
        # Cannot remove an index not yet created
        FullTextIndexing.remove_indexing(content_id)

    # Index some words to our "Content Item"
    FullTextIndexing.new_indexing(internal_id=content_id, unique_words={"lab", "research", "R/D"})

    assert FullTextIndexing.number_of_indexed_words(content_id) == 3
    assert NeoSchema.count_data_nodes_of_class("Word") == 3
    assert NeoSchema.count_data_nodes_of_class(class_id="Indexer") == 1

    indexer_node_id = FullTextIndexing.get_indexer_node_id(content_id)


    # Now remove the indexing for our "Content Item" node
    FullTextIndexing.remove_indexing(content_id)

    assert FullTextIndexing.number_of_indexed_words(content_id) == 0
    assert NeoSchema.count_data_nodes_of_class("Word") == 3             # The words are still there
    assert NeoSchema.count_data_nodes_of_class(class_id="Indexer") == 0 # The Indexer node is gone

    assert db.get_nodes(match=indexer_node_id) == []                    # No such node exists anymore



def test_get_indexer_node_id(db):
    db.empty_dbase()

    assert FullTextIndexing.get_indexer_node_id(internal_id= -1) is None   # Bad ID

    assert FullTextIndexing.get_indexer_node_id(internal_id="Not an integer") is None   # Bad ID

    assert FullTextIndexing.get_indexer_node_id(internal_id= 1) is None  # The dbase is empty

    # Set up a new indexing system, and create a sample Content node
    content_id = setup_sample_index(db)
    # ...and then index some words to it
    FullTextIndexing.new_indexing(internal_id=content_id, unique_words={"lab", "research", "R/D"})

    assert NeoSchema.count_data_nodes_of_class(class_id="Indexer") == 1

    indexer_node_id = FullTextIndexing.get_indexer_node_id(content_id)

    print(indexer_node_id)

    # Verify the 3 total relationships from the "Word" data nodes to the "Indexer" data node
    match_from = db.match(labels="Word")
    assert db.number_of_links(match_from=match_from, match_to=indexer_node_id, rel_name="occurs") == 3

    # Verify the relationship from the "Content Item" data node to the "Indexer" data node
    assert db.number_of_links(match_from=content_id, match_to=indexer_node_id, rel_name="has_index") == 1

    # Verify that the "Indexer" data node is indeed associated to the schema Class called "Indexer"
    assert NeoSchema.class_of_data_node(node_id=indexer_node_id, labels="Indexer") == "Indexer"




############################   SEARCHING   ############################

def test_search_word(db):
    # Set up a new indexing system, and create a sample Content node
    content_id_1 = setup_sample_index(db)
    # ...and then index some words to it
    FullTextIndexing.new_indexing(internal_id=content_id_1,
                                  unique_words={"lab", "R/D", "SHIPPING","absence"},
                                  to_lower_case=True)

    assert FullTextIndexing.search_word("missing") == []                # Word not present

    assert FullTextIndexing.search_word("") == []                       # Missing search term

    assert FullTextIndexing.search_word("lab") == [content_id_1]
    assert FullTextIndexing.search_word("shipping") == [content_id_1]   # Case-insensitive
    assert FullTextIndexing.search_word("  Shipping   ") == [content_id_1]   # Ignores leading/trailing blanks
    assert FullTextIndexing.search_word("ship") == [content_id_1]       # Substring
    assert FullTextIndexing.search_word("R/D") == [content_id_1]
    assert FullTextIndexing.search_word("r/d") == [content_id_1]        # Case-insensitive
    assert FullTextIndexing.search_word("ab") == [content_id_1]         # This will match both "lab" and "absence"

    result = FullTextIndexing.search_word("  Shipping   ", all_properties=True)
    assert result == [{'filename': 'My_Document.pdf', 'internal_id': content_id_1, 'neo4j_labels': ['Content Item']}]


    # Add a 2nd data node of type "Content Item"...
    content_id_2 = NeoSchema.create_data_node(class_node="Content Item", properties={"filename": "some_other_file.txt"})
    # ...and then index some words to it
    FullTextIndexing.new_indexing(internal_id=content_id_2, unique_words={"ship", "lab", "glassware"})

    assert FullTextIndexing.search_word("missing") == []                # Word not present

    assert FullTextIndexing.search_word("glassware") == [content_id_2]
    assert FullTextIndexing.search_word("r/d") == [content_id_1]
    assert compare_unordered_lists(FullTextIndexing.search_word("lab"), [content_id_1, content_id_2])

    assert FullTextIndexing.search_word("shipping") == [content_id_1]   # "shipping" only matches one...
    assert compare_unordered_lists(FullTextIndexing.search_word("ship"), [content_id_1, content_id_2])  # ...while "ship" matches both

    result = FullTextIndexing.search_word("ship", all_properties=True)
    expected = [{'filename': 'My_Document.pdf', 'internal_id': content_id_1, 'neo4j_labels': ['Content Item']},
                {'filename': 'some_other_file.txt', 'internal_id': content_id_2, 'neo4j_labels': ['Content Item']}
               ]

    assert compare_recordsets(result, expected)
