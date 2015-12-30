yttc - YANG to TOSCA converter
=====================

Library for converts YANG  modules into TOSCA node types for Cloudify orchestration framework.
[Cloudify](http://docs.getcloudify.org)

YANG - A Data Modeling Language for the Network Configuration Protocol
[RFC 6020](https://tools.ietf.org/html/rfc6020)

TOSCA - Topology and Orchestration Specification for Cloud Applications
[TOSCA](http://docs.oasis-open.org/tosca/TOSCA/v1.0/TOSCA-v1.0.html)

Installation
============
This module require Python 2.
```
$git clone https://github.com/cloudify-cosmo/yttc
$cd yttc
$ pip install .
````
Usage
=====
For converting yang modules, you must call:

`yacc.convert(filenames, out_fd)`

Where:
* **filenames** - list of filenames, of yang files
* **out_fd** - file descriptor. It may be descriptor of open file, or StringIO class.

The output will be written to the out_fd.

# Examples:
## With StringIO
```
> import yttc
> import StringIO
> output = StringIO.StringIO()
> yttc.convert( ['acme.yang', 'acme-augment.yang'], output)
> print output.getvalue()
> output.close()
```
## With standart output
```
> import yttc
> import sys
> output = sys.stdout
> yttc.convert( ['acme.yang', 'acme-augment.yang'], output)
```

## With file
```
> import yttc
> import sys
> output = file.open('acme.yaml', 'w')
> yttc.convert( ['acme.yang', 'acme-augment.yang'], output)
```

Testing
=======
Directory examples contains simple YANG files for testing purpose.

For running converter from commad line you can use "test.py" from 'tests' directory:
```
cd test
python test.py ../examples/acme.yang
```

Using converter in command line
===============================
This library has simple wrapper for `pyang` command line utility: **`yttc`**

pyang is a YANG validator, transformator and code generator, written in python.
It can be used to validate YANG modules for correctness, to transform YANG modules
into other formats, and to generate code from the modules.
https://github.com/mbj4668/pyang


Instead of run:
`pyang --plugindir /home/user/yttc/plugin -f tosca acme.yang`

You can just run:
`yttc acme.yang`

Also you can use other options, that `pyang` support.
For example:
`yttc -o acme.yaml acme.yang`
