import sys
import paramiko
import xml.etree.ElementTree as ET
import re
import yaml

magic_end = "]]>]]>"


def send_xml(chan, xml):
    buff = ""
    xml_prefix = """<?xml version="1.0" encoding="UTF-8"?>"""
    chan.send(xml_prefix + xml + magic_end)
    while buff.find(magic_end) == -1:
        buff += chan.recv(8192)
    response = buff[:buff.find(magic_end)]
    return response


def _type_cast(text):
    try:
        return int(text)
    except (ValueError, TypeError):
        return text


def dump_tree(data_node):
    output = {}
    for node in data_node.getchildren():
        m = re.search('{.+}(.+)', node.tag)
        tag_name = m.group(1)
        if node.getchildren():
            output[tag_name] = dump_tree(node)
        else:
            output[tag_name] = _type_cast(node.text)
    return output


def save_config(host, chan, parsed_yaml):
    response = send_xml(chan, """
     <rpc message-id="1"
          xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
       <get-config>
         <source>
           <running/>
         </source>
       </get-config>
     </rpc>
""")
    data_node = ET.fromstring(response).getchildren()[0]

    output = dump_tree(data_node)
    module_name = parsed_yaml['node_types'].keys()[0]
    parsed_yaml['node_types'][module_name]['properties']['default'] = output
    with open(host + '.yaml', 'w') as config:
        dump = yaml.dump(parsed_yaml, width=100, allow_unicode=True,
                         default_flow_style=False)
        config.write(dump)


def main(yaml_file, host, user, password, port):
    try:
        with open(yaml_file, 'r') as stream:
            parsed_yaml = yaml.load(stream)
    except (IOError, yaml.scanner.ScannerError):
        print "Can't parse input file: '{}'".format(yaml_file)
        sys.exit(-2)
    with paramiko.SSHClient() as ssh:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password,
                    port=port, look_for_keys=False)
        with ssh.get_transport().open_session() as chan:
            chan.invoke_subsystem('netconf')
            send_xml(chan, """
            <hello xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
            <capabilities>
            <capability>urn:ietf:params:netconf:base:1.0</capability>
            </capabilities>
            </hello>""")
            save_config(host, chan, parsed_yaml)


if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) < 4:
        print "Usage: python get_yang.py yaml_file host user password"
        sys.exit(-1)
    port = 830 if len(args) == 4 else int(args[4])
    main(args[0], args[1], args[2], args[3], port)
