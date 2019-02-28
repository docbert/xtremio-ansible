#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: xtremio_initiator

short_description: Dell EMC XtremIO Initiator operations

description:
    - "Create, Remove or Modify an Initiator on an XtremIO Array"

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
            - Initiator name
        required: true
    ig:
        description:
            - Initiator Group the Initiator is in
        required: true
    os:
        description:
            - Operating system of the initiator. Required when state is present
        choices: ["linux", "esx", "windows", "solaris", "aix", "hpux", "other"]
    address:
        description:
            - WWN or IQN of the initiator. Required when state is present
    state:
        description:
            - Desired state of the volume
        required: true
        choices: ["present", "absent"]

author:
    - Scott Howard (@docbert)
'''

EXAMPLES = '''
- name: Add an initiator to the IG "MyIG1"
  xtremio_initiator:
    xms: xms.example.com
    username: admin
    password: Xtrem10
    name: MyInitiator1
    ig: MyIG1
    os: linux
    address: 80:80:80:80:80:80:80:80
    state: present

- name: Delete an initiator
  xtremio_initiator:
    xms: xms.example.com
    username: admin
    password: Xtrem10
    name: MyInitiator1
    state: absent

- name: Change WWN of an initiator
  xtremio_initiator:
    xms: xms.example.com
    username: admin
    password: Xtrem10
    name: MyInitiator1
    os: linux
    address: 90:90:90:90:90:90:90:90
    state: present

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
        ig=dict(type='str', required=True),
        os=dict(type='str', choices=['linux', 'esx', 'windows', 'solaris', 'aix', 'hpux', 'other']),
        address=dict(type='str'),
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
    ig = module.params['ig']
    os = module.params['os']
    address = module.params['address']
    state = module.params['state']

    if state == 'present':
        if not os:
            module.fail_json(msg='os is required when state is "present"')
        if not address:
            module.fail_json(msg='address is required when state is "present"')

    # Need to error-check the WWN format/etc

    try:
        xtremio = XtremIO(xms, username, password)
        initiator = xtremio.get_initiator(name)
    except Exception as e:
        module.fail_json(msg='error accessing xms - ' + str(e))

    if initiator:
        currentaddr = initiator['port-address']
        currentos = initiator['operating-system']
        currentig = initiator['ig-name']

    changed=False
    if not initiator:
        if state == 'present':
            if not module.check_mode:
                try:
                    xtremio.create_initiator(name, ig, address, os)
                except Exception as e:
                    module.fail_json(msg='error creating initiator - ' + str(e))
            changed=True
    else:
        if state == 'absent':
            if not module.check_mode:
                try:
                    xtremio.remove_initiator(name)
                except Exception as e:
                    module.fail_json(msg='error removing initiator - ' + str(e))
            changed=True
        elif state == 'present':
            if ig != currentig:
                module.fail_json(msg='Initiator exists and can not be moved between IGs')
            if not os == currentos:
                if not module.check_mode:
                    try:
                        xtremio.modify_initiator(name, os=os)
                    except Exception as e:
                        module.fail_json(msg='error modifying initiator OS - ' + str(e))
                changed=True

            if not address == currentaddr:
                if not module.check_mode:
                    try:
                        xtremio.modify_initiator(name, address=address)
                    except Exception as e:
                        module.fail_json(msg='error modifying initiator OS - ' + str(e))
                changed=True

    module.exit_json(changed=changed)



def main():
    run_module()

if __name__ == '__main__':
    main()
