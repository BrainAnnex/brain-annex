:: Quick start for Jupyter Lab (see IMPORTANT NOTE below: must change the folder name below!)

:: This batch file can be run, for example, by typing its name (exclusive of the .bat) in
::     the PyCharm TERMINAL window tab at the bottom (not to be confused with the Python console!)

:: ****** IMPORTANT ****** - FIRST CHANGE THE FOLDER NAME BELOW TO THE LOCATION ON YOUR MACHINE!!

:: Add the root of the project files to the value of the sys.path seen inside the execution of the notebooks
set PYTHONPATH=\Docs\- MY CODE\Brain Annex\BA-Win7

:: Start Jupyter Lab (if a port other than the default 8888 is desired, use the option --port YOUR_PORT_NUMBER)
jupyter-lab