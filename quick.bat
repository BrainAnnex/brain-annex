:: Quick start for Jupyter Lab (see IMPORTANT NOTE below: must change the folder name below!)

:: This batch file can be run, for example, by typing its name, as  .\quick   in
::     the PyCharm TERMINAL window tab at the bottom (not to be confused with the Python console!)

:: ****** IMPORTANT ****** - FIRST CHANGE THE FOLDER NAME BELOW TO THE LOCATION ON YOUR MACHINE!!

:: Add the root of the project files to the value of the sys.path seen inside the execution of the notebooks
:: EXAMPLE (on Windows):  set PYTHONPATH=\Docs\- MY CODE\My Project Name
set PYTHONPATH=\PATH_TO_YOUR_PYCHARM_PROJECT

:: Start Jupyter Lab (if a port other than the default 8888 is desired, use the option --port YOUR_PORT_NUMBER)
.\venv\Scripts\jupyter-lab