import io
import pyang
from tosca import emit_yaml


# Parameters:
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
            return False, "error %s: %s\n" % (filename, str(ex))
        except UnicodeDecodeError as ex:
            s = str(ex).replace('utf-8', 'utf8')
            return False, "%s: unicode error: %s\n" % (filename, s)
        module = ctx.add_module(filename, text)
        if module is None:
            return False, "Can't load module: {}".format(filename)
        else:
            modules.append(module)
    emit_yaml(ctx, modules, out_fd)
    return True, 'Converted'
