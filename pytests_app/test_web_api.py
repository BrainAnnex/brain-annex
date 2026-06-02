import pytest
from brainannex import GraphAccess, GraphSchema
from utilities.comparisons import compare_recordsets
from app_libraries.data_manager import DataManager

from app_build import create_app    # In top-level file app_build.py


# Provide a Flask app object (with a test database connection)
# that can be used by the various pytests that need it
@pytest.fixture(scope="module")
def app():
    """
    The fixture is created once for all the tests of this Python file (module).
    All tests inside this file reuse the same fixture instance.

    :return:    The object for the Flask app
    """
    graph_db_obj = GraphAccess(debug=False)
    app = create_app(db=graph_db_obj, test=True)    # An instantiated Flask object
                                                    # This instantiation also initializes various modules, such as GraphSchema
    yield app



@pytest.fixture
def client(app):
    """
    This fixture is created once per test function (using the default pytest scope="function").

    The test database gets emptied out.

    It makes use of test_client(), a built-in testing utility of Flask.
    It creates an object that behaves like an HTTP client,
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

    app.config["LOGIN_DISABLED"] = True     # Disable the enforcement of logins (a built-in feature)
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



def test_class_properties_full_data_api(client):
    endpoint = "class-properties-full-data"

    json = '{"class_name": "Quote"}'

    request = f"/BA/api/{endpoint}?json={json}"
    response = client.get(request)
    # The response is an object of type 'werkzeug.test.WrapperTestResponse'
    assert response.status_code == 200
    assert response.json["status"] == "ok"
    assert response.json["payload"] == []   # The database is empty


    # Populate the database
    GraphSchema.create_class_with_properties(name="Quote", properties=["text", "attribution", "verified"])
    prop_ids = [GraphSchema.get_property_internal_id(class_name="Quote", property_name=p)
                    for p in ["text", "attribution", "verified"] ]

    GraphSchema.set_property_attribute(class_name="Quote", prop_name="text",
                                       attribute_name="description", attribute_value="the body of the quote")

    GraphSchema.set_property_attribute(class_name="Quote", prop_name="text",
                                       attribute_name="system", attribute_value=False)

    GraphSchema.set_property_attribute(class_name="Quote", prop_name="text",
                                       attribute_name="dtype", attribute_value="string")

    GraphSchema.set_property_attribute(class_name="Quote", prop_name="text",
                                       attribute_name="required", attribute_value=True)

    GraphSchema.set_property_attribute(class_name="Quote", prop_name="text",
                                       attribute_name= "format", attribute_value="6,50")

    GraphSchema.set_property_attribute(class_name="Quote", prop_name="verified",
                                       attribute_name="dtype", attribute_value="boolean")

    GraphSchema.set_property_attribute(class_name="Quote", prop_name="verified",
                                       attribute_name="required", attribute_value=False)


    response = client.get(request)
    assert response.status_code == 200
    assert response.json["status"] == "ok"
    assert response.json["payload"] == [    {'name': 'text',        'entity_id': 'schema-2', '_internal_id': prop_ids[0],  'dtype': 'string', 'system': False,
                                             'format': '6,50', 'description': 'the body of the quote', 'required': True},
                                            {'name': 'attribution', 'entity_id': 'schema-3', '_internal_id': prop_ids[1]},
                                            {'name': 'verified',    'entity_id': 'schema-4', '_internal_id': prop_ids[2],  'dtype': 'boolean', 'required': False}
                                         ]


    json = '{"class_name": "I dont exist"}'      # Missing Class
    request = f"/BA/api/{endpoint}?json={json}"
    response = client.get(request)
    assert response.status_code == 200
    assert response.json["status"] == "ok"
    assert response.json["payload"] == [ ]


    GraphSchema.create_class(name="Car")    # Class without Properties

    json = '{"class_name": "Car"}'
    request = f"/BA/api/{endpoint}?json={json}"
    response = client.get(request)
    assert response.status_code == 200
    assert response.json["status"] == "ok"
    assert response.json["payload"] == [ ]


    json = '{"class_name": "Car"}'
    request = f"/BA/api/{endpoint}?jXYZson={json}"  # Malformed GET request
    response = client.get(request)
    assert response.status_code == 400
    assert response.json["status"] == "error"

    json = '{"class_name"::: "Car"}'                # Malformed JSON-encoded string
    request = f"/BA/api/{endpoint}?json={json}"
    response = client.get(request)
    assert response.status_code == 400
    assert response.json["status"] == "error"
    print(response.json["error_message"])



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



def test_create_schema_from_data_POST(client):
    endpoint = "create-schema-from-data"
    url = f"/BA/api/{endpoint}"

    db = GraphSchema.db

    # Populate the database
    db.create_node(labels="Car")    # This node lacks any properties

    response = client.post(url, json={"label": "Car"})
    # The response is an object of type 'werkzeug.test.WrapperTestResponse'

    assert response.status_code == 200
    assert response.json["status"] == "ok"
    result = response.json["payload"]   # The internal database ID of the newly-created Class node

    # Verify we now have a `Car` Class, with no Properties
    assert GraphSchema.class_name_exists("Car")
    assert GraphSchema.get_class_internal_id("Car") == result
    assert GraphSchema.get_class_properties(class_node="Car") == []
    assert not GraphSchema.is_strict_class("Car")


    db.create_node(labels="Person", properties={"name": "Julian"})
    db.create_node(labels="Person", properties={"name": "Val", "age": 22})
    db.create_node(labels="Person", properties={"name": "Liz", "Medical #": "0425"})


    response = client.post(url, json={"label": "Person"})
    assert response.status_code == 200
    assert response.json["status"] == "ok"
    result = response.json["payload"]   # The internal database ID of the newly-created Class node

    # Verify we now have a `Person` Class, with the 3 Properties inferred from the data
    assert GraphSchema.class_name_exists("Person")
    assert GraphSchema.get_class_internal_id("Person") == result
    assert GraphSchema.get_class_properties(class_node="Person") == ["age", "Medical #", "name"]    # in alphabetic order
    assert not GraphSchema.is_strict_class("Person")


    response = client.post(url, json={"xyz": "Person"})   # Missing key 'label'
    assert response.status_code == 400
    assert response.json["status"] == "error"
    assert response.json["error_message"] == "/create-schema-from-data : A key named `label` must be present in the dictionary in the body of the request"


    response = client.post(url, json={"label": "NON_EXISTENT"})     # No such nodes exist
    assert response.status_code == 422
    assert response.json["status"] == "error"
    assert type(response.json["error_message"]) == str
    #print(response.json["error_message"])


    response = client.post(url, json={"label": "Person"})   # A Class by that name already exists
    assert response.status_code == 422
    assert response.json["status"] == "error"
    assert type(response.json["error_message"]) == str
    #print(response.json["error_message"])
