import pytest
from BrainAnnex.modules.utilities.comparisons import *
from BrainAnnex.modules.full_text_indexing.full_text_indexing import FullTextIndexing



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