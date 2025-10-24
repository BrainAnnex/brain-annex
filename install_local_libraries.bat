:: Just for debugging, to switch from the repository version of GraphAccess
:: to a local one, in a sibling directory of this project's top directory.
:: This is done by means of a pip install of the local package in "editable" mode, which means:
:: Instead of copying the code into your Python environment, pip creates a symbolic link to your source directory.
:: Changes you make to the code are immediately reflected in the installed package — no need to reinstall.

:: This batch file can be run, for example, by typing its name (exclusive of the .bat) in
::     the PyCharm TERMINAL window tab at the bottom (not to be confused with the Python console!)
::      On Win11, also need to prefix  ".\"          EXAMPLE:   .\install_local_libraries

.\venv\Scripts\python -m pip install -e ..\GraphAccess