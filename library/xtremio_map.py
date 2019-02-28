#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: xtremio_map

short_description: Dell EMC XtremIO Map Volume operations

description:
    - "Map and Unmap a Volume on an XtremIO Array"

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
    ig:
        description:
            - Initiator Group for mapping operation
        required: true
    volume:
        description:
            - Volume (or snapshot) to Map/unmap
        required: true
    state:
        description:
            - Desired state of the mapping between volume and IG
        required: true
        choices: ["present", "absent"]

author:
    - Scott Howard (@docbert)
'''

EXAMPLES = '''
- name: Map a volume to an IG
  xtremio_map:
    xms: xms.example.com
    username: admin
    password: Xtrem10
    volume: MyVol1
    ig: MyIG1
    state: present

- name: Unmap a volume to an IG
  xtremio_map:
    xms: xms.example.com
    username: admin
    password: Xtrem10
    volume: MyVol1
    ig: MyIG1
    state: absent

'''

RETURN = '''
'''



from ansible.module_utils.basic import AnsibleModule
from xtremio import XtremIO

def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        xms=dict(type='str', required=True),
        username=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        ig=dict(type='str', required=True),
        volume=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['absent', 'present']),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    xms = module.params['xms']
    username = module.params['username']
    password = module.params['password']
    ig = module.params['ig']
    volume = module.params['volume']
    state = module.params['state']

    try:
        xtremio = XtremIO(xms, username, password)
        lunmap = xtremio.get_volume_mapping(volume, ig)
    except Exception as e:
        module.fail_json(msg='error accessing xms - ' + str(e))
        
    changed=False

    if lunmap:
        if state == 'absent':
            if not module.check_mode:
                try:
                    xtremio.remove_volume_mapping(volume, ig)
                except Exception as e:
                    module.fail_json(msg='error removing mapping - ' + str(e))
            changed=True
    else:
        if state == 'present':
            if not module.check_mode:
                try:
                    xtremio.create_volume_mapping(volume, ig)
                except Exception as e:
                    module.fail_json(msg='error adding mapping - ' + str(e))
            changed=True
    module.exit_json(changed=changed)

def main():
    run_module()

if __name__ == '__main__':
    main()
