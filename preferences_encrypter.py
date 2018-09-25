# -*- coding: utf-8 -*-

import os
import base64
import hashlib
import argparse

from lxml import etree
from Crypto.Cipher import AES


def generate_key(package_name):
    xor_map = b'fLxYB9M84AbeusERMY9YFzVG'
    output_key = []

    for index, value in enumerate(package_name):
        xor_map_result = xor_map[index % len(xor_map)]
        output_key.append(((value ^ xor_map_result) & 0x1f) + 48)

    output_key.reverse()
    return bytes(output_key)


class SecurePreferences:

    def __init__(self, key, mode):
        self.key = hashlib.sha256(key).digest()
        self.mode = mode
        self.IV = b'fldsjfodasjifudslfjdsaofshaufihadsf'
        if self.mode == AES.MODE_ECB:
            self.aes_stream = AES.new(self.key, self.mode)

    def encrypt(self, plain):
        # If it's CBC we have to re-create a stream for each values
        if self.mode == AES.MODE_CBC:
            self.aes_stream = AES.new(self.key, self.mode, self.IV[:AES.block_size])

        encrypted = self.aes_stream.encrypt(self.pkcs5_pad(plain.encode('utf-8')))
        return base64.b64encode(encrypted).decode('utf-8')

    def pkcs5_pad(self, plain):
        block_size = AES.block_size
        pad_size = block_size - len(plain) % block_size

        return plain + bytes([pad_size] * pad_size)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='''
        Command line tool that aim to encrypt supercell
        credentials files''')

    parser.add_argument('file', help='xml file to be encrypted', nargs=1)
    parser.add_argument('-a', '--android_id', help='android id that will be used as a key to encrypt the xml file')
    parser.add_argument('-p', '--package_name', help='package name that will be used to generate encrypt key')

    args = parser.parse_args()

    xml_file = args.file[0]

    if os.path.isfile(xml_file):
        if xml_file.endswith('.xml'):
            if args.android_id or args.package_name:
                if not (args.android_id and args.package_name):
                    if args.package_name:
                        key = generate_key(args.package_name.encode('utf-8'))

                    else:
                        key = args.android_id.encode('utf-8')

                    et = etree.parse(xml_file)

                    key_stream = SecurePreferences(key, AES.MODE_ECB)
                    value_stream = SecurePreferences(key, AES.MODE_CBC)

                    for line in et.getroot():
                        key = line.attrib['name']
                        value = line.text

                        line.set('name', key_stream.encrypt(key))
                        line.text = value_stream.encrypt(value)

                    output_name = '_encrypted'.join(os.path.splitext(os.path.basename(xml_file)))

                    with open(output_name, 'wb') as f:
                        f.write(etree.tostring(et, xml_declaration=True, encoding='utf-8', standalone='yes'))

                else:
                    print('[*] You shouldn\'t set both android id and package name !')

            else:
                print('[*] You should set an android id or a package name !')

        else:
            print('[*] Only xml files are supported !')

    else:
        print('[*] {} don\'t exists !'.format(xml_file))
