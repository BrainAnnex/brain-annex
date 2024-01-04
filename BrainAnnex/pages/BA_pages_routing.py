"""
    Router/generator for Brain Annex pages
    MIT License.  Copyright (c) 2021-2023 Julian A. West
"""

from flask import Blueprint, render_template, current_app, make_response, request   # The "request" package
                                                                                    # makes available a GLOBAL request object
from flask_login import login_required, current_user
from BrainAnnex.modules.data_manager.data_manager import DataManager
from BrainAnnex.modules.node_explorer.node_explorer import NodeExplorer
from BrainAnnex.modules.categories.categories import Categories
from datetime import datetime
import time
import json



class PagesRouting:
    """
    Setup and routing for all the Flask-based web pages served by this module
    """
    
    # Module-specific parameters (as class variables)
    blueprint_name = "BA_pages"         # Name unique to this module
    url_prefix = "/BA/pages"            # Prefix for all URL's handled by this module
    template_folder = "templates"       # Location of HTML templates (Relative to this module's location)
    static_folder = "static"            # Location of website's static content (Relative to this module's location)
    
    site_pages = None                   # Data for the site navigation



    #############################################################
    #         REGISTRATION OF THIS MODULE WITH FLASK            #
    #############################################################

    @classmethod
    def setup(cls, flask_app_obj) -> None:
        """
        Based on the module-specific class variables, and given a Flask app object,
        instantiate a "Blueprint" object,
        and register:
            the names of folders used for templates and static content
            the URL prefix to use
            the functions that will be assigned to the various URL endpoints

        :param flask_app_obj:	The Flask app object
        :return:				None
        """
        flask_blueprint = Blueprint(cls.blueprint_name, __name__,
                                    template_folder=cls.template_folder, static_folder=cls.static_folder)

        # Define the Flask routing (mapping URLs to Python functions) for all the web pages served by this module
        cls.set_routing(flask_blueprint)

        # Register with the Flask app object the Blueprint object created above, and request the desired URL prefix
        flask_app_obj.register_blueprint(flask_blueprint, url_prefix = cls.url_prefix)




    #############################################################
    #                           ROUTING                         #
    #############################################################

    @classmethod
    def set_routing(cls, bp) -> None:
        """
        Define the Flask routing (mapping URLs to Python functions)
        for all the web pages served by this module,
        and provide the functions assigned to the various URL endpoints

        :param bp:  The Flask "Blueprint" object that was created for this module
        :return:    None
        """

        ##################  START OF ROUTING DEFINITIONS  ##################

        @bp.route('/viewer')
        @bp.route('/viewer/<category_uri>')
        @login_required
        def category_page_viewer(category_uri="1") -> str:
            """
            General viewer/editor for the Content Items attached to the specified Category
            # EXAMPLES of invocation:
                http://localhost:5000/BA/pages/viewer
                http://localhost:5000/BA/pages/viewer/3
            """

            template = "page_viewer.htm"

            # Get the Name and Remarks attached to the given Category
            category_info = Categories.get_category_info(category_uri)
            # EXAMPLE : [{'id': '3', 'name': 'Hobbies', 'remarks': 'excluding sports'}]

            if not category_info:   # If page wasn't found
                # TODO: add a special page to show the error messages
                if category_uri == "1":    # The home category doesn't exist yet; maybe the Schema hasn't been imported
                    return f"<b>No Home Category found!</b> Maybe the Schema hasn't been imported yet? " \
                           f"<a href='/BA/pages/admin'>Go to the Admin page</a>"
                else:                   # Requesting a (non-home) Category that doesn't exist
                    return f"<b>No such Category ID ({category_uri}) exists!</b> Maybe that category got deleted? " \
                           f"<a href='/BA/pages/viewer/1'>Go to top (HOME) category</a>"

            # TODO: catch errors, and provide a graceful error page

            category_name = category_info.get("name", "[No name]")
            category_remarks = category_info.get("remarks", "")

            parent_categories = Categories.get_parent_categories_alt(category_uri)
            subcategories = Categories.get_subcategories_alt(category_uri)
            all_categories = Categories.get_all_categories(exclude_root=False, include_remarks=True)

            siblings_categories = Categories.viewer_handler(category_uri)

            records_types = DataManager.get_leaf_records()
            #records_schema_data = DataManager.get_records_schema_data(category_uri)  # TODO: *** TEST
            records_schema_data = Categories.get_items_schema_data(category_uri)      # TODO: *** TEST
            # EXAMPLE: {'German Vocabulary': ['Gender', 'German', 'English', 'notes'],
            #           'Site Link': ['url', 'name', 'date', 'comments', 'rating', 'read'],
            #           'Headers': ['text']}
            #print("records_schema_data: ", records_schema_data)

            bread_crumbs = Categories.create_bread_crumbs(category_uri) # A list with data from which to create UI "bread crumbs"
            #print("bread_crumbs: ", bread_crumbs)
            # EXAMPLE: ['START_CONTAINER', ['1', 'ARROW', '544'], 'END_CONTAINER']


            # Fetch all the Content Items attached to this Category
            content_items = Categories.get_content_items_by_category(category_uri)
            #   List of dictionaries.  EXAMPLE:
            #       [
            #           {'schema_code': 'h', 'uri': '1', 'text': 'Overview', pos: 10, 'class_name': 'Headers'},
            #           {'schema_code': 'n', 'uri': '1', 'basename': 'overview', 'suffix': 'htm', pos: 20, 'class_name': 'Notes'}
            #       ]


            return render_template(template, current_page=request.path, site_pages=cls.site_pages, header_title=category_name,
                                   content_items=content_items,
                                   category_id=category_uri, category_name=category_name, category_remarks=category_remarks,
                                   all_categories=all_categories,
                                   subcategories=subcategories, parent_categories=parent_categories,
                                   siblings_categories=siblings_categories,
                                   bread_crumbs=bread_crumbs,
                                   records_types=records_types, records_schema_data=records_schema_data
                                   )



        @bp.route('/filter')
        def filter_page() -> str:
            """
            # General filter page, in early stage
            # EXAMPLE invocation: http://localhost:5000/BA/pages/filter
            """
            template = "filter.htm"

            return render_template(template, current_page=request.path, site_pages=cls.site_pages)



        @bp.route('/md-file/<category_uri>')
        def md_file(category_uri) -> str:
            """
            Generate the .MD file version of the Content Items attached to the specified Category
            EXAMPLE invocation: http://localhost:5000/BA/pages/md-file/3
            """
            template = "md_file_generator.htm"

            content_items = Categories.get_content_items_by_category(category_uri=category_uri)

            return render_template(template, content_items=content_items)



        @bp.route('/static-web/<category_uri>')
        def static_web(category_uri) -> str:
            """
            Generate the static-webpage version of the Content Items attached to the specified Category
            EXAMPLE invocation: http://localhost:5000/BA/pages/static-web/3
            """

            template = "viewer_static.htm"

            # Fetch all the Content Items attached to the given Category
            content_items = Categories.get_content_items_by_category(category_uri)

            category_info = Categories.get_category_info(category_uri)
            category_name = category_info.get("name", "MISSING CATEGORY NAME. Make sure to add one!")
            category_remarks = category_info.get("remarks", "")
            subcategories = Categories.get_subcategories_alt(category_uri)
                            # EXAMPLE: [{'id': 2, 'name': 'Work'}, {'id': 3, 'name': 'Hobbies'}]

            return render_template(template,
                                   content_items=content_items,
                                   category_id=category_uri, category_name=category_name,
                                   subcategories=subcategories)



        @bp.route('/admin')
        @login_required
        def admin() -> str:
            """
            Generate a general administrative page
            (currently for import/exports, and a link to the Schema-Editor page)

            EXAMPLE invocation: http://localhost:5000/BA/pages/admin
            """
            #print(f"User is logged in as: `{current_user.username}`")
            template = "admin.htm"
            return render_template(template,
                                   username=current_user.username,
                                   current_page=request.path, site_pages=cls.site_pages)



        @bp.route('/schema-manager')
        @login_required
        def schema_manager() -> str:
            """
            Generate an administrative page to manage the Schema
            EXAMPLE invocation: http://localhost:5000/BA/pages/schema-manager
            """
            template = "schema_manager.htm"
            class_list = DataManager.all_schema_classes()
            return render_template(template, current_page=request.path, site_pages=cls.site_pages,
                                   class_list=class_list)



        @bp.route('/data-import')
        @login_required
        def data_import() -> str:
            """
            Generate an administrative page for a variety of data imports
            EXAMPLE invocation: http://localhost:5000/BA/pages/data-import
            """
            template = "data_import.htm"
            class_list = DataManager.all_schema_classes()
            intake_status = DataManager.data_intake_status()

            # Extract some config parameters (used for Continuous Data Ingestion)
            intake_folder = current_app.config['INTAKE_FOLDER']            # Defined in main file
            outtake_folder = current_app.config['OUTTAKE_FOLDER']          # Defined in main file

            return render_template(template, current_page=request.path, site_pages=cls.site_pages,
                                   class_list=class_list, intake_status=intake_status,
                                   intake_folder=intake_folder, outtake_folder=outtake_folder)




        #############################   CATEGORY-RELATED   #############################

        @bp.route('/category_manager/<category_uri>')
        @login_required
        def category_manager(category_uri :str) -> str:
            """
            Generate a page for administration of the Categories
            EXAMPLE invocation: http://localhost:5000/BA/pages/category_manager
            """

            template = "category_manager.htm"

            category_info = Categories.get_category_info(category_uri)
            category_name = category_info.get("name", "MISSING CATEGORY NAME. Make sure to add one!")
            category_remarks = category_info.get("remarks", "")

            # EXAMPLE of the various categories listings, below:
            #               [{'uri': 2, 'name': 'Work'}, {'uri': 3, 'name': 'Hobbies'}]
            subcategories = Categories.get_subcategories(category_uri)
            all_categories = Categories.get_all_categories(exclude_root=False)
            parent_categories = Categories.get_parent_categories(category_uri)
            pin_status = Categories.is_pinned(category_uri)

            return render_template(template, current_page=request.path, site_pages=cls.site_pages,
                                   category_uri=category_uri, category_name=category_name, category_remarks=category_remarks,
                                   subcategories=subcategories, parent_categories=parent_categories,
                                   all_categories=all_categories, pin_status=pin_status)




        #############################   SEARCH-RELATED   #############################

        #@bp.route('/search/<search_terms>')
        @bp.route('/search')
        @login_required
        def search() -> str:
        #def search(search_terms) -> str:
            """
            Generate a page of search results
            EXAMPLE invocation: http://localhost:5000/BA/pages/search?term=boat
            """
            template = "search.htm"

            search_terms = request.args.get("term", type = str)     # COULD ALSO ADD: , default = "someDefault"      Using Request data in Flask

            if search_terms is None:
                raise Exception("Missing value for parameter `term`")   # TODO: deal with empty searches

            content_items = DataManager.search_for_word(search_terms)

            page_header = f"{len(content_items)} SEARCH RESULT(S) for `{search_terms}`"

            return render_template(template,
                                   content_items=content_items,
                                   page_header=page_header,
                                   current_page=request.path, site_pages=cls.site_pages)





        #############################  EXPERIMENTAL PAGES   #############################

        @bp.route('/experimental')
        def experimental() -> str:
            """
            Page with links to experimental pages

            EXAMPLE invocation: http://localhost:5000/BA/pages/experimental
            :return:
            """

            template = "experimental.htm"

            return render_template(template, current_page=request.path, site_pages=cls.site_pages)



        @bp.route('/node')
        def node_explorer() -> str:
            # Node Explorer for all nodes in the database
            # EXAMPLE invocation: http://localhost:5000/BA/pages/node

            template = "node_explorer.htm"

            label_list = DataManager.get_node_labels()

            return render_template(template, current_page=request.path, site_pages=cls.site_pages,
                                   label_list = label_list)



        @bp.route('/nodes_viewer')
        def nodesviewer() -> str:
            # Node Explorer: display a (hardwired-for-now) list of nodes
            # EXAMPLE invocation: http://localhost:5000/BA/pages/nodes_viewer

            template = "nodes_viewer.htm"

            node_list = NodeExplorer.serialize_nodes(None)
            node_list_json = json.dumps(node_list)

            return render_template(template, current_page=request.path, site_pages=cls.site_pages,
                                   node_list=node_list, node_list_json=node_list_json)



        @bp.route('/manage_labels')
        @login_required
        def manage_labels() -> str:
            """
            Generate a page to manage nodes in the database; in particular,
            to display a list of all node labels, and to enter new nodes
            EXAMPLE invocation: http://localhost:5000/BA/pages/manage_labels
            """

            template = "manage_node_labels.htm"
            label_list = DataManager.get_node_labels()
            return render_template(template, label_list = label_list, current_page=request.path,
                                   site_pages=cls.site_pages)



        @bp.route('/node/<label>')
        def nodes_with_given_label(label) -> str:
            # Node Explorer for all nodes with a given label
            # EXAMPLE invocation: http://localhost:5000/BA/pages/node/BA

            template = "node_explorer.htm"

            label_list = DataManager.get_node_labels()
            return "TEMPORARILY DISABLED"
            # TODO: fix infinite loop in print statements
            (header_list, record_list, inbound_headers, outbound_headers, inbound_counts, outbound_counts) = \
                NodeExplorer.all_nodes_by_label(label)

            return render_template(template, current_page="node", site_pages=cls.site_pages,   # Maybe it should be current_page=request.path
                                   label_list = label_list,
                                   header_list = header_list, record_list = record_list,
                                   inbound_headers = inbound_headers,
                                   outbound_headers = outbound_headers,
                                   inbound_counts = inbound_counts,
                                   outbound_counts = outbound_counts
                                   )



        @bp.route('/table_tests')
        def table_tests() -> str:
            """
            Generate a page to experiment with table structures

            EXAMPLE invocation: http://localhost:5000/BA/pages/table_tests
            """
            template = "table_tests.htm"

            return render_template(template, current_page=request.path, site_pages=cls.site_pages)





        #############################   TESTS and DIAGNOSTICS  #############################

        @bp.route('/test/hello-world')
        def test_hello_world() -> str:
            # A very basic test
            # EXAMPLE invocation: http://localhost:5000/BA/pages/test/hello-world
            template = "tests/hello_world.htm"
            return render_template(template)


        @bp.route('/test/nav')
        def test_nav() -> str:
            # A test of integration into site navigation
            # EXAMPLE invocation: http://localhost:5000/BA/pages/test/nav
            template = "tests/nav.htm"
            return render_template(template, site_pages=cls.site_pages)


        @bp.route('/test/upload')
        @login_required
        def test_upload() -> str:
            """
            Test of file upload
            EXAMPLE invocation: http://localhost:5000/BA/pages/test/upload
            """
            template = "tests/upload.htm"
            return render_template(template)


        @bp.route('/test/set-cookie')
        def test_set_cookie() -> str:
            # EXAMPLE invocation: http://localhost:5000/BA/pages/test/set-cookie
            # Set a cookie, and display a test page
            print("In test_set_cookie()")
            template = "tests/hello_world.htm"
            response  = make_response(render_template(template))
            now_python = datetime.now()
            now_unix = time.mktime(now_python.timetuple())
            n_days = 1
            n_days_later_unix = now_unix + (3600 * 24 * n_days)     # Add an appropriate number of seconds to the UNIX time

            response.set_cookie(key='julianTest2', value='This cookie should expire a day later', expires=n_days_later_unix)
            return response


        @bp.route('/test/read-cookie')
        def test_read_cookie() -> str:
            # EXAMPLE invocation: http://localhost:5000/BA/pages/test/read-cookie
            cookie_name = 'julianTest2'
            cookie_value = request.cookies.get(cookie_name)
            return f"In test_read_cookie(); the cookie value was `{cookie_value}`"


        @bp.route('/test/delete-cookie')
        def test_delete_cookie() -> str:
            # EXAMPLE invocation: http://localhost:5000/BA/pages/test/delete-cookie
            # Delete a cookie, and display a test page
            print("In test_delete_cookie()")
            template = "tests/hello_world.htm"
            response  = make_response(render_template(template))
            response.set_cookie(key='julianTest2',  max_age=0)
            return response



        ######################  END OF ROUTING DEFINITIONS  ######################
