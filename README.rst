Ansible argument specification generator
========================================

This package contains code for Ansible argument specification program. Its main
audience are Ansible module maintainers that would like to reduce the
duplication in their modules by generating the argument specification directly
from the module's user documentation.


Quickstart
----------

Documentation extractor is published on PyPI_ and we can install it using
``pip``::

   $ pip install ansible-argspec-gen[base]     # This will install ansible-base
   $ pip install ansible-argspec-gen[ansible]  # This will install ansible
   $ pip install ansible-argspec-gen           # We need to install ansible or
                                               # ansible-base ourselves

.. _PyPI: https://pypi.org/

If the previous command did not fail, we are ready to start updating our
modules. When we use the generator for the first time, we need to perform the
following three steps:

1. Add two comments to the module's source that will mark the location for the
   generated code. By default, the generator searched for the ``# AUTOMATIC
   MODULE ARGUMENTS`` comment, but this can be changed with the ``--marker``
   command-line parameter.
2. Run the generator, possibly in dry-run and diff mode first to spot any
   issues.
3. Remove any hand-writen remnants that are not needed anymore.

For example, let us assume that the first few lines of our module's main
function looks like this before the generator run::

   def main():
       # AUTOMATIC MODULE ARGUMENTS
       # AUTOMATIC MODULE ARGUMENTS

       module = AnsibleModule(

If we run the the generator now in check mode with difference priting switched
on, we will get back something like this::

   $ ansible-argspec-gen --diff --dry-run plugins/modules/route.py
   --- ../ansible_collections/steampunk/nginx_unit/plugins/modules/route.py.old
   +++ ../ansible_collections/steampunk/nginx_unit/plugins/modules/route.py.new
   @@ -359,6 +359,52 @@

    def main():
        # AUTOMATIC MODULE ARGUMENTS
   +    argument_spec = {
   +        "global": {"default": False, "type": "bool"},
   +        "name": {"type": "str"},
   +        "socket": {"type": "path"},
   +        "state": {
   +            "choices": ["present", "absent"],
   +            "default": "present",
   +            "type": "str",
   +        },
   +    }
   +    required_if = [("global", False, ("name",)), ("state", "present", ("steps",))]
        # AUTOMATIC MODULE ARGUMENTS

        module = AnsibleModule(

Once we are happy wth the proposed changes, we can write them to the file::

   $ ansible-argspec-gen plugins/modules/route.py

If we update the module's documentation, we can simply rerun the previous
command and generator will take or updating the  specification. Note that the
generator will **overwrite** the content between the markers, so make sure you
do not manually modify that part of the file or you will loose the changes on
next update.


Writing module documentation
----------------------------

Generating argument specification for the ``AnsibleModule`` class should work
on any module that has a documentation. But getting the generator to produce
other parameters such as conditional requirements takes a bit of work.

In order to generate a ``required_if`` specification, our parameters need to
have a sentence in its description that fits the template *required if
I({param_name}) is C({param_value})*. The next example::

   options:
     name:
       description:
         - Name of the resource. Required if I(state) is C(present).

will produce the following specification::

   required_if = [("state", "present", ("name", ))]

Another thing that generator knows how to produce is the ``mutually_exclusive``
specification. The pattern that the generator is looking for in this case is
*Mutually exclusive with I({param1}), I({param2}), and I({param3})*, where the
number of parameters that we can specify is not limited. Example::

   options:
     processes:
       description:
         - Dynamic process limits.
         - Mutually exclusive with I(no_processes).
     no_processes:
       description:
         - Static process limit.
         - Mutually exclusive with I(processes).

This will produce::

   mutually_exclusive = [("no_processes", "processes")]


Development setup
-----------------

Getting development environment up and running is relatively simple if we
have ``pipenv`` installed::

   $ pipenv update

To test the extractor, we can run::

   $ pipenv run ansible-argspec-gen
