# Test of the ability to connect to the Neo4j database upon having the user type in the credentials

import os
from neoaccess import NeoAccess

print("About to test the database connection...  Enter the host IP, but leave out the port number: (EXAMPLES:  bolt://1.2.3.4  OR  neo4j://localhost )\n")
host = input()
host += ":7687"
print("Enter the password:")    # TODO: change to getpass.getpass()
password = input()

print(f"Attempting to connect as host='{host}', username='neo4j', with the password just entered...")


# Attempt to connect to the Neo4j database from the passed credentials
obj = NeoAccess(host=host,
                credentials=("neo4j", password),
                debug=True, autoconnect=True)


print("Version of the Neo4j driver: ", obj.version())

print("END of test")

