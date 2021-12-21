"""
    ----------------------------------------------------------------------------------
	MIT License

    Copyright (c) 2021 Julian A. West

    This file is part of the "Brain Annex" project (https://BrainAnnex.org)

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
	----------------------------------------------------------------------------------
"""
from BrainAnnex.modules.neo_access import neo_access
from BrainAnnex.modules.categories.categories import Categories



class PagesRequestHandler:
    """
    For general database-interaction operations.
    Used by the UI for Page Generation,
    as well as by the API to produce data for the endpoints.

    "Request Handlers" are the ONLY CLASSES THAT DIRECTLY COMMUNICATES WITH THE DATABASE INTERFACE
    """

    db = neo_access.NeoAccess()    # Saving database-interface object as a CLASS variable.
                                        # This will only be executed once


    @classmethod
    def get_content_items_by_category(cls, category_id = 1) -> [{}]:
        """
        Return the records for all nodes linked to the Category node identified by its item_id value

        :return:    A list of dictionaries
                    EXAMPLE:
                    [{'schema_code': 'i', 'item_id': 1,'width': 450, 'basename': 'my_pic', 'suffix': 'PNG', pos: 0, 'class_name': 'Images'},
                     {'schema_code': 'h', 'item_id': 1, 'text': 'Overview', pos: 10, 'class_name': 'Headers'},
                     {'schema_code': 'n', 'item_id': 1', basename': 'overview', 'suffix': 'htm', pos: 20, 'class_name': 'Notes'}
                    ]
        """

        # Locate all the Content Items linked to the given Category, and also extract the name of the schema Class they belong to
        cypher = """
            MATCH (cl :CLASS)<-[:SCHEMA]-(n :BA)-[r :BA_in_category]->(category :BA {schema_code:"cat", item_id:$category_id})
            RETURN n, r.pos AS pos, cl.name AS class_name
            ORDER BY r.pos
            """

        result = cls.db.query(cypher, {"category_id": category_id})
        #print(result)

        #content_item_list = [elem["n"] for elem in result]
        content_item_list = []
        for elem in result:
            item_record = elem["n"]             # A dictionary with the various fields

                                                            # TODO: eliminate possible conflict if the node happens to have
                                                            #       attributes named "pos" or "class_name"!
            item_record["pos"] = elem["pos"]                # Inject into the record a positional value
            item_record["class_name"] = elem["class_name"]  # Inject into the record the name of its Class
            content_item_list.append(item_record)

        print(content_item_list)
        return content_item_list



    @classmethod
    def get_node_labels(cls) -> [str]:
        """
        Look up and return a list of all the node labels in the database.
        EXAMPLE: ["my_label_1", "my_label_2"]

        :return:    A list of strings
        """

        label_list = cls.db.get_labels()        # Fetch all the node labels in the database

        return label_list




    #############################   CATEGORY-RELATED (TODO: being moved to categories.py)  #############################

    @classmethod
    def get_subcategories(cls, category_id) -> [dict]:
        """
        Return all the (immediate) subcategories of the given category,
        as a list of dictionaries with keys 'id' and 'name' TODO: fix
        EXAMPLE:
            OLD -> [{'id': 2, 'name': 'Work'}, {'id': 3, 'name': 'Hobbies'}]
            [{'item_id': 2, 'name': 'Work', remarks: 'outside employment'}, {'item_id': 3, 'name': 'Hobbies'}]

        :return:    A list of dictionaries
        """
        q =  '''
             MATCH (sub:BA {schema_code:"cat"})-[BA_subcategory_of]->(c:BA {schema_code:"cat", item_id:$category_id})
             RETURN sub.item_id AS id, sub.name AS name
             '''
        result = cls.db.query(q, {"category_id": category_id})

        '''
        new = cls.db.follow_links(labels="BA", key_name="item_id", key_value=category_id,
                                  rel_name="BA_subcategory_of", rel_dir="IN",
                                  neighbor_labels="BA")
        # OR: properties_condition = {"item_id": category_id, "schema_code": "cat"}
        '''

        return result



    @classmethod
    def get_parent_categories(cls, category_id) -> [dict]:
        """
        Return all the (immediate) parent categories of the given category,
        as a list of dictionaries with all the keys of the Category Class
        EXAMPLE:
            [{'item_id': 2, 'name': 'Work', remarks: 'outside employment'}, {'item_id': 3, 'name': 'Hobbies'}]

        :return:    A list of dictionaries
        """
        match = cls.db.find(labels="BA",
                            properties={"item_id": category_id, "schema_code": "cat"})

        result = cls.db.follow_links(match, rel_name="BA_subcategory_of", rel_dir="OUT",
                                     neighbor_labels="BA")

        return result



    @classmethod
    def get_all_categories(cls) -> [dict]:
        """
        Return all the existing Categories - except the root -
        as a list of dictionaries with keys 'id' and 'name',
        sorted by name
        EXAMPLE:
            [{'id': 3, 'name': 'Hobbies'}, {'id': 2, 'name': 'Work'}]

        :return:    A list of dictionaries
        """
        q =  '''
             MATCH (cat:BA {schema_code:"cat"})
             WHERE cat.item_id <> 1
             RETURN cat.item_id AS id, cat.name AS name
             ORDER BY toLower(cat.name)
             '''
        # Notes: 1 is the ROOT.
        # Sorting must be done across consistent capitalization, or "GSK" will appear before "German"!

        result = cls.db.query(q)

        return result


