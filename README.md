# Brain Annex

**Version 5** of is a *complete overhaul* of Brain Annex's internal structure.  
This major new release is in a *late Beta* stage, approaching "release candidate".

However, the bottom layer (the `NeoAccess` library) is NOT in Beta: it's stable,
and is released independently.

The version number can be found in `VERSION_NUMBER.txt`

### Website: https://BrainAnnex.org

**[Change Log](https://brainannex.org/viewer.php?ac=2&cat=14)**



# Brain Annex's Technology Stack (Overview)

NOTE: the bottom layer, or layers, of the stack may be used independently of the
layers above them, if desired.

_From lower to higher levels:_

* **Neo4j graph database** (v. 4.4)

* **NeoAccess library** (python interface offering many services)

* **NeoSchema library** (optional Schema layer)

* **Python/Flask** (for API and webapp pages)

* **Vue2.js**




### EXAMPLE of use case : Multimedia Knowledge Representation and Management
[Motivation and overview](https://julianspolymathexplorations.blogspot.com/2019/03/multimedia-knowledge-representation-and-management-brain-annex.html)



## What are Neo4j/Graph Databases, and why do they matter?
If you're new, here's a 
[gentle brief intro](https://julianspolymathexplorations.blogspot.com/2021/02/neo4j-graph-databases-intro.html). 


# Brain Annex's Technology Stack (Details)

Brain Annex may be used as a standalone web app, or used to power *other* web apps.  
The libraries that are the bottom layers may also be used independently.

![Brain Annex Technology Stack](BrainAnnex/docs/BrainAnnex_Technology_Stack.png)


# How to set up and use Brain Annex

Brain Annex, if used in its entirety, supports both local and remote setup of the web app and of the Neo4j database.

The database and web app may reside on the same or different machines.

## SETUP

[INSTRUCTIONS](https://brainannex.org/setup)




## EXAMPLES of Schemas available for import

(For instructions on how to import the Schemas, see the setup page, above)

#### EXAMPLE 1 - the available default Multimedia Content Management System

The ROOT node for the Categories is shown in blue at the top.

![Minimal_Schema_plus_ROOT_category.png](BrainAnnex/docs/Minimal_Schema_plus_ROOT_category.png)

---

#### EXAMPLE 2 - same as example 1, but with sample extra Classes (representative of user-added schema)

The diagram below is split in 2 parts, for readability.

"chem" is an example of a custom Class.

![Classes and Properties in Brain Annex - Non-record types](BrainAnnex/docs/Classes_and_Properties_Non_record_types.png)

The following second half of the diagram shows the remainder of the Schema, detailing Classes that are instances of the "Records" Class.
Most of the items in this diagram are examples of typical user-added schema:

![Classes and Properties in Brain Annex - Record types](BrainAnnex/docs/Classes_and_Properties_Record_types.png)



**Optional: add Neo4j Indexes and Constraints**

Not strictly needed for test runs, but at some point Neo4j Indexes and Constraints 
need to be added, for speed and reliability.
From the Neo4j browser interface, issue the following Cypher commands:

    CREATE CONSTRAINT unique_BA_ID ON (n:BA) ASSERT n.item_id IS UNIQUE
    CREATE CONSTRAINT unique_CLASS_ID ON (n:CLASS) ASSERT n.schema_id IS UNIQUE
    CREATE CONSTRAINT unique_CLASS_NAME ON (n:CLASS) ASSERT n.name IS UNIQUE
    CREATE CONSTRAINT unique_PROPERTY_ID ON (n:PROPERTY) ASSERT n.schema_id IS UNIQUE


# Major components
* **NeoAccess** : a library to connect to Neo4j with python. It provides many services.
  [Link](https://github.com/BrainAnnex/neoaccess)


* **NeoSchema** : a higher-level schema-based library on top of NeoAccess.
  [Link](https://github.com/BrainAnnex/brain-annex/blob/main/BrainAnnex/modules/neo_schema/neo_schema.py)  
  [Article explaining this layer](https://julianspolymathexplorations.blogspot.com/2022/11/schema-graph-databases-neo4j.html)
  

* **CK Editor** : open-source JavaScript library to implement an online HTML Editor.  
  [Website](https://www.quackit.com/html/online-html-editor/full/).
  (Note: Brain Annex uses [version 4](https://ckeditor.com/docs/ckeditor4/latest/) of the CK Editor)
  

* **API** : the endpoints appear in [this file](https://github.com/BrainAnnex/brain-annex/blob/main/BrainAnnex/api/BA_api_routing.py)


* **Web pages** : the pages generated by Brain Annex are listed in [this routing file](https://github.com/BrainAnnex/brain-annex/blob/main/BrainAnnex/pages/BA_pages_routing.py)


* **Navigation bar** : Brain Annex can be used either as a standalone web app, or integrated with another site.  
  The navigation is implemented [in this package](https://github.com/BrainAnnex/brain-annex/tree/main/navigation)


### Project website: [https://BrainAnnex.org](https://BrainAnnex.org)

### The lead author of Brain Annex can be reached on [LinkedIn](https://www.linkedin.com/in/julian-%F0%9F%A7%AC-west-059997185/)