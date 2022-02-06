"""
    Router/generator for Brain Annex pages

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

from flask import Blueprint, render_template, request   # The request package makes available a GLOBAL request object
from BrainAnnex.pages.BA_pages_request_handler import PagesRequestHandler
from BrainAnnex.api.BA_api_request_handler import APIRequestHandler     # TODO: reorganize, to avoid this
from BrainAnnex.modules.node_explorer.node_explorer import NodeExplorer
from BrainAnnex.modules.categories.categories import Categories
import json



class PagesRouting:

    def __init__(self, site_pages):
        """
        
        :param site_pages: Data for the site navigation
        """
        # Specify where this module's TEMPLATE and STATIC folders are located (relative to this module's main folder)
        self.BA_pages_flask_blueprint = Blueprint('BA_pages', __name__,
                                                  template_folder='templates', static_folder='static')
        # This "Blueprint" object will get registered in the Flask app object in main.py, using: url_prefix = "/BA/pages"

        self.site_pages = site_pages    # Data for the site navigation
        
        self.set_routing()              # Define the Flask routing (mapping URLs to Python functions)



    ###############################################
    #               For ROUTING                   #
    ###############################################

    def set_routing(self) -> None:
        """
        Define the Flask routing (mapping URLs to Python functions)
        for all the web pages served by this module

        :return: None
        """

        #"@" signifies a decorator - a way to wrap a function and modify its behavior
        @self.BA_pages_flask_blueprint.route('/login')
        def login() -> str:
            # EXAMPLE invocation: http://localhost:5000/BA/pages/login
            url = "login.htm"
            """
            # DEBUGGING, TO DELETE
            not_yet_used = current_app.config['UPLOAD_FOLDER']
            print(not_yet_used)
            not_yet_used2 = current_app.config['APP_NEO4J_DBASE']
            print(not_yet_used2.credentials)
            """
            return render_template(url)




        @self.BA_pages_flask_blueprint.route('/nodes_viewer')
        def nodes_viewer() -> str:
            # Node Explorer: display a (hardwired-for-now) list of nodes
            # EXAMPLE invocation: http://localhost:5000/BA/pages/nodes_viewer

            url = "nodes_viewer.htm"

            ne_obj = NodeExplorer()
            node_list = ne_obj.serialize_nodes(None)
            node_list_json = json.dumps(node_list)

            return render_template(url, current_page="nodes_viewer", site_pages=self.site_pages,
                                   node_list=node_list, node_list_json=node_list_json)

        @self.BA_pages_flask_blueprint.route('/nodes_viewer')
        def nodesviewer_duplicate() -> str:
            # Node Explorer: display a (hardwired-for-now) list of nodes
            # EXAMPLE invocation: http://localhost:5000/BA/pages/nodes_viewer

            url = "nodes_viewer.htm"

            ne_obj = NodeExplorer()
            node_list = ne_obj.serialize_nodes(None)
            node_list_json = json.dumps(node_list)

            return render_template(url, current_page=request.path, site_pages=self.site_pages,
                                   node_list=node_list, node_list_json=node_list_json)



        @self.BA_pages_flask_blueprint.route('/node')
        def node_explorer() -> str:
            # Node Explorer for all nodes in the database
            # EXAMPLE invocation: http://localhost:5000/BA/pages/node

            url = "node_explorer.htm"

            label_list = PagesRequestHandler.get_node_labels()

            return render_template(url, current_page=request.path, site_pages=self.site_pages,
                                   label_list = label_list)


        @self.BA_pages_flask_blueprint.route('/node/<label>')
        def nodes_with_given_label(label) -> str:
            # Node Explorer for all nodes with a given label
            # EXAMPLE invocation: http://localhost:5000/BA/pages/node/BA

            url = "node_explorer.htm"

            label_list = PagesRequestHandler.get_node_labels()

            ne_obj = NodeExplorer()
            (header_list, record_list, inbound_headers, outbound_headers, inbound_counts, outbound_counts) = ne_obj.all_nodes_by_label(label)

            return render_template(url, current_page="node", site_pages=self.site_pages,   # Maybe it should be current_page="/BA/pages/node"
                                   label_list = label_list,
                                   header_list = header_list, record_list = record_list,
                                   inbound_headers = inbound_headers,
                                   outbound_headers = outbound_headers,
                                   inbound_counts = inbound_counts,
                                   outbound_counts = outbound_counts
                                   )



        @self.BA_pages_flask_blueprint.route('/viewer')
        @self.BA_pages_flask_blueprint.route('/viewer/<category_id>')
        def category_page_viewer(category_id=1) -> str:
            """
            General viewer/editor for the Content Items attached to the specified Category
            # EXAMPLES of invocation:
                http://localhost:5000/BA/pages/viewer
                http://localhost:5000/BA/pages/viewer/3
            """

            template = "page_viewer.htm"
            category_id = int(category_id)  # TODO: return good error message if it's not an integer

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
            all_categories = PagesRequestHandler.get_all_categories(exclude_root=False)

            records_classes = APIRequestHandler.get_leaf_records()

            bread_crumbs = Categories.create_bread_crumbs(category_id)

            return render_template(template, current_page=request.path, site_pages=self.site_pages, header_title=category_name,
                                   content_items=content_items,
                                   category_id=category_id, category_name=category_name, category_remarks=category_remarks,
                                   all_categories=all_categories,
                                   subcategories=subcategories, parent_categories=parent_categories,
                                   bread_crumbs=bread_crumbs,
                                   records_classes=records_classes
                                   )



        @self.BA_pages_flask_blueprint.route('/filter')
        def filter_page() -> str:
            # Experimental filter
            # EXAMPLE invocation: http://localhost:5000/BA/pages/filter

            template = "filter.htm"

            return render_template(template, current_page=request.path, site_pages=self.site_pages)



        @self.BA_pages_flask_blueprint.route('/md-file/<category_id>')
        def md_file(category_id) -> str:
            """
            Generate the .MD file version of the Content Items attached to the specified Category
            # EXAMPLE invocation: http://localhost:5000/BA/pages/md-file/3
            """
            template = "md_file_generator.htm"

            content_items = PagesRequestHandler.get_content_items_by_category(category_id=int(category_id))

            return render_template(template, content_items=content_items)



        @self.BA_pages_flask_blueprint.route('/static-web/<category_id>')
        def static_web(category_id) -> str:
            """
            Generate the static-webpage version of the Content Items attached to the specified Category
            # EXAMPLE invocation: http://localhost:5000/BA/pages/static-web/3
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



        @self.BA_pages_flask_blueprint.route('/admin')
        def admin() -> str:
            # A general administrative page (currently for import/exports)
            # EXAMPLE invocation: http://localhost:5000/BA/pages/admin

            url = "admin.htm"
            return render_template(url, current_page=request.path, site_pages=self.site_pages)



        @self.BA_pages_flask_blueprint.route('/manage_labels')
        def manage_labels() -> str:
            """
            Generate a page to manage nodes in the database; in particular,
            to display a list of all node labels, and to enter new nodes
            EXAMPLE invocation: http://localhost:5000/BA/pages/manage_labels
            """

            url = "manage_node_labels.htm"
            label_list = PagesRequestHandler.get_node_labels()
            return render_template(url, label_list = label_list, current_page=request.path,
                                    site_pages=self.site_pages)




        #############################   CATEGORY-RELATED   #############################

        @self.BA_pages_flask_blueprint.route('/category_manager/<category_id>')
        def category_manager(category_id) -> str:
            """

            EXAMPLE invocation: http://localhost:5000/BA/pages/category_manager
            """

            template = "category_manager.htm"
            category_id = int(category_id)

            category_info = Categories.get_category_info(category_id)
            category_name = category_info.get("name", "MISSING CATEGORY NAME. Make sure to add one!")
            category_remarks = category_info.get("remarks", "")

            # EXAMPLE of the various categories listings, below: [{'item_id': 2, 'name': 'Work'}, {'item_id': 3, 'name': 'Hobbies'}]
            subcategories = Categories.get_subcategories(category_id)
            all_categories = Categories.get_all_categories()
            parent_categories = Categories.get_parent_categories(category_id)

            return render_template(template, current_page=request.path, site_pages=self.site_pages,
                                   category_id=category_id, category_name=category_name, category_remarks=category_remarks,
                                   subcategories=subcategories, parent_categories=parent_categories,
                                   all_categories=all_categories)




        #############################   TESTS   #############################

        @self.BA_pages_flask_blueprint.route('/test/hello-world')
        def test_hello_world() -> str:
            # A very basic test
            # EXAMPLE invocation: http://localhost:5000/BA/pages/test/hello-world
            url = "tests/hello_world.htm"
            return render_template(url)


        @self.BA_pages_flask_blueprint.route('/test/nav')
        def test_nav() -> str:
            # A test of integration into site navigation
            # EXAMPLE invocation: http://localhost:5000/BA/pages/test/nav
            url = "tests/nav.htm"
            return render_template(url, site_pages=self.site_pages)


        @self.BA_pages_flask_blueprint.route('/test/upload')
        def test_upload() -> str:
            """
            Test of file upload
            EXAMPLE invocation: http://localhost:5000/BA/pages/test/upload
            """
            url = "tests/upload.htm"
            return render_template(url)
