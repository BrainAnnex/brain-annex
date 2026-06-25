# Test of ability to connect to the Neo4j database from the credentials
# in the environment variables NEO4J_HOST, NEO4J_USER, NEO4J_PASSWORD .  TODO: change those names for consistency with other modules

import os
from brainannex import GraphAccess

print("About to test the database connection, using the credentials STORED in the environment variables NEO4J_HOST, NEO4J_USER, NEO4J_PASSWORD...\n")

print(f"Value of environment variable NEO4J_HOST: `{os.getenv('NEO4J_HOST')}`")
print(f"Value of environment variable NEO4J_USER: `{os.environ.get('NEO4J_USER')}`")


if not os.environ.get('NEO4J_HOST') \
    or not os.environ.get('NEO4J_USER') \
       or not os.environ.get('NEO4J_HOST'):
    print("To run this test, ALL of the following env variables must FIRST be set: NEO4J_HOST, NEO4J_USER, NEO4J_PASSWORD.  "
          "Test skipped")

else:
    # Attempt to connect to the Neo4j database from credentials in environment variables
    db = GraphAccess(debug=True, autoconnect=True)

    print("\nVersion of the Neo4j driver: ", db.driver_version())
    print("Version of the Neo4j server: ", db.server_version())

    db.test_dbase_connection()

    print("End of test")