# Breadcrumb navigation as done in v. 4
"""
/*
	Create navigation BREAD CRUMBS, unless we are at the top level
 */

if ($categoryID != $SITE_ENV->categoryHandler->rootNodeID())	// If not at the root node
	echo breadCrumbs($categoryID, $categoryName);
	
	
function breadCrumbs($categoryID, $categoryName)
/*	Return an HTML element depicting all possible breadcrumb paths for the given node.  Perhaps move it to Categories module?
	A recursive call is used.
 */ 
{
	global $SITE_ENV;
		
	if ($categoryID == $SITE_ENV->categoryHandler->rootNodeID())		// If it is the root
		return  "<span class='br_nav'>TOP</span>";

	//$html = " <div style='inline-block; vertical-align:center'>&raquo; " . "$categoryName</div>\n";	// The category itself (no link because we're on that page)
	
	
	/* If we get here, we're NOT at the root.  Put together an HTML element depicting all possible breadcrumb paths from the ROOT to the current category...
	 */
	
	$html = "<div class='br_container'>\n";
	$html .= recursive($categoryID, $categoryName, true);
	$html .= "</div>\n";
	return $html;
	
} // breadCrumbs()



function recursive($categoryID, $categoryName, $terminalNode = false)
// Recursive graph traversal to generate page's bread crumbs
{
	global $SITE_ENV;
	
	//echo "categoryID:  $categoryID | categoryName: '$categoryName' | terminalNode: $terminalNode<br>";	
	if ($categoryID == $SITE_ENV->categoryHandler->rootNodeID())							// If it is the root...
		return "<span class='br_nav'><a href='" . $SITE_ENV->viewerURL . $SITE_ENV->categoryHandler->rootNodeID() ."'>TOP</a></span>\n";		// ...recursive exit
	
	$parentsArray = $SITE_ENV->categoryHandler->fetchParentCategories($categoryID);	// each element is an array that contains: [parentID, name, remarks]


	if (sizeof($parentsArray) == 0)  {
		/* 	Termination from an orphaned node!
			This might be due to a missing edge in the graph, or more simply from lacking permissions to view the parent categories */
		
		
		if ($SITE_ENV->isAdmin && ($SITE_ENV->userAccountID == $SITE_ENV->siteAccount))	// If the user is an admin visiting a page on his own account, then the problem  must be a missing edge in the graph...
			// Generate a warming, and provide a link to remedy it
		 	$SITE_ENV->userMessages->displayWarning("WARNING",
					"&ldquo;$categoryName&rdquo; <span style='color:gray'>(category ID $categoryID)</span> has no parent categories",
		 		    "<a href='siteModules/categoryManagement/categoryManager.php?c=$categoryID'>CLICK HERE TO REMEDY: Add a parent category</a>");
		else					// ... otherwise, for general users, we'll assume it's a permissions issue; assign the ROOT node as the only parent
			$parentsArray = array(
									array("parentID" =>$SITE_ENV->categoryHandler->rootNodeID(), "name" => "TOP", "remarks" => "")
								  );		// Assign the Top Level as the only parent
	}


	if ($terminalNode)
		$currentCategory = "<span class='br_nav'> &raquo; $categoryName</span>\n";
	else
		$currentCategory = "<span class='br_nav'> &raquo; <a href='" . $SITE_ENV->viewerURL . "$categoryID'>$categoryName</a></span>\n";

	
	if (sizeof($parentsArray) == 1)  {		// If just one parent

		$parent = $parentsArray[0];			// Single parent
		$parentID = $parent["parentID"];
		$parentName = $parent["name"];
		
		$html = recursive($parentID, $parentName);
		
		return $html . $currentCategory;
	}
	else  {									// If multiple parents
		$html = "<div class='br_block'>\n";
		
		foreach ($parentsArray as $i => $parent)  {
			$parentID = $parent["parentID"];
			$parentName = $parent["name"];
							
			$html .= "<div class='br_line'>\n";
			
			$html .= recursive($parentID, $parentName);
			
			$html .= "</div>\n";	// end div 'br_line'
			
			if ($i != sizeof($parentsArray) - 1)				// Skip if we're dealing with last element
				$html .= "<div style='clear:right'></div>";	
		}
		
		$html .= "</div>\n";	// end div 'br_block'
		
		return $html . $currentCategory;
	}

} // recursive()
"""