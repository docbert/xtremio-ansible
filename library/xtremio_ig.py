#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: xtremio_ig

short_description: Dell EMC XtremIO Initiator Group operations

description:
    - "Create or Delete an Initiator Group on an XtremIO Array"

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
            - Initiator Group name
        required: true
    state:
        description:
            - Desired state of the Initiator Group
        required: true
        choices: ["present", "absent"]

author:
    - Scott Howard (@docbert)
'''

EXAMPLES = '''
- name: Create an IG if it doesn't already exist
  xtremio_ig:
    xms: xms.example.com
    username: admin
    password: Xtrem10
    name: MyIG1
    state: present

- name: Delete an IG
  xtremio_ig:
    xms: xms.example.com
    username: admin
    password: Xtrem10
    name: MyIG1
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
        name=dict(type='str', required=True),
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
    state = module.params['state']

    try:
        xtremio = XtremIO(xms, username, password)
        ig = xtremio.get_ig(name)
    except Exception as e:
        module.fail_json(msg='error accessing xms - ' + str(e))

    changed=False

    if not ig:
        if state == 'present':
            if not module.check_mode:
                try:
                    xtremio.create_ig(name)
                except Exception as e:
                    module.fail_json(msg='error creating IG - ' + str(e))
            changed=True
    else:
        if state == 'absent':
            if ig['num-of-vols']>0:
                module.fail_json(msg='can''t delete IG with volume mappings');
            if not module.check_mode:
                try:
                    xtremio.remove_ig(name)
                except Exception as e:
                    module.fail_json(msg='error removing IG - ' + str(e))
            changed=True
    module.exit_json(changed=changed)


def main():
    run_module()

if __name__ == '__main__':
    main()
