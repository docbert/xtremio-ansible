#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: xtremio_volume

short_description: Dell EMC XtremIO Volume operations

description:
    - "Create, Remove or Modify volumes on an XtremIO Array"

options:
    xms:
        description:
            - Hostname/IP address of XMS
        required: true
    username:
        description:
            - XMS Username
        required: true
    password:
        description:
            - XMS Password
        required: true
    name:
        description:
            - Volume name
        required: true
    size:
        description:
            - Size of volume. Required for new volume, or to resize an existing volume. Must be a number followed by one of B/KB/MB/GB/TB
    state:
        description:
            - Desired state of the volume
        required: true
        choices: ["present", "absent"]

author:
    - Scott Howard (@docbert)
'''

EXAMPLES = '''
- name: Create a volume if it doesn't already exist
  xtremio_volume:
    xms: xms.example.com
    username: admin
    password: Xtrem10
    name: MyVol1
    size: 100GB
    state: present

- name: Resize existing volume
  xtremio_volume:
    xms: xms.example.com
    username: admin
    password: Xtrem10
    name: MyVol1
    size: 200GB
    state: present

- name: Delete volume if it exists
  xtremio_volume:
    xms: xms.example.com
    username: admin
    password: Xtrem10
    name: MyVol1
    state: absent

'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
from xtremio import XtremIO
from math import ceil
import re

sizeunits = {"b": 1.0/8, "k": 1, "m": 1024, "g": 1048576, "t": 1073741824}

def sizeToKB(size):
    s=re.search('(?i)^([\d.]+) ?([bkmgt])b? *$', size)
    if not s:
        return None
    size = float(s.group(1)) * sizeunits[str(s.group(2)).lower()]
    size = int(ceil(size / 8.0)) * 8
    return size


def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        xms=dict(type='str', required=True),
        username=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        name=dict(type='str', required=True),
        size=dict(type='str', required=False),
        state=dict(type='str', default='present', choices=['absent', 'present']),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    xms = module.params['xms']
    username = module.params['username']
    password = module.params['password']
    name = module.params['name']
    size = module.params['size']
    state = module.params['state']

    if size:
        size = sizeToKB(size)
        if not size:
            module.fail_json(msg='unable to parse volume size')

    try:
        xtremio = XtremIO(xms, username, password)
        vol = xtremio.get_volume(name)
    except Exception as e:
        module.fail_json(msg='error accessing xms - ' + str(e))

    if not vol:
        volsize=-1
    else:
        volsize = int(vol['vol-size'])

    changed=False

    if volsize<0:
        if state == 'present':
            if not size:
                module.fail_json(msg='volume size not supplied')
            if not module.check_mode:
                try:
                    xtremio.create_volume(name, size)
                except Exception as e:
                    module.fail_json(msg='error creating volume - ' + str(e))
            changed=True
    else:
        if state == 'absent':
            if not module.check_mode:
                try:
                    xtremio.remove_volume(name)
                except Exception as e:
                    module.fail_json(msg='error deleting volume - ' + str(e))
            changed=True
        elif state == 'present':
            if size:
                if volsize>size:
                    module.fail_json(msg='Shrinking volume not supported')
                elif volsize<size:
                    if not module.check_mode:
                        try:
                            xtremio.modify_volume(name, size=size)
                        except Exception as e:
                            module.fail_json(msg='error resizing volume - ' + str(e))
                    changed=True

    module.exit_json(changed=changed)


def main():
    run_module()

if __name__ == '__main__':
    main()
