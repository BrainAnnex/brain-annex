# Brain Annex

**Version 5** of is a *complete overhaul* of Brain Annex's internal structure.  
This major new release is in a *late Beta* stage, approaching "release candidate".  
The version number can be found in `VERSION_NUMBER.txt`

# The New Technology Stack (Overview)

* **Neo4j graph database** (v. 4.3)


* **Python/Flask**


* **Vue2.js**


**[Change Log](https://brainannex.org/viewer.php?ac=2&cat=14)**

## Background - Multimedia Knowledge Representation and Management
[What is Brain Annex?](https://julianspolymathexplorations.blogspot.com/2019/03/multimedia-knowledge-representation-and-management-brain-annex.html)
### Project website: https://BrainAnnex.org



## What are Neo4j/Graph Databases, and why do they matter?
If you're new, here's a 
[gentle brief intro](https://julianspolymathexplorations.blogspot.com/2021/02/neo4j-graph-databases-intro.html). 


# Brain Annex's Technology Stack

Brain Annex may be used as a standalone web app, or used to power *other* web apps.

![Brain Annex Technology Stack](BrainAnnex/docs/BrainAnnex_Technology_Stack.png)

# How to set up and use Brain Annex

Brain Annex supports both local and remote setup of the web app and the Neo4j database.

The database and web app may reside on the same or different machines.

## PART 1 - Neo4j

**Set up and start the Database (and Install Java, as needed)**

[INSTRUCTIONS](https://brainannex.org/setup)




## After completing the above instructions:







![Log into Brain Annex](BrainAnnex/docs/BrainAnnex_login.png)



**Import the Schema**

Go to the "Admin" page of the Brain Annex UI (the layout of this page may be different):

![Brain Annex Admin page](BrainAnnex/docs/JSON_import.png)

Brain Annex is schema-based, and **it's critical that you import the standard schema.**
Use the **"IMPORT from JSON"** box on that "Admin" page.

For testing, we recommend importing the file `/BrainAnnex/init/Schema_EXAMPLE_plus_root_category.json`, which
includes various examples of user-added schema.

If you don't want the examples, there's the file `/BrainAnnex/Schema_MINIMAL_plus_root_category.json`, which
contains everything that is regarded as *fundamental* in a typical Brain Annex installation.

In addition to the Schema, both files contain the ROOT node for the Categories (which is regarded as a data point,
not part of the Schema.)

At the end of the import operation,
you should see a message about having imported a certain number of nodes and relationships.

Note - the imported schema may be seen by going to the Neo4j browser interface,
and issuing the Cypher command:

    MATCH (c1:CLASS)--(c2:CLASS)-[:HAS_PROPERTY]-(p:PROPERTY), (n:BA)
    RETURN c1, c2, p, n

The following diagram shows about 1/2 of the Schema.  "chem" is an example of a custom Class; the remaining
Classes are for a typical Brain Annex installation:
![Classes and Properties in Brain Annex - Non-record types](BrainAnnex/docs/Classes_and_Properties_Non_record_types.png)

The following diagram shows the remainder of the Schema, detailing Classes that are instances of the "Records" Class.
Most of the items in this diagrams are examples of typical user-added schema, only present if you imported
the larger schema file with the examples:
![Classes and Properties in Brain Annex - Record types](BrainAnnex/docs/Classes_and_Properties_Record_types.png)

Below is the **minimal** version of the JSON file imports - it's the combination of the previous 2 diagrams, minus 
any sample user customization.  Also shown here is the ROOT node for the Categories, in blue at the top.

![Minimal_Schema_plus_ROOT_category.png](BrainAnnex/docs/Minimal_Schema_plus_ROOT_category.png)

**Optional: add Neo4j Indexes and Constraints**

Not strictly needed for test runs, but at some point Neo4j Indexes and Constraints 
need to be added, for speed and reliability.
From the Neo4j browser interface, issue the following Cypher commands:

    CREATE CONSTRAINT unique_BA_ID ON (n:BA) ASSERT n.item_id IS UNIQUE
    CREATE CONSTRAINT unique_CLASS_ID ON (n:CLASS) ASSERT n.schema_id IS UNIQUE
    CREATE CONSTRAINT unique_CLASS_NAME ON (n:CLASS) ASSERT n.name IS UNIQUE
    CREATE CONSTRAINT unique_PROPERTY_ID ON (n:PROPERTY) ASSERT n.schema_id IS UNIQUE


# Major components
* **NeoAccess** : a library to connect to Neo4j.
  The APOC library must be installed on Neo4j to use the function export_dbase_json().  
  [Link](https://github.com/BrainAnnex/brain-annex/blob/main/BrainAnnex/modules/neo_access/neo_access.py)


* **NeoSchema** : a higher-level schema-based library on top of NeoAccess.
  [Link](https://github.com/BrainAnnex/brain-annex/blob/main/BrainAnnex/modules/neo_schema/neo_schema.py)
  

* **CK Editor** : open-source JavaScript library to implement an online HTML Editor.  
  [Website](https://www.quackit.com/html/online-html-editor/full/).
  (Note: Brain Annex uses [version 4](https://ckeditor.com/docs/ckeditor4/latest/) of the CK Editor)
  

* **API** : the endpoints appear in [this file](https://github.com/BrainAnnex/brain-annex/blob/main/BrainAnnex/api/BA_api_routing.py)


* **Web pages** : the pages generated by Brain Annex are listed in [this routing file](https://github.com/BrainAnnex/brain-annex/blob/main/BrainAnnex/pages/BA_pages_routing.py)


* **Navigation bar** : Brain Annex can be used either as a standalone web app, or integrated with another site.  
  The navigation is implemented [in this package](https://github.com/BrainAnnex/brain-annex/tree/main/navigation)


### Project website: [https://BrainAnnex.org](https://BrainAnnex.org)

### The lead author of Brain Annex can be reached on [LinkedIn](https://www.linkedin.com/in/julian-%F0%9F%A7%AC-west-059997185/)