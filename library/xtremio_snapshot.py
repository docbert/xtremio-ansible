#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: xtremio_snapshot

short_description: Dell EMC XtremIO Snapshot Operations

description:
    - "Take/Refresh/Delete snapshots on an XtremIO Array"

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
    sourcevol:
        description:
            - Source Volume when snapshotting/refreshing a single volume. Target must be a Volume ("targetvol")
    sourcecg:
        description:
            - Source Consistency Group when snapshotting/refreshing a CG. Target must be a Snapshot Set ("targetss")
    sourcess:
        description:
            - Source Snapshot Set when snapshotting/refreshing a SS. Target must be a Consistency Group ("targetcg") or a Snapshot Set ("targetss")
    targetvol:
        description:
            - Target Volume when snapshotting/refreshing a single volume
    targetcg:
        description:
            - Target Consistency Group when snapshotting/refreshing a CG
    targetss:
        description:
            - Target Snapshot Set when snapshotting/refreshing a CG/SS.
    suffix:
        description:
            - Suffix added to snapshot volume names when creating a snapshot from a CG or SS
    refresh:
        description:
            - If the snapshot already exists, whether it should be refreshed or not
        choices: ["True", "False"]
        default: False
    state:
        description:
            - Desired state of the snapshot
        required: true
        choices: ["present", "absent"]

author:
    - Scott Howard (@docbert)
'''

EXAMPLES = '''
- name: Create a snapshot of MyVol1. If is already exists, do NOT refresh it
  xtremio_snapshot:
    xms: xms.example.com
    username: admin
    password: Xtrem10
    sourcevol: MyVol1
    targetvol: MySnap1
    refresh: false
    state: present

- name: Refresh a snapshot of MyVol1, or create it if it already exists
  xtremio_snapshot:
    xms: xms.example.com
    username: admin
    password: Xtrem10
    sourcevol: MyVol1
    targetvol: MySnap1
    refresh: true
    state: present

- name: Create or refresh a snapshot of MyCG1 to a snapshots set MySnapSet1. New snapshots names are given the suffix MySnap1
  xtremio_snapshot:
    xms: xms.example.com
    username: admin
    password: Xtrem10
    sourcecg: MyCG1
    targetss: MySnapSet1
    suffix: MySnap1
    refresh: true
    state: present

- name: Delete a snapshot set, including snapshots in it
  xtremio_snapshot:
    xms: xms.example.com
    username: admin
    password: Xtrem10
    targetss: MySnapSet1
    state: absent

'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
from xtremio import XtremIO
from uuid import uuid4

def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        xms=dict(type='str', required=True),
        username=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        sourcevol=dict(type='str', required=False),
        sourcecg=dict(type='str', required=False),
        sourcess=dict(type='str', required=False),
        targetvol=dict(type='str', required=False),
        targetcg=dict(type='str', required=False),
        targetss=dict(type='str', required=False),
        suffix=dict(type='str', required=False),
        state=dict(type='str', default='present', choices=['absent', 'present']),
	refresh=dict(type='bool', default=False)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    xms = module.params['xms']
    username = module.params['username']
    password = module.params['password']
    sourcevol = module.params['sourcevol']
    sourcecg = module.params['sourcecg']
    sourcess = module.params['sourcess']
    targetvol = module.params['targetvol']
    targetcg = module.params['targetcg']
    targetss = module.params['targetss']
    suffix = module.params['suffix']
    state = module.params['state']
    refresh = module.params['refresh']

    if [targetvol, targetcg, targetss].count(None) != 2:
        module.fail_json(msg='exactly one of targetvol, targetss, targetcg is required')

    if [sourcevol, sourcecg, sourcess].count(None) < 2:
        module.fail_json(msg='no more than one of targetvol, targetss, targetcg can be set')


    if state == 'present':
        if targetvol and not sourcevol:
            module.fail_json(msg='sourcevol must be specified when targetvol is used')
        elif targetcg and not sourcess:
            module.fail_json(msg='sourcess must be specified when targetcg is used')
        elif targetss and not (sourcess or sourcecg):
            module.fail_json(msg='one of sourcecg or sourcess must be specified when targetss is used')

    try:
        xtremio = XtremIO(xms, username, password)
        if targetvol: snap = xtremio.get_volume(targetvol)
        if targetss: snap = xtremio.get_snapshot_set(targetss)
        if targetcg: snap = xtremio.get_cg(targetcg)
    except Exception as e:
        module.fail_json(msg='error accessing xms - ' + str(e))

    changed=False

    if not snap:
        if state == 'present':
            if not module.check_mode:
                tmpuuid = str(uuid4())
                try:
                    if sourcevol: xtremio.create_snapshot(vol=sourcevol, suffix=tmpuuid)
                    if sourcecg:  xtremio.create_snapshot(cg=sourcecg, ssname=targetss, suffix=suffix)
                    if sourcess:  xtremio.create_snapshot(ss=sourcess, ssname=targetss, suffix=suffix)
                except Exception as e:
                    module.fail_json(msg='error creating snapshots - ' + str(e))
                if sourcevol:
                    try:
                        xtremio.modify_volume(sourcevol + "." + tmpuuid, name=targetvol)
                    except Exception as e:
                        module.fail_json(msg='error renaming snapshots - ' + str(e))
            changed=True

    else:
        if state == 'absent':
            if targetcg:
                module.fail_json(msg='Consistency Groups can not be removed with this module')
            if not module.check_mode:
                try:
                    if targetvol: xtremio.remove_volume(targetvol)
                    if targetss:  xtremio.remove_snapshot_set(targetss)
                except Exception as e:
                    module.fail_json(msg='error removing snapshot - ' + str(e))
            changed=True
        elif state == 'present':
            if refresh:
                if not module.check_mode:
                    tmpuuid = str(uuid4())
                    try:
                        if sourcevol: xtremio.refresh_snapshot(fromvol=sourcevol, tovol=targetvol, nobackup=True)
                        if sourcecg:  xtremio.refresh_snapshot(fromcg=sourcecg, toss=targetss, ss=tmpuuid)
                        if sourcess:
                            if targetss: xtremio.refresh_snapshot(fromss=sourcess, toss=targetss, ss=tmpuuid)
                            if targetcg: xtremio.refresh_snapshot(fromss=sourcess, tocg=targetcg)
                        if targetss: xtremio.modify_snapshot_set(tmpuuid, name=targetss)
                    except Exception as e:
                        module.fail_json(msg='error refreshing snapshot from  - ' + str(e))
                changed=True

    module.exit_json(changed=changed)

def main():
    run_module()

if __name__ == '__main__':
    main()
