from brainannex import DocumentationGenerator


def test_prepare_preview_table():
    data = [("a", "b", "c"), ("x", "y", "z")]

    result = DocumentationGenerator.prepare_preview_table(data)
    #print(result)
    assert result == "<table border='1' style='border-collapse: collapse'>" \
                        "<tr><td>a</td><td>b</td><td>c</td></tr>" \
                        "<tr><td>x</td><td>y</td><td>z</td></tr>" \
                     "</table>"



def test_clean_up_args():
    assert DocumentationGenerator.clean_up_args("cls") == ""
    assert DocumentationGenerator.clean_up_args("   cls        ") == ""

    assert DocumentationGenerator.clean_up_args("self") == ""
    assert DocumentationGenerator.clean_up_args("       self ") == ""

    assert DocumentationGenerator.clean_up_args("   cls, r, x    ") == "r, x"
    assert DocumentationGenerator.clean_up_args("   self   , r:int,  x :list    ") == "r:int,  x :list"
