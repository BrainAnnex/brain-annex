import pytest
from brainannex import GraphAccess, GraphSchema, Collections, Categories
from utilities.comparisons import compare_recordsets
from app_libraries.data_manager import DataManager

from app_build import create_app


# Provide a Flask app (with a test database connection) that can be used by the various pytests that need it
@pytest.fixture(scope="module")
def app():
    """
    The fixture is created once for all the tests of this Python file (module).
    All tests inside this file reuse the same fixture instance.

    :return:    The object for the Flask app
    """
    graph_db_obj = GraphAccess(debug=False)
    app = create_app(db=graph_db_obj, test=True)
    yield app



@pytest.fixture
def client(app):
    """
    This fixture is created once per test function (using the default scope="function").

    The test database gets emptied out.

    It makes use of test_client(), a built-in testing utility of Flask. It creates an object that behaves like an HTTP client,
    but instead of sending real network requests,
    it calls your Flask application directly inside the same Python process

    The Flask test_client() maintains request context and sometimes session state;
    creating a new client per test, as we do here, ensures:
        no cookie leakage
        no session leakage
        no request context artifacts
        predictable isolation

    :param app: The object for the Flask app
    :return:
    """
    # Untested optional method:
    #with app.test_client() as client:
        #yield client

    db = app.config['DATABASE']
    db.empty_dbase()            # Empty out the test database

    app.config["LOGIN_DISABLED"] = True     # Disable the enforcement of logins
                                            # Otherwise, 302 status will be returned, as a re-direct to login page

    return app.test_client()




def test_get_class_properties_api(client):
    endpoint = "get_class_properties"

    json = '{"class_name": "Quote"}'
    # Note: a URL-safe version of the above string would be '%7B%22class_name%22%3A%20%22Quote%22%7D'

    request = f"/BA/api/{endpoint}?json={json}"
    response = client.get(request)
    # The response is an object of type 'werkzeug.test.WrapperTestResponse'
    assert response.status_code == 200
    assert response.json["status"] == "ok"
    assert response.json["payload"] == []   # The database is empty


    # Populate the database
    GraphSchema.create_class_with_properties(name="Quote", properties =["Author", "Text"])

    response = client.get(request)
    assert response.status_code == 200
    assert response.json["status"] == "ok"
    assert response.json["payload"] == ['Author', 'Text']


    json = '{"fake_key": "Quote"}'      # Missing required key
    request = f"/BA/api/{endpoint}?json={json}"
    response = client.get(request)
    assert response.status_code == 200
    assert response.json["status"] == "error"
    assert response.json["error_message"] == "Missing required value for either `class_name` or `label` in the JSON data"



def test_get_links_api(client):
    endpoint = "get_links"

    data = 'Company'

    request = f"/BA/api/{endpoint}/{data}"
    response = client.get(request)
    assert response.status_code == 200
    assert response.json["status"] == "ok"
    assert response.json["payload"] == {"in" :[], "out": []}   # The database is empty


    # Populate the database
    GraphSchema.create_class(name="Company")

    response = client.get(request)
    assert response.status_code == 200
    assert response.json["status"] == "ok"
    assert response.json["payload"] == {"in" :[], "out": []}    # Still no links


    GraphSchema.create_class(name="Person")
    GraphSchema.create_class_relationship(from_class="Company", to_class="Person", rel_name="EMPLOYS")

    response = client.get(request)
    assert response.status_code == 200
    assert response.json["status"] == "ok"
    assert response.json["payload"] == {"in" :[], "out": ["EMPLOYS"]}
