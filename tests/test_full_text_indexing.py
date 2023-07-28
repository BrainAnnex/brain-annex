import pytest
from neoaccess import NeoAccess
from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema
from BrainAnnex.modules.full_text_indexing.full_text_indexing import FullTextIndexing
from BrainAnnex.modules.utilities.comparisons import compare_unordered_lists



# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = NeoAccess(debug=False)
    NeoSchema.set_database(neo_obj)
    FullTextIndexing.db = neo_obj
    yield neo_obj




def test_extract_unique_good_words():
    with pytest.raises(Exception):
        FullTextIndexing.extract_unique_good_words(None)

    with pytest.raises(Exception):
        FullTextIndexing.extract_unique_good_words(123)

    result = FullTextIndexing.extract_unique_good_words("Hello world!")
    assert result == ["hello", "world"]

    result = FullTextIndexing.extract_unique_good_words("Hello to the world! And, YES - why not - let's say, hello again as well :)")
    assert result == ["hello", "world", "say"]

    result = FullTextIndexing.extract_unique_good_words("I shout, and shout - and REALLY, REALLY shout because I can!")
    assert result == ["shout"]

    result = FullTextIndexing.extract_unique_good_words("<span>OK, this is    just a very CRAZY related issue in two empty parts; and bad HTML format!")
    assert result == ["crazy", "html", "format"]

    text = '<p>Mr. Joe&amp;sons<br>A Long&ndash;Term business! Find it at &gt; (http://example.com/home)<br>Visit Joe&#39;s &quot;NOW!&quot;</p>'
    result = FullTextIndexing.extract_unique_good_words(text)
    assert result == ['mr', 'joe', 'sons', 'long', 'term', 'business', 'find', 'example', 'home', 'visit']



def test_split_into_words():
    result = FullTextIndexing.split_into_words("Hello world!")
    assert result == ["hello", "world"]

    text = '<p>Mr. Joe&amp;sons<br>A Long&ndash;Term business! Find it at &gt; (http://example.com/home)<br>Visit Joe&#39;s &quot;NOW!&quot;</p>'

    result = FullTextIndexing.split_into_words(text, to_lower_case=False)
    assert result == ['Mr', 'Joe', 'sons', 'A', 'Long', 'Term', 'business', 'Find', 'it', 'at', 'http', 'example', 'com', 'home', 'Visit', 'Joe', 's', 'NOW']

    result = FullTextIndexing.split_into_words(text, to_lower_case=True)
    assert result == ['mr', 'joe', 'sons', 'a', 'long', 'term', 'business', 'find', 'it', 'at', 'http', 'example', 'com', 'home', 'visit', 'joe', 's', 'now']



def test_initialize_schema(db):
    pass


def test_new_indexing(db):
    db.empty_dbase()

    # Set up all the needed Schema
    NeoSchema.create_class_with_properties(class_name="Content Item", schema_type="S",
                                           property_list=["filename"])
    FullTextIndexing.initialize_schema()

    # Create a data node of type "Content Item"...
    content_id = NeoSchema.add_data_point(class_name="Content Item", properties={"filename": "My_Document.pdf"})
    # ...and then index some words to it
    FullTextIndexing.new_indexing(content_item_id=content_id, unique_words=["lab", "research", "R/D"])

    assert NeoSchema.count_data_nodes_of_class(class_id="Word") == 3
    assert NeoSchema.count_data_nodes_of_class(class_id="Indexer") == 1
    assert NeoSchema.count_data_nodes_of_class(class_id="Content Item") == 1

    assert FullTextIndexing.count_indexed_words(content_id) == 3

    q = '''
        MATCH (w:Word)-[:SCHEMA]->(wc:CLASS {name: "Word"})-[:occurs]->(ic:CLASS {name:"Indexer"})
        <-[:SCHEMA]-(i:Indexer)<-[:occurs]-(w)
        RETURN w.name AS name
        '''
    res = db.query(q, single_column="name")
    #print(res)
    assert compare_unordered_lists(res, ["lab", "research", "R/D"])


    # Now test a scenario where some Word node already exist

    # Create a data node of type "Content Item"...
    content_id = NeoSchema.add_data_point(class_name="Content Item", properties={"filename": "My_Other_Document.txt"})
    # ...and then index some words to it
    FullTextIndexing.new_indexing(content_item_id=content_id, unique_words=["research", "science"])

    assert NeoSchema.count_data_nodes_of_class(class_id="Word") == 4    # One word from earlier got re-used
    assert NeoSchema.count_data_nodes_of_class(class_id="Indexer") == 2
    assert NeoSchema.count_data_nodes_of_class(class_id="Content Item") == 2

    assert FullTextIndexing.count_indexed_words(content_id) == 2

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
    assert compare_unordered_lists(res, ["lab", "research", "R/D", "science"])



def test_update_indexing(db):
    db.empty_dbase()

    # Set up all the needed Schema
    NeoSchema.create_class_with_properties(class_name="Content Item", schema_type="S",
                                           property_list=["filename"])
    FullTextIndexing.initialize_schema()

    # Create a data node of type "Content Item"...
    content_id = NeoSchema.add_data_point(class_name="Content Item", properties={"filename": "My_Document.pdf"})
    # ...and then index some words to it
    FullTextIndexing.new_indexing(content_item_id=content_id, unique_words=["lab", "research", "R/D"])

    assert FullTextIndexing.count_indexed_words(content_id) == 3
    assert NeoSchema.count_data_nodes_of_class("Word") == 3
    assert NeoSchema.count_data_nodes_of_class(class_id="Indexer") == 1

    indexer_node_id = FullTextIndexing.get_indexer_node_id(content_id)


    # Now, change the indexing (of that same Content Item) to a new set of words
    FullTextIndexing.update_indexing(content_item_id=content_id, unique_words=["closed", "renovation"])

    assert FullTextIndexing.count_indexed_words(content_id) == 2
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
    FullTextIndexing.update_indexing(content_item_id=content_id, unique_words=["research", "neuroscience"])

    assert FullTextIndexing.count_indexed_words(content_id) == 2
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



def test_prepare_word_node_OBSOLETE(db):
    db.empty_dbase()
    _ , word_class_id = NeoSchema.create_class_with_properties(class_name="Word", schema_type="S",
                                                               property_list=["name"])
    FullTextIndexing.prepare_word_node_OBSOLETE("life")

