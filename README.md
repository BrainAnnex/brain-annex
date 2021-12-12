# Brain Annex, version 5

**Version 5** of Brain Annex is a complete overhaul of its internal structure:

* **Neo4j graph database** (v. 4.3) replaces MySQL and the old built-in triplestore database


* **Python/Flask** replace the old PHP/pForce framework


* **Vue2.js** has expanded to take on a full role, replacing the old vanilla-JavaScript parts

This major new release is currently in a **late Beta stage**.  Released to open source on Dec. 12, 2021

All testing done with *Neo4j version 4.3.4*

**TO CONNECT TO THE NEO4J DATABASE**, must set the following Environmental Variables:

    NEO4J_HOST
    NEO4J_USER
    NEO4J_PASSWORD

**OTHER INITIAL CONFIGURATION:**

    * The Python variable MEDIA_FOLDER must be set to the desired location for your media
    (for the time being, it must be in a Flask static-pages folder)
    
    * The Brain Annex schema must be imported
    (use the "Admin tab" after running main.py) 

Project website: https://BrainAnnex.org

## Major components
* **NeoAccess** : a library to connect to Neo4j
                  The APOC library must be installed to use the function export_dbase_json()


* **NeoSchema** : a higher-level schema-based library on top of NeoAccess