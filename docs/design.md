This is a essentially a build script, except optimize for an arbitrary project
which may have never used any particular quality gate. 

Garbage detection
--
- does python -compileall work?
	- no? pure garbage, serious syntax errors or dead code
- does it format with black?
	- no? it is not python 3 or it some sort of garbage
- can a module be found?
	- likely garbage or an unusual project layout 
- homepage dead?
- parked package (either ad hoc or via https://pypi.org/project/pypi-parker/ )
- known malicious package (although detecting malicious packages is out of scope)
- trivial number of lines of code
    - 0 is trash.
    - 1 to 10 is a bad idea, staticly link that (i.e. copy-paste), don't add the overhead of a library.
    - might just mean it isn't python, some libraries are data libraries or C++ libraries hosted by pypi
    
Good signs:
---
- many releases
- 2+ maintainers
- claims production (unreliable signal!)
- used by someone
- more than x lines of code (<10 is garbage, code that could be vendorized)
- few dependencies (unless an app)
- has docs 
- has requirements.txt and/or Pipfile
- has Manifest file
- metadata filled in
- has easily findable license (hard problem)

Expensive/Unreliable Signs
---
- Installer runs w/o exception in promised python versions
- Little lint (what if they are good but don't lint or format?)
- Little mypy (what if they never bothered to annotate or used a weird annotation syntax?)
- test run (what if thy got complex depedencies, such as web servers and databases)
- convertable with 2to3 if py2 only
