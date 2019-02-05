Project Description
-------------------

Is that package you’d like to take a dependency on any good?

This question turns out to call for a different standard of quality than
you’d use for your own code, since you can’t dictate formatting, working
lint & mypy warnings and you might not even want to run setup & the
tests just yet. A wonderful library might not have a single annotation
and would fail mypy, it might be formatted perfectly but not to pep8, it
might have rigorous unit tests but pylint finds a million quibbles.

But a wonderful library can be expected to have syntactically valid
python, not be empty of all .py files, have more than a single commit to
github, a homepage that doesn’t return 404, and so on. A library with a
README, frequent and recent updates might be wonderful, but if they
aren’t there, it doesn’t indicate anything one way or the other.

These criteria would be a bit weird to apply to your own code, they are
too minimal or don’t actually help your code run better. But these
criteria are not bad for evaluating other libraries, expecially in bulk
& without doing a full installation of what could be malicious code.

Existing Similar Solutions
--------------------------

-  `kwalitee <https://github.com/inveniosoftware/kwalitee>`__ This is a
   multi-tool linter. Many exist like this, but it is used by Cheesecake
-  `Cheesecake <https://pypi.org/project/Cheesecake/>`__ Calculates a
   score. Faults packages for things that are rarely complied with, such
   as a missing a FAQ file. *Python 2 only*. After a code review, I am
   convinced that this will never be evolved to Python 3.

Garbage detection
-----------------

-  does python -compileall work?

   -  no? pure garbage, serious syntax errors or dead code

-  does it format with black?

   -  no? it is not python 3 or it some sort of garbage

-  can a module be found?

   -  likely garbage or an unusual project layout

-  homepage dead?
-  parked package (either ad hoc or via
   https://pypi.org/project/pypi-parker/ )
-  known malicious package (although detecting malicious packages is out
   of scope)
-  trivial number of lines of code

   -  0 is trash.
   -  1 to 10 is a bad idea, staticly link that (i.e. copy-paste), don’t
      add the overhead of a library.
   -  might just mean it isn’t python, some libraries are data libraries
      or C++ libraries hosted by pypi

Good signs:
-----------

-  many releases
-  2+ maintainers
-  claims production (unreliable signal!)
-  used by someone
-  more than x lines of code (<10 is garbage, code that could be
   vendorized)
-  few dependencies (unless an app)
-  has docs
-  has requirements.txt and/or Pipfile
-  has Manifest file
-  metadata filled in
-  has easily findable license (hard problem)

Expensive/Unreliable Signs
--------------------------

-  Installer runs w/o exception in promised python versions
-  Little lint (what if they are good but don’t lint or format?)
-  Little mypy (what if they never bothered to annotate or used a weird
   annotation syntax?)
-  test run (what if thy got complex depedencies, such as web servers
   and databases)
-  convertable with 2to3 if py2 only
