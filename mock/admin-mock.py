# -*- encoding: utf8 -*-
#
# The Qubes OS Project, http://www.qubes-os.org
#
# Copyright (C) 2017 Marek Marczykowski-Górecki
#                               <marmarek@invisiblethingslab.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program; if not, see <http://www.gnu.org/licenses/>.
import os
import sys
import yaml

data_path = '/etc/qubes/mock-qubes.yml'

class QubesMock(object):
    def __init__(self):
        self.data = self.load_yaml()

    def load_yaml(self):
        with open(data_path) as f:
            data = yaml.safe_load(f)
        return data

    def property_get(self, name, prop):
        try:
            if name == 'global':
                obj = self.data['global']
            else:
                obj = self.data['domains'][name]
        except KeyError:
            return None
        try:
            value = obj[prop]
            return 'default=False ' + value
        except KeyError:
            value = self.property_get('default', prop)
            return value.replace('default=False ', 'default=True ')

    def vm_list(self):
        response = ''
        for vm in self.data['domains'].keys():
            response += '{} class={} state=Halted\n'.format(
                vm, self.data[vm].get('class', 'AppVM'))
        return response

    def volumes(self, vm):
        return 'root\nprivate\nvolatile\n'

    def volume_info(self, vm, volume):
        return 'pool=test-pool\n' \
            'vid=some-id\n' \
            'size=1024\n' \
            'usage=512\n' \
            'rw=True\n' \
            'snap_on_start=True\n' \
            'save_on_stop=True\n' \
            'source=\n' \
            'revisions_to_keep=3\n'

    def label_list(self):
        return ''.join('{}\n'.format(label) for label in self.data['labels'])

    def label_index(self, label):
        return self.data['labels'][label]['index']

def main():
    mock = QubesMock()
    try:
        method = sys.argv[0]
        arg = sys.argv[1]
        # FIXME
        target = os.environ.get('QREXEC_REQUESTED_TARGET', 'testvm')
        if method == 'admin.property.Get':
            response = mock.property_get('global', arg)
        elif method == 'admin.vm.property.Get':
            response = mock.property_get(target, arg)
        elif method == 'admin.vm.volume.List':
            response = mock.volumes(target)
        elif method == 'admin.vm.volume.Info':
            response = mock.volume_info(target, arg)
        elif method == 'admin.label.List':
            response = mock.label_list()
        elif method == 'admin.label.Index':
            response = mock.label_index(arg)
        else:
            raise NotImplementedError('Method {} not supported'.format(method))
    except KeyError:
        sys.stdout.write('2\x00QubesException\x00\x00Value not set\x00')
    except NotImplementedError as err:
        sys.stdout.write('2\x00QubesException\x00\x00{}\x00'.format(err))

    sys.stderr.write('0\0' + str(response))

if __name__ == '__main__':
    main()
