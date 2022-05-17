"""
    Router/generator for Brain Annex pages
    MIT License.  Copyright (c) 2021-2022 Julian A. West
"""

from flask import Blueprint, render_template, request   # The request package makes available a GLOBAL request object
from flask_login import login_required, current_user
from BrainAnnex.pages.BA_pages_request_handler import PagesRequestHandler
from BrainAnnex.api.BA_api_request_handler import APIRequestHandler     # TODO: reorganize, to avoid this
from BrainAnnex.modules.node_explorer.node_explorer import NodeExplorer
from BrainAnnex.modules.categories.categories import Categories
import json



class PagesRouting:
    """
    Setup, routing and endpoints for all the web pages served by this module
    """
    
    # Module-specific parameters (as class variables)
    blueprint_name = "BA_pages"         # Name unique to this module
    url_prefix = "/BA/pages"            # Prefix for all URL's handled by this module
    template_folder = "templates"       # Relative to this module's location
    static_folder = "static"            # Relative to this module's location
    
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
        @bp.route('/viewer/<category_id>')
        def category_page_viewer(category_id=1) -> str:
            """
            General viewer/editor for the Content Items attached to the specified Category
            # EXAMPLES of invocation:
                http://localhost:5000/BA/pages/viewer
                http://localhost:5000/BA/pages/viewer/3
            """

            template = "page_viewer.htm"
            category_id = int(category_id)  # TODO: return a good error message (a special page) if it's not an integer

            # Fetch all the Content Items attached to the given Category.
            content_items = PagesRequestHandler.get_content_items_by_category(category_id)
            #   List of dictionaries.  EXAMPLE:
            #       [
            #           {'schema_code': 'h', 'item_id': 1, 'text': 'Overview', pos: 10, 'class_name': 'Headers'},
            #           {'schema_code': 'n', 'item_id': 1', basename': 'overview', 'suffix': 'htm', pos: 20, 'class_name': 'Notes'}
            #       ]

            # Get the Name and Remarks attached to the given Category
            category_info = Categories.get_category_info(category_id)
            # EXAMPLE : [{'id': 3, 'name': 'Hobbies', 'remarks': 'excluding sports'}]

            if not category_info:
                # TODO: add a special page to show that
                return f"<b>No such Category ID ({category_id}) exists!</b> Maybe that category got deleted? <a href='/BA/pages/viewer/1'>Go to top (HOME) category</a>"

            category_name = category_info.get("name", "[No name]")
            category_remarks = category_info.get("remarks", "")

            parent_categories = PagesRequestHandler.get_parent_categories(category_id)
            subcategories = PagesRequestHandler.get_subcategories(category_id)
            all_categories = PagesRequestHandler.get_all_categories(exclude_root=False) # TODO: switch to Categories.get_all_categories()

            records_types = APIRequestHandler.get_leaf_records()
            records_schema_data = APIRequestHandler.get_records_schema_data(category_id)  # TODO: *** TEST
            #print("records_schema_data: ", records_schema_data)

            bread_crumbs = Categories.create_bread_crumbs(category_id)

            return render_template(template, current_page=request.path, site_pages=cls.site_pages, header_title=category_name,
                                   content_items=content_items,
                                   category_id=category_id, category_name=category_name, category_remarks=category_remarks,
                                   all_categories=all_categories,
                                   subcategories=subcategories, parent_categories=parent_categories,
                                   bread_crumbs=bread_crumbs,
                                   records_types=records_types, records_schema_data=records_schema_data
                                   )



        @bp.route('/filter')
        def filter_page() -> str:
            # General filter page, in early stage
            # EXAMPLE invocation: http://localhost:5000/BA/pages/filter

            template = "filter.htm"

            return render_template(template, current_page=request.path, site_pages=cls.site_pages)



        @bp.route('/md-file/<category_id>')
        def md_file(category_id) -> str:
            """
            Generate the .MD file version of the Content Items attached to the specified Category
            EXAMPLE invocation: http://localhost:5000/BA/pages/md-file/3
            """
            template = "md_file_generator.htm"

            content_items = PagesRequestHandler.get_content_items_by_category(category_id=int(category_id))

            return render_template(template, content_items=content_items)



        @bp.route('/static-web/<category_id>')
        def static_web(category_id) -> str:
            """
            Generate the static-webpage version of the Content Items attached to the specified Category
            EXAMPLE invocation: http://localhost:5000/BA/pages/static-web/3
            """

            template = "viewer_static.htm"

            category_id = int(category_id)

            # Fetch all the Content Items attached to the given Category
            content_items = PagesRequestHandler.get_content_items_by_category(category_id)

            category_info = Categories.get_category_info(category_id)
            category_name = category_info.get("name", "MISSING CATEGORY NAME. Make sure to add one!")
            category_remarks = category_info.get("remarks", "")
            subcategories = PagesRequestHandler.get_subcategories(category_id)
                            # EXAMPLE: [{'id': 2, 'name': 'Work'}, {'id': 3, 'name': 'Hobbies'}]

            return render_template(template,
                                   content_items=content_items,
                                   category_id=category_id, category_name=category_name,
                                   subcategories=subcategories)



        @bp.route('/admin')
        @login_required
        def admin() -> str:
            """
            Generate a general administrative page
            (currently for import/exports, and a link to the Schema-Editor page)

            EXAMPLE invocation: http://localhost:5000/BA/pages/admin
            """
            print(f"User is logged in as: `{current_user.username}`")
            template = "admin.htm"
            return render_template(template,
                                   username=current_user.username,
                                   current_page=request.path, site_pages=cls.site_pages)



        @bp.route('/schema-manager')
        def schema_manager() -> str:
            """
            Generate an administrative page to manage the Schema
            EXAMPLE invocation: http://localhost:5000/BA/pages/schema-manager
            """
            template = "schema_manager.htm"
            class_list = PagesRequestHandler.all_schema_classes()
            return render_template(template, current_page=request.path, site_pages=cls.site_pages,
                                   class_list=class_list)



        @bp.route('/data-import')
        def data_import() -> str:
            """
            Generate a general administrative page (currently for import/exports)
            EXAMPLE invocation: http://localhost:5000/BA/pages/data-import
            """
            template = "data_import.htm"
            class_list = PagesRequestHandler.all_schema_classes()
            return render_template(template, current_page=request.path, site_pages=cls.site_pages,
                                   class_list=class_list)




        #############################   CATEGORY-RELATED   #############################

        @bp.route('/category_manager/<category_id>')
        def category_manager(category_id) -> str:
            """
            Generate a page for administration of the Categories
            EXAMPLE invocation: http://localhost:5000/BA/pages/category_manager
            """

            template = "category_manager.htm"
            category_id = int(category_id)

            category_info = Categories.get_category_info(category_id)
            category_name = category_info.get("name", "MISSING CATEGORY NAME. Make sure to add one!")
            category_remarks = category_info.get("remarks", "")

            # EXAMPLE of the various categories listings, below: [{'item_id': 2, 'name': 'Work'}, {'item_id': 3, 'name': 'Hobbies'}]
            subcategories = Categories.get_subcategories(category_id)
            all_categories = Categories.get_all_categories(exclude_root=False)
            parent_categories = Categories.get_parent_categories(category_id)

            return render_template(template, current_page=request.path, site_pages=cls.site_pages,
                                   category_id=category_id, category_name=category_name, category_remarks=category_remarks,
                                   subcategories=subcategories, parent_categories=parent_categories,
                                   all_categories=all_categories)




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

            label_list = PagesRequestHandler.get_node_labels()

            return render_template(template, current_page=request.path, site_pages=cls.site_pages,
                                   label_list = label_list)



        @bp.route('/nodes_viewer')
        def nodesviewer() -> str:
            # Node Explorer: display a (hardwired-for-now) list of nodes
            # EXAMPLE invocation: http://localhost:5000/BA/pages/nodes_viewer

            template = "nodes_viewer.htm"

            ne_obj = NodeExplorer()
            node_list = ne_obj.serialize_nodes(None)
            node_list_json = json.dumps(node_list)

            return render_template(template, current_page=request.path, site_pages=cls.site_pages,
                                   node_list=node_list, node_list_json=node_list_json)



        @bp.route('/manage_labels')
        def manage_labels() -> str:
            """
            Generate a page to manage nodes in the database; in particular,
            to display a list of all node labels, and to enter new nodes
            EXAMPLE invocation: http://localhost:5000/BA/pages/manage_labels
            """

            template = "manage_node_labels.htm"
            label_list = PagesRequestHandler.get_node_labels()
            return render_template(template, label_list = label_list, current_page=request.path,
                                   site_pages=cls.site_pages)



        @bp.route('/node/<label>')
        def nodes_with_given_label(label) -> str:
            # Node Explorer for all nodes with a given label
            # EXAMPLE invocation: http://localhost:5000/BA/pages/node/BA

            template = "node_explorer.htm"

            label_list = PagesRequestHandler.get_node_labels()

            ne_obj = NodeExplorer()
            (header_list, record_list, inbound_headers, outbound_headers, inbound_counts, outbound_counts) = ne_obj.all_nodes_by_label(label)

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





        #############################   TESTS   #############################

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
        def test_upload() -> str:
            """
            Test of file upload
            EXAMPLE invocation: http://localhost:5000/BA/pages/test/upload
            """
            template = "tests/upload.htm"
            return render_template(template)


        ##################  END OF ROUTING DEFINITIONS  ##################
