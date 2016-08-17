import sys
import paramiko
import xml.etree.ElementTree as ET
import re

magic_end = "]]>]]>"


def send_xml(chan, xml):
    buff = ""
    xml_prefix = """<?xml version="1.0" encoding="UTF-8"?>"""
    chan.send(xml_prefix + xml + magic_end)
    while buff.find(magic_end) == -1:
        buff += chan.recv(8192)
    response = buff[:buff.find(magic_end)]
    return response


def save_schema(chan, text):
    print text
    m = re.search('.+module=(.+)&.+', text)
    if not m:
        return
    schema_name = m.group(1)
    if not schema_name:
        return
    response = send_xml(chan, """
    <rpc message-id="1" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
    <get-schema xmlns="urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring">
    <identifier>{}</identifier>
    </get-schema>
    </rpc> """.format(schema_name))
    schema = ET.fromstring(response).getchildren()[0].text
    print "Save: " + schema_name
    with open(schema_name + '.yang', 'w') as yang:
        yang.write(schema)


def main(host, user, password, port):
    ssh = paramiko.SSHClient()
    try:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password, port=port, look_for_keys=False)
        try:
            chan = ssh.get_transport().open_session()
            chan.invoke_subsystem('netconf')
            response = send_xml(chan, """
            <hello xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
            <capabilities>
            <capability>urn:ietf:params:netconf:base:1.0</capability>
            </capabilities>
            </hello>""")
            for c in ET.fromstring(response).getchildren()[0].getchildren():
                save_schema(chan, c.text)
        finally:
            chan.close()
    finally:
        ssh.close()


if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) < 3:
        print "Usage: python get_yang.py host user password"
        sys.exit(-1)
    port = 830 if len(args) == 3 else int(args[3])
    main(args[0], args[1], args[2], port)
