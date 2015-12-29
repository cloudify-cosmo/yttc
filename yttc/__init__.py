import sys
import io
import pyang
from tosca import emit_yaml

#Parameters:
#  filenames - list of YANG files
#  out_fd - file descriptor, where output will be written
def convert(filenames, out_fd):
    repos = pyang.FileRepository('.')
    ctx = pyang.Context(repos)
    modules = []
    for filename in filenames:
        try:
            fd = io.open(filename, "r", encoding="utf-8")
            text = fd.read()
        except IOError as ex:
            sys.stderr.write("error %s: %s\n" % (filename, str(ex)))
            sys.exit(1)
        except UnicodeDecodeError as ex:
            s = str(ex).replace('utf-8', 'utf8')
            sys.stderr.write("%s: unicode error: %s\n" % (filename, s))
            sys.exit(1)
        module = ctx.add_module(filename, text)
        if module is None:
            sys.stderr.write("Can't load module: {}".format(filename))
            sys.exit(1)
        else:
            modules.append(module)
    emit_yaml(ctx, modules, out_fd)
