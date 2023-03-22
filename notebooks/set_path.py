"""
A copy of this file should be present in every notebook folder
that isn't the BrainAnnex project's root folder.

Only needed when JupyterLab isn't started with an option
that adds the project's root folder to sys.path
(as done, for example, in the "quick.bat" script in BrainAnnex root folder.)

However, there's no harm in using this module under all circumstances,
even if the project's root folder is already present in sys.path.

Adding the project's root folder to sys.path permits
the use of absolute paths in import of modules into notebooks.

# IMPORTANT: change the level number as needed, 
             in the function call at the very bottom of this file!


TO USE:
------
Insert the following line at the top of your notebooks that reside in the 
same folder as this set_path.py file:

import set_path
"""


import sys
import pathlib


def add_ancestor_dir_to_syspath(level: int, verbose=True) -> None:
    """
    Add the ancestor (at the specified level) of the current working directory to the system path.
    Doing so will allow the use of absolute paths (starting at that ancestor folder)
    in import of modules into notebooks.

    :param level:   The number of levels to go up,
                        to reach the project's home directory,
                        from the directory containing this notebook
    :param verbose: Flag indicating whether to print out 
                        the name of the directory newly added to syspath
    :return:        None
    """
    directory = pathlib.Path.cwd()      # Start with the current working directory

    for _ in range(level):
        directory = directory.parent    # Navigate up one level in the file hierarchy

    sys.path.append(str(directory))

    if verbose:
        print(f"Added '{directory}' to sys.path")

        
####################################################################################################
add_ancestor_dir_to_syspath(level=1)    # The value for the level will need to be adjusted,
                                        # based on what folder this file resides in,
                                        # relative to the project's home folder
