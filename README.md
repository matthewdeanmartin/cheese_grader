Project Description
----
Is that package you'd like to take a dependency on any good?

This question turns out to call for a different standard of quality than you'd use for your own code, since you can't dictate formatting, working lint & mypy warnings and you might not even want to run setup & the tests just yet. A wonderful library might not have a single annotation and would fail mypy, it might be formatted perfectly but not to pep8, it might have rigorous unit tests but pylint finds a million quibbles.

But a wonderful library can be expected to have syntactically valid python, not be empty of all .py files, have more than a single commit to github, a homepage that doesn't return 404, and so on. A library with a README, frequent and recent updates might be wonderful, but if they aren't there, it doesn't indicate anything one way or the other.

These criteria would be a bit weird to apply to your own code, they are too minimal or don't actually help your code run better. But these criteria are not bad for evaluating other libraries, expecially in bulk & without doing a full installation of what could be malicious code.

Two big alternatives:

libraries.io - CodeRank
Package Health score, eg. https://snyk.io/advisor/python/pyrankvote

Docs
-----
- [Prior Art](docs/prior_art.md)
- [TODO](docs/TODO.md)
- [Design Plans](docs/design.md)