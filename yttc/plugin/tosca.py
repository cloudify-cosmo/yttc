"""Tosca output plugin

Idea copied from tree.
"""

from pyang import plugin
from pyang import statements
import StringIO
import optparse
import pyang.plugins.tree
import pyang.translators.dsdl
import sys
import yaml
from collections import OrderedDict


DERIVED_FROM = 'cloudify.netconf.nodes.xml_rpc'


def pyang_plugin_init():
    plugin.register_plugin(ToscaPlugin())


class ToscaPlugin(plugin.PyangPlugin):
    def add_output_format(self, fmts):
        self.multiple_modules = True
        fmts['tosca'] = self

    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--tosca-help",
                                 dest="tosca_help",
                                 action="store_true",
                                 help="Print help on tosca plugin and exit")]
        g = optparser.add_option_group("Tosca output specific options")
        g.add_options(optlist)

    def setup_ctx(self, ctx):
        if ctx.opts.tosca_help:
            print_help()
            sys.exit(0)

    def setup_fmt(self, ctx):
        ctx.implicit_errors = False

    def emit(self, ctx, modules, fd):
        emit_yaml(ctx, modules, fd)


def print_help():
    print("""
    Convert YANG files to TOSCA files with YAML format
""")


def emit_yaml(ctx, modules, fd):
    xmlns = {}
    main_module = None
    uses_modules = {}
    for module in modules:
        if module.keyword == 'submodule':
            message = "Can't work with submodule."
            fd.write(message)
            return False, message
        namespace = "{}".format(module.search_one('namespace').arg)
        children = _collect_children(module)
        if children:
            main_module = "{}".format(module.arg)
            xmlns["_"] = namespace
        else:
            prefix = "{}".format(module.i_prefix)
            xmlns[prefix] = namespace
        rev = module.search_one('revision')
        if rev:
            revision = "{}".format(rev.arg)
        else:
            revision = 'unknown'
        uses_modules.update({"{}".format(module.arg): revision})
    if not main_module:
        message = "Can't find main module."
        fd.write(message)
        return False, message
    dsdl = _get_dsdl_representation(ctx, modules)
    output = {
        'data_types': {
            '_config': {
                'properties': {
                }},
            '_rpc': {
                'properties': {
                }}},
        'node_types': {
            main_module: {
                'derived_from': DERIVED_FROM,
                'properties': {
                    'config': {
                        'required': False,
                        'type': '_config'},
                    'rpc': {
                        'required': False,
                        'type': '_rpc'},
                    'metadata': {
                        'default': {
                            'dsdl': dsdl,
                            'xmlns': xmlns,
                            'modules': uses_modules}}}}}}
    for module in modules:
        _handle_edit_config(module, main_module, output)
        _handle_custom_rpc(module, main_module, output)
    dump = yaml.dump(output, allow_unicode=True,
                     default_flow_style=False)
    treeout = _get_tree_representation(ctx, modules)
    fd.write(dump + treeout)
    return True, 'Converted'


def _handle_edit_config(module, main_module, output):
    children = _collect_children(module)
    if children:
        type_info = {}
        _handle_children(children, module, type_info, output)
        output['data_types']['_config']['properties'].update(type_info)


def _handle_custom_rpc(module, main_module, output):
    rpcs = [ch for ch in module.i_children
            if ch.keyword == 'rpc']
    for rpc in rpcs:
        rpc_name = "{}".format(rpc.arg)
        input_stmt = rpc.search_one('input')
        node_info = output['data_types']['_rpc']['properties']
        if input_stmt:
            node_info.update({rpc_name: {'type': _type(rpc_name),
                                         'required': False}})
            type_info = {}
            children = _collect_children(input_stmt)
            _handle_children(children, module, type_info, output)
            output['data_types'][_type(rpc_name)] = {'properties':
                                                     type_info}
        else:
            node_info.update({rpc_name: {'default': {},
                                         'required': False}})


def _collect_children(statement):
    return [ch for ch in statement.i_children
            if ch.keyword in statements.data_definition_keywords]


def _handle_children(children, module, type_info, output):
    for c in children:
        if _not_configurable(c):
            continue
        child_name = _get_child_name(module, c)
        if c.keyword == 'choice':
            for choice in c.i_children:
                _handle_children(choice.i_children, module, type_info, output)
            continue
        type_info[child_name] = {}
        _update_required(c, type_info[child_name])
        if c.keyword == 'leaf-list':
            datatype = c.search_one('type')
            _update_decription(type_info[child_name],
                               datatype.arg)
        else:
            new_type = _set_type(c, type_info[child_name])
            _set_default(c, type_info[child_name], new_type)
        if hasattr(c, 'i_children') and c.i_children:
            if c.keyword == 'list':
                _update_decription(type_info[child_name],
                                   child_name)
            else:
                type_info[child_name]['type'] = _type(child_name)
            _add_new_data_type(c, module, output)


def _add_new_data_type(statement, module, output):
    children = _collect_children(statement)
    if not children:
        return
    type_info = output['data_types']
    type_name = _type(_get_child_name(module, statement))
    type_info[type_name] = {}
    type_info[type_name]['properties'] = {}
    _handle_children(children, module,
                     type_info[type_name]['properties'], output)


def _get_child_name(module, statement):
        if statement.i_module.i_modulename == module.i_modulename:
            return "{}".format(statement.arg)
        else:
            return "{}@{}".format(statement.i_module.i_prefix, statement.arg)


def _not_configurable(statement):
    config = statement.search_one('config')
    return config and config.arg == "false"


def _update_required(statement, place):
    def _is_mandatory(statement):
        mandatory = statement.search_one('mandatory')
        return mandatory and mandatory.arg == "true"
    place.update({'required': bool(_is_mandatory(statement))})


def _update_decription(place, text):
    if 'description' not in place:
        place['description'] = ''
    place['description'] = "[List_of: {}]{}".format(_type(text),
                                                    place['description'])


def _set_default(statement, place, new_type):
    default = statement.search_one('default')
    if default:
        default = default.arg
        if new_type == 'float':
            default = float(default)
        elif new_type == 'boolean':
            default = bool(default)
        elif new_type == 'integer':
            default = int(default)
        elif new_type == 'string':
            default = str(default)
        place.update({'default': default})


def _set_type(statement, place):
    convertor = {'string': 'string',
                 'leafref': 'string',
                 'decimal64': 'float',
                 'boolean': 'boolean',
                 'int8': 'integer',
                 'int16': 'integer',
                 'int32': 'integer',
                 'int64': 'integer',
                 'uint8': 'integer',
                 'uint16': 'integer',
                 'uint32': 'integer',
                 'uint64': 'integer'}
    datatype = statement.search_one('type')
    if datatype:
        arg = datatype.arg
        if arg in convertor:
            place.update({'type': convertor[arg]})
            return convertor[arg]


def _get_tree_representation(ctx, modules):
    tree = StringIO.StringIO()
    pyang.plugins.tree.emit_tree(ctx, modules, tree, None, None)
    return '\n#' + tree.getvalue().replace('\n', '\n#')


def _get_dsdl_representation(ctx, modules):
    dsdl = StringIO.StringIO()
    pyang.translators.dsdl.emit_dsdl(ctx, modules, dsdl)
    return "{}".format(dsdl.getvalue())


def _type(name):
    return name + '_type'
