#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: xtremio_cg

short_description: Dell EMC XtremIO Consistency Group operations

description:
    - "Create, Remove or Modify Consistency Groups on an XtremIO Array"

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
            - Consistency Group name
        required: true
    volumes:
        description:
            - List of volumes in Consistengy Group. Used when createing a new CG, or to modify the volumes in the CG
    state:
        description:
            - Desired state of the Consistency Group
        required: true
        choices: ["present", "absent"]

author:
    - Scott Howard (@docbert)
'''

EXAMPLES = '''
- name: Create a Consistency group that doesn't already exist
  xtremio_cg:
    xms: xms.example.com
    username: admin
    password: Xtrem10
    name: MyCG1
    volumes:
      - MyVol1
      - MyVol2
      - MyVol3
    state: present

- name: Delete a Consistency group
  xtremio_cg:
    xms: xms.example.com
    username: admin
    password: Xtrem10
    name: MyCG1
    state: absent

- name: Change volumes in a Consistency group (remove MyVol2/3, Add MyVol4/5)
  xtremio_cg:
    xms: xms.example.com
    username: admin
    password: Xtrem10
    name: MyCG1
    volumes:
      - MyVol1
      - MyVol4
      - MyVol5
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
        volumes=dict(type='list'),
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
    volumes = module.params['volumes']
    state = module.params['state']

    try:
        xtremio = XtremIO(xms, username, password)
        cg = xtremio.get_cg(name)
    except Exception as e:
        module.fail_json(msg='error accessing xms - ' + str(e))

    changed=False

    if not cg:
        if state == 'present':
            if not module.check_mode:
                try:
                    xtremio.create_cg(name, volumes)
                except Exception as e:
                    module.fail_json(msg='error creating CG - ' + str(e))
            changed=True
    else:
        if state == 'absent':
            if not module.check_mode:
                try:
                    xtremio.remove_cg(name)
                except Exception as e:
                    module.fail_json(msg='error removing CG - ' + str(e))
            changed=True
        elif state == 'present':
            currentvol = []
            for vol in (cg['vol-list']):
                currentvol.append(vol[1])

            addvol=list(set(volumes)-set(currentvol))
            delvol=list(set(currentvol)-set(volumes))

            for vol in addvol:
                if not module.check_mode:
                    try:
                        xtremio.modify_cg(name, add=vol)
                    except Exception as e:
                        module.fail_json(msg='error adding volume ' + vol + ' to CG - ' + str(e))
                changed=True

            for vol in delvol:
                if not module.check_mode:
                    try:
                        xtremio.modify_cg(name, remove=vol)
                    except Exception as e:
                        module.fail_json(msg='error removing volume ' + vol + ' from CG - ' + str(e))
                changed=True

    module.exit_json(changed=changed)


def main():
    run_module()

if __name__ == '__main__':
    main()
