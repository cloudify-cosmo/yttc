import os
import subprocess
import sys
import yttc


def cli():
    plugin_path = os.path.join(os.path.dirname(yttc.__file__), 'plugin')
    command = "--plugindir {} -f tosca ".format(plugin_path)
    options = ' '.join(sys.argv[1:])
    subprocess.call("pyang {} {}".format(command, options ), shell=True)
