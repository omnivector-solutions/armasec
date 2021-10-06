=========================
 Contributing Guidelines
=========================

Security Concerns
=================

Before any further discussion, a point about security needs to be addressed.
*If you find a serious security vulnerability that could affect current users,
please report it to maintainers via email or some form of private
communication*. For other issue reports, see below.


Thanks!
=======

First, thank you for your interest in contributing to armasec! Even
though this is a small security project, it takes a bit of work to keep
it maintained. All contributions help and improve the extension.


Contact Us
==========

The maintainers of armasec can be reached most easily via email::

  * Omnivector Development Team <info@omnivector.solutions>


Conduct
=======

Everyone's conduct should be respectful and friendly. For most people, these
things don't need to be spelled out. However, to establish a baseline of
acceptable conduct, the armasec project expects contributors to adhere
to a customized version of the
`Python Software Foundation's Code of Conduct <https://www.python.org/psf/codeofconduct>`_.
Please see the `CONDUCT guide <CONDUCT.rst>`_ to reference the code of conduct.
Any issues working with other contributors should be reported to the maintainers


Contribution Recommendations
============================

Github Issues
-------------

The first and primary source of contributions is opening issues on github.
Please feel free to open issues when you find problems or wish to request a
feature. All issues will be treated seriously and taken under consideration.
However, the maintainers may disregard/close issues at their discretion.

Issues are most helpful when they contain specifics about the problem they
address. Specific error messages, references to specific lines of code,
environment contexts, and such are extremely helpful.


Code Contributions
------------------

Code contributions should be submitted via pull-requests on github. Project
maintainers will review pull-requests and may test new features out. All
merge requests should come with commit messages that describe the changes as
well as a reference to the issue that the code addresses.

Code contributions should follow best-practices where possible. Use the
`Zen of Python <https://www.python.org/dev/peps/pep-0020/>`_ as a guideline.
All code must pass our quality checks. Run ``make qa`` to check the quality.

Adding addtional dependencies should be limited except where needed
functionality can be easily added through pip packages. Please include
dependencies that are only applicable to development and testing in the
dev dependency list. Packages should only be added to the dependency lists if:

* They are actively maintained
* They are widely used
* They are hosted on pypi.org
* They have source code hosted on a public repository (github, gitlab, bitbucket, etc)
* They include tests in their repositories
* They include a software license


Documentation
=============

Help with documentation is *always* welcome.

The armasec project hosts its documentation on
`a github page <https://omnivector-solutions.github.io/armasec/>`_.

Documentation lives in the `docs` subdirectory. Added pages should be
referenced from the table of contents.

Documentation should be clear, include examples where possible, and reference
source material as much as possible.

All modules, classes, methods, etc should include docstrings. These docstrings
should be direct and clear. All docstrings should be
`sphinx compatible docstrings <https://www.python.org/dev/peps/pep-0257/>`_.

Documentation through code comments should be kept to a minimum. Code should
be as self-documenting as possible. If a section of code needs some explanation,
the bulk of it should be be presented in the docstrings.


Non-preferred Contributions
===========================

There are some types of contribution that aren't as helpful and are not as
welcome:

* Complaints without suggestion
* Criticism about the overall approach of the extension
* Copied code without attribution
* Promotion of personal packages/projects without due need
* Sarcasm/ridicule of contributions or design choices
