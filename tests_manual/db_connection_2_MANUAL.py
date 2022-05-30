# Test of ability to connect to the Neo4j database from the credentials
# in the environment variables NEO4J_HOST, NEO4J_USER, NEO4J_PASSWORD

import os
from BrainAnnex.modules.neo_access.neo_access import NeoAccess

print("About to test the database connection, using the credentials STORED in the environment variables NEO4J_HOST, NEO4J_USER, NEO4J_PASSWORD...\n")


# Attempt to connect to the Neo4j database from credentials in environment variables
obj = NeoAccess(debug=True, autoconnect=True)


print("Version of the Neo4j driver: ", obj.version())

print(f"Value of environment variable NEO4J_USER: `{os.environ.get('NEO4J_USER')}`")

print("End of test")