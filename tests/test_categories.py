# *** CAUTION! ***  The database gets cleared out during some of the tests!


import pytest
from BrainAnnex.modules.utilities.comparisons import compare_unordered_lists, compare_recordsets
from neoaccess import NeoAccess
from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema, SchemaCache, SchemaCacheExperimental


# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = NeoAccess(debug=False)
    NeoSchema.set_database(neo_obj)
    yield neo_obj



# ************  CREATE SAMPLE CATEGORIES for the testing  **************

def create_sample_category_1():
    # Schema with patient/result/doctor Classes (each with some Properties),
    # and relationships between the Classes: HAS_RESULT, IS_ATTENDED_BY

    _, sch_1 = NeoSchema.create_class_with_properties(class_name="Categories",
                                                      property_list=["name", "remarks"])

    _, sch_2 = NeoSchema.create_class_with_properties(class_name="result",
                                                      property_list=["biomarker", "value"])

    _, sch_3 = NeoSchema.create_class_with_properties(class_name="doctor",
                                                      property_list=["name", "specialty"])

    NeoSchema.create_class_relationship(from_id=sch_1, to_id=sch_2, rel_name="HAS_RESULT")
    NeoSchema.create_class_relationship(from_id=sch_1, to_id=sch_3, rel_name="IS_ATTENDED_BY")

    return {"patient": sch_1, "result": sch_2, "doctor": sch_3}



def create_sample_category_2():
    # Class "quotes" with relationship named "in_category" to Class "categories";
    # each Class has some properties
    _, sch_1 = NeoSchema.create_class_with_properties(class_name="quotes",
                                                      property_list=["quote", "attribution", "verified"])

    _, sch_2 = NeoSchema.create_class_with_properties(class_name="categories",
                                                      property_list=["name", "remarks"])

    NeoSchema.create_class_relationship(from_id=sch_1, to_id=sch_2, rel_name="in_category")

    return {"quotes": sch_1, "categories": "sch_2"}





def test_get_all_categories(db):
    db.empty_dbase()

