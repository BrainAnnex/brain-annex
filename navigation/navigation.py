"""
Definition of the Navigation Bar entries for the overall site navigation
(both Brain Annex and, possibly, co-hosted sites)
"""


def get_site_pages() -> dict:
    """
    All entries for the Navigation Bar should be declared inside this function.

    :return: A dictionary of entries for the Navigation Bar
    """

    # Listing of pages to show in the top navbar
    site_pages = {      # Format of dictionary entries is
                        #       URL : text to show in the navbar
        
        "/BA/pages/viewer" : "Category Viewer",      
        "/BA/pages/filter" : "Search",
        "/BA/pages/experimental" : "Experimental",
        "/BA/pages/admin" : "Admin",
        "/sample/pages/sample-page" : "Other site"      # Example page from a co-hosted site
    }

    return site_pages
