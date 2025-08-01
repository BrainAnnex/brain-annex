import re                               # For REGEX
import pandas as pd



"""
    MIT License.  Copyright (c) 2021-2025 Julian A. West and the BrainAnnex.org project
"""



class DocumentationGenerator:
    """
    To generate the HTML for a documentation page, from a python file
    (for best results, it's expected to be a file following some styling conventions
    as done in the source code for the  BrainAnnex project)
    """


    @classmethod
    def import_python_file(cls, basename, full_filename) -> str:
        """
        Parse a python source file (expected to conform to a few conventions)
        and generate HTML that can be used to create a documentation page

        :param basename:        EXAMPLE: "my_file_being_uploaded.txt"
        :param full_filename:   EXAMPLE: "D:/tmp/my_file_being_uploaded.txt"
        :return:                HTML code to populate a documentation page
        """
        # Read in the python file
        n_chars_to_show = 400       # Number of initial characters in the file to show to the user
        try:
            with open(full_filename, 'r') as fh:
                file_contents = fh.read()
                print(f"\n--- First {n_chars_to_show} bytes of uploaded file:\n{file_contents[:n_chars_to_show]}")
        except Exception:
            return f"import_python_file(): File I/O failed (on uploaded file {full_filename})"


        pattern = cls.define_pattern()      # String that will be used for REGEX parsing
        print("Pattern used for the matches: ", pattern)

        all_matches = re.findall(pattern, file_contents, re.DOTALL)
        # It returns a (possibly-empty) list of tuples of capture groups
        # [Note: it could also be a list of strings, if there was only 1 capture group in pattern, but that's not what we do here]

        # The following is just to provide a printout of the results of the match
        print(f"\n-- {len(all_matches)} MATCHES found--")
        for m in all_matches:
            abridged_match = []
            for el in m:
                abridged_match.append(el[:60])
            print(f"match: {abridged_match}")


        if all_matches:     # If the list is not empty, i.e. if matches were found
            # Produce a simple HTML table to present to the user the various matches that were found.
            # Each match will be presented on a separate row; each matched pattern (within a match) will appear as a separate column
            scan_results = cls.prepare_preview_table(all_matches)
        else:
            print("NO MATCHES found")
            return f"File `{basename}` uploaded successfully, but <b>NO MATCHES</b> found"


        # Zap all private methods, as well as methods whose names contain "_OLD" or "_OBSOLETE"
        all_matches_pared_down = []
        for match in all_matches:
            method_name = match[0]
            args = match[1]
            if method_name and method_name[0] == "_" and method_name != "__init__" and args != "DIVIDER":
                print(f"Dropping private method `{method_name}()`")
            elif ("_OLD" in method_name) or ("_OBSOLETE" in method_name):
                print(f"Dropping deprecated method `{method_name}()`")
            else:
                all_matches_pared_down.append(match)


        # Put together the parsing data as a Pandas dataframe
        column_names = ["method_name", "args", "return_value", "comments", "class_name", "class_description"]
        df = pd.DataFrame(all_matches_pared_down, columns = column_names)
        #print("Number of records matched:", df.count())
        '''
        print(df.head(10))
        print("...")
        print(df.tail(10))
        '''

        # Modify the "args" column, by applying the "clean_up_args" to each of its entries
        df["args"] = df["args"].map(cls.clean_up_args)


        # Produce HTML code to documented the python file from its parsing data
        htm = cls.generate_documentation(df)

        safe_htm = htm.replace("<", "&lt;").replace(">", "&gt;")

        # TODO:  < , > and & in code comments are still not sufficiently protected
        #        Need to replace  <  with  &lt;
        #        Need to replace  &  with  &amp;
        #        Try it out on documenting the method FullTextIndexing.split_into_words()

        return f"File `{basename}` uploaded successfully.  <b>{len(all_matches)} MATCH(ES)</b> found.  Nothing added to database.  " \
               f"Scan results:<br><br>{scan_results}<br><br>" \
               f"<b>HTML:</b><br><br><pre>{safe_htm}</pre>"



    @classmethod
    def prepare_preview_table(cls, data :[tuple]) -> str:
        """
        Produce and return a simple HTML table from a list of row data;
        each element of the list should be a tuple with the data for the cells on that row

        :param data:    A list of tuples (for example, originating as a tuple of RegEx capture groups)
        :return:        HTML code to define a simple table
        """
        assert type(data) == list, \
                "prepare_preview_table(): incorrect format of argument, which should be a list of tuples"

        scan_results = "<table border='1' style='border-collapse: collapse'>"
        for match_instance in data:   # Consider each match in turn
            assert type(match_instance) == tuple, \
                "prepare_preview_table(): incorrect format of argument, which should be a list of tuples"
            scan_results += "<tr>"
            for item in match_instance:
                scan_results += f"<td>{item}</td>"
            scan_results += "</tr>"

        scan_results += f"</table>"

        return scan_results



    @classmethod
    def define_pattern(cls) -> str:
        """
        Pattern for the creation of documentation from python files.

        The python files has some expectations about their formatting; for example, as used in neoschema.py

        Compose and return a REGEX pattern for parsing of data files, for use in import_datafile()

        The pattern is expected to be used in a re.findall() that uses re.DOTALL as the last argument

        :return:    A string with a REGEX pattern
        """
        # The R before the string escapes all characters ("raw strings" aka "verbatim strings")

        '''
        PART A - Python Class Methods
        '''

        pattern_1 = R'def\s+([a-zA-Z_][a-zA-Z0-9_]*)'   # Match and capture the method name:
                                                        #   "def" followed by 1 or more blanks, followed by
                                                        #   (one letter or underscore, followed by any number of letters, numbers or underscores)

        pattern_2 = R'\((.*?)\)'                        # Match and capture (non-greedy) everything inside the round parentheses after method name

        #pattern_3 = R'(?:\s*->\s*(.*?)\s*)?:'
        #pattern_3 = R'(?:\s*->\s*(.*?)\s*)?:(?:\s*#.*?\n)?'
        pattern_3 = R'(?:\s*->\s*(.*?)\s*)?:.*?\n'              # Match and capture (non-greedy) the method's return type - which may or may not be present
                                                                # Advance (there might be blanks and/or optional comments) until the end of the line
        '''
            (?:                 Start of NON-capturing grouping
                \s*                 0+ blanks
                ->                  Literal "->"
                \s*                 0+ blanks
                (                   Start of capture group
                    +*?                 Any single character, 1 or more times (non-greedy)
                )                   End of capture group
                \s*                 0+ blanks
            )                   End of non-capturing grouping
            ?                   Make the preceding group optional
            :                   Literal ":"
            .*?                 Any single character, 0 or more times (non-greedy)
            \n                  End of line           
        '''


        pattern_4 = R'(?:\s+"""(.*?)""")?'          # Match and capture (non-greedy) everything within the following pair of """
        '''
            (?:                 Start of NON-capturing grouping
                \s+                 1+ blanks
                """                 Literal triple double quotes
                (                   Start of capture group
                    .*?                 Any single character, 0 or more times (non-greedy)
                                        Note: newlines also matched because the calling functions uses re.DOTALL
                                              as the 3rd argument in re.findall()
                )                   End of capture group
                """                 Literal triple double quotes
            )                   End of non-capturing grouping
            ?                   Make the preceding group optional
        '''


        pattern_A = pattern_1 + pattern_2 + pattern_3 + pattern_4


        '''
        PART B - Python Class Names
        '''
        # Match and capture a python class name
        #       EXAMPLE 1:  "class NeoAccessCore:"
        #       EXAMPLE 2:  "class NeoAccess(NeoAccessCore):"
        pattern_1 = R'class\s+([a-zA-Z][a-zA-Z0-9_]*)(?:\([a-zA-Z][a-zA-Z0-9_]*\))?\s*:'
        '''
            class               Literal "class"
            \s+                 1+ blanks
            (                   Capture start
                [a-zA-Z]            letter
                [a-zA-Z0-9_]*       0+ alphanumeric or underscore
            )                   Capture end
            (?:                 Start of NON-capturing grouping
                \(                  Literal "("
                [a-zA-Z]            letter
                [a-zA-Z0-9_]*       0+ alphanumeric or underscore  
                \)                  Literal ")"    
            )                   End of non-capturing grouping
            ?                   Make the preceding group optional
            \s*                 0+ blanks
            :                   Literal ":"
        '''

        pattern_2 = R'.+?"""(.*?)"""'               # Match and capture (non-greedy) everything within the following pair of """
        #   The .+? at the beginning = 1 or more characters (non-greedy).  Note: that required character is the preceding newline
        pattern_B = pattern_1 + pattern_2


        pattern = f"(?:{pattern_A})|(?:{pattern_B})"    # Deal with alternations.  Note: "?:" means that the parentheses are NOT a capture group

        return pattern



    @classmethod
    def clean_up_args(cls, s:str) -> str:
        """
        Strip off the leading "cls" or "self", together with the comma after it,
        from a string that is meant to represent the arguments of a python class method declaration.
        Leading/trailing blanks are also eliminated.
        If s is simply "cls" or "self" (i.e, no args), then return a blank string

        EXAMPLES:   "   cls, r, x    "                  gives  "r, x"
                    "   self   , r:int,  x :list    "   gives  "r:int,  x :list"

        :param s:   String with a list of arguments of a python class method
        :return:    Cleanup-up version, stripped of leading "cls" or "self"
        """
        s = s.strip()
        if s == "cls" or s == "self":
            return ""

        pos_first_comma = s.find(",")       # Position in the string of the first comma
        if pos_first_comma == -1:           # If not found
            return s

        first_arg = s[:pos_first_comma]
        first_arg = first_arg.strip()       # Cleaned-up version of the 1st argument (the expected "cls" or "self")

        if (first_arg != "cls") and (first_arg != "self"):      # If not found
            return s

        abridged = s[pos_first_comma+1 :]   # Ditch the early part of the string, up to - and including - the first comma
        return abridged.strip()             # Eliminate lading/trailing blanks



    @classmethod
    def generate_documentation(cls, df :pd.DataFrame) -> str:
        """
        Print out, and return as a string, the HTML code to create a documentation page,
        from a Pandas data frame containing the data about the various elements
        of the python file.
        TODO: probably switch to a Flask template

        Note: the HTML code also contains references to some CSS classes for styling.

        :param df:  A Pandas data frame, with the following columns:
                        class_name, class_description, method_name, args, return_value, comments
        :return:    A string with HTML code
        """

        toc = "<div class='sidebar-left'>\n"    # Table of contents, with links to Classes and methods
        htm = ""                                # HTML for the main body of the documentation page, EXCLUSIVE of the above Table of Contents
        python_class_name = ""
        first_python_class = True               # Flag indicating whether the currently-parsed python Class is the first being encountered

        for ind in df.index:    # EXAMPLE of df.index: RangeIndex(start=0, stop=11, step=1)
            # For each row in the Pandas data frame

            if df['class_name'][ind]:                   # Start documenting a new pythons class
                python_class_name = df['class_name'][ind]
                python_class_description = df['class_description'][ind]

                toc += f"\n    <br><a href='#{python_class_name}' style='font-weight:bold; font-size:18px'>Class {python_class_name}</a><br>\n"

                if first_python_class:
                    first_python_class = False
                else:
                    htm += "<br><br><hr>"       # Skipped if it's the first Class

                htm += f"<a name='{python_class_name}'></a>\n"
                htm += f"<h1 class='class-name'>Class {python_class_name}</h1>\n"
                htm += f"<pre>{python_class_description}</pre>\n\n\n"

            elif "____" in df['method_name'][ind]:      # A BrainAnnex styling convention to indicate a new section
                section_name = df['method_name'][ind]
                clean_name = section_name.replace("_", " ").strip()

                toc += f"\n    <span style='margin-left:15px; font-weight:bold'>{clean_name}:</span><br>\n"
                htm += f"<br><h2 class='section-header'>{clean_name}</h2>\n\n"

            else:           # Document an individual class method
                method_name = df['method_name'][ind]
                anchor_name = f"{python_class_name}_{method_name}"   # Needed because some method names (such as __init__) may appear in multiple classes
                                                                     # EXAMPLE:  "NeoAccess_query"

                toc += f"    <a href='#{anchor_name}' style='margin-left:40px'>{method_name}</a><br>\n"

                htm += f"<a name='{anchor_name}'></a>\n"
                htm += "<table class='cd-main'>\n"
                htm += "<tr><th>name</th><th>arguments</th><th>returns</th></tr>\n"

                htm += "<tr>"
                #print(df["method_name"][ind], df["args"][ind], df["comments"][ind])
                htm += f"<td class='cd-fun-name'>{df['method_name'][ind]}</td>"
                htm += f"<td>{df['args'][ind]}</td>"
                htm += f"<td>{df['return_value'][ind]}</td>"

                htm += "</tr>\n"

                htm += "<tr>"
                htm += "<td colspan=3 class='cd-description'>\n"
                htm += f"<pre>{df['comments'][ind]}</pre>\n"
                htm += "</td>\n"
                htm += "</tr>\n"
                htm += "</table>\n\n\n"


        toc += "\n<br>\n</div>    <!-- sidebar-left -->\n\n\n\n\n"     # Complete the Table of Contents

        '''
        print("###################################################################################")
        print(toc)
        print(htm)
        print("###################################################################################")
        '''

        return toc + htm
