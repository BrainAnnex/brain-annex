# Test of ability to connect to the Neo4j database upon having the user type in the credentials

import os
from BrainAnnex.modules.neo_access.neo_access import NeoAccess

print("About to test the database connection...  Enter the host IP: (EXAMPLES:  bolt://1.2.3.4  OR  neo4j://localhost )\n")
host = input()
host += ":7687"
print("Enter the password:")
password = input()

print(f"Attempting to connect as host='{host}', username='neo4j', password=`{password}`")


# Attempt to connect to the Neo4j database from the passed credentials
obj = NeoAccess(host=host,
                credentials=("neo4j", password),
                debug=True, autoconnect=True)


print("Version of the Neo4j driver: ", obj.version())

print(f"Value of environment variable NEO4J_USER: `{os.environ.get('NEO4J_USER')}`")

print("End of test")

