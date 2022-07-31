import pytest
from BrainAnnex.modules.utilities.comparisons import *
from BrainAnnex.modules.full_text_indexing.full_text_indexing import FullTextIndexing



def test_extract_unique_good_words():
    result = FullTextIndexing.extract_unique_good_words("Hello world!")
    assert result == ["hello", "world"]

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