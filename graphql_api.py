import strawberry
from strawberry.flask.views import GraphQLView
from brainannex import GraphSchema

"""
EXAMPLE:
Enter into the large window of the UI at http://localhost:5000/graphql , the following query:

{
    people {
        name
        age
        worksAt {
            location
            name
        }
    }
}
  
Notes: 
- `people` is a `field` of the root Query type (Its resolver returns a list of Person objects)
- `name` is a field of the `Person` type, nested inside the selection for `people` (GraphQL retrieves that field for each returned person)

- The outer braces define the selection set: the fields you want to retrieve from the root query object.
- The inner braces define the selection set for each `Person` returned by `people`,
    and for each `Company` returned by `works_at`
    
    
    
    
Another example (upon adding a second root query field):
{
  labels {
    name
  }
}
"""

# GraphQL object types
@strawberry.type
class Company:
    name: str
    location: str

@strawberry.type
class Person:
    name: str
    age: int
    works_at: Company

@strawberry.type
class DatabaseLabel:
    name: str



# Root of the query schema
@strawberry.type
class Query:
    # Below are various root query fields

    @strawberry.field
    def people(self) -> list[Person]:
        # A root query field

        """
        records =[
            {"name": "Alice", "age": 22},
            {"name": "Bob", "age": 38},
            {"name": "Christine", "age": 18}
        ]

        return [
            Person(name=record["name"], age=record["age"])
            for record in records
        ]
        """
        return [
            Person(
                name="Alice", age=22,
                works_at=Company(name="Bayer", location="Germany"),
            ),
            Person(
                name="Christine", age=18,
                works_at=Company(name="NASA", location="California"),
            )
        ]


    @strawberry.field
    def labels(self) -> list[DatabaseLabel]:
        # Another root query field
        label_list = GraphSchema.db.get_labels()
        data = [DatabaseLabel(name=label)
            for label in label_list]
        return data




schema = strawberry.Schema(query=Query)




def register_graphql(app) -> None:
    """
    For Flask integration of GraphQL: adding the Strawberry integration
    adds another endpoint to the existing Flask application
    :param app:

    :return:    None
    """
    app.add_url_rule(
        "/graphql",
        view_func=GraphQLView.as_view(
            "graphql_view",
            schema=schema,
        ),
    )
