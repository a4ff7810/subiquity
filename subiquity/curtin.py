# Copyright 2015 Canonical, Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import jinja2
import os
import datetime
import yaml

CURTIN_STORAGE_CONFIG_FILE = '/tmp/subiquity-config.yaml'
CURTIN_STORAGE_CONFIG_HEADER = """
reporter:
 subiquity:
  path: /tmp/curtin_progress_subiquity
  progress: True

partitioning_commands:
 builtin: curtin block-meta custom

storage:
  version: 1
  config:
"""
CURTIN_STORAGE_CONFIG_TEMPLATE = """
# Autogenerated by SUbiquity: {{DATE}} UTC
reporter:
 subiquity:
  path: /tmp/curtin_progress_subiquity
  progress: True

partitioning_commands:
 builtin: curtin block-meta custom

storage:
  version: 1
  config:
    - id: {{TARGET_DISK_NAME}}
      type: disk
      ptable: msdos
      model: {{TARGET_DISK_MODEL}}
      serial: {{TARGET_DISK_SERIAL}}
    - id: {{TARGET_DISK_NAME}}1
      type: partition
      offset: 512MB
      size: 8GB
      device: {{TARGET_DISK_NAME}}
      flag: boot
    - id: {{TARGET_DISK_NAME}}2
      type: partition
      offset: 8512MB
      size: 1GB
      device: {{TARGET_DISK_NAME}}
    - id: {{TARGET_DISK_NAME}}1_root
      type: format
      fstype: ext4
      volume: {{TARGET_DISK_NAME}}1
    - id: {{TARGET_DISK_NAME}}2_home
      type: format
      fstype: ext4
      volume: {{TARGET_DISK_NAME}}2
    - id: {{TARGET_DISK_NAME}}1_mount
      type: mount
      path: /
      device: {{TARGET_DISK_NAME}}1_root
    - id: {{TARGET_DISK_NAME}}2_mount
      type: mount
      path: /home
      device: {{TARGET_DISK_NAME}}2_home
"""

POST_INSTALL_CONFIG_FILE = '/tmp/subiquity-postinst.yaml'
# TODO, this should be moved to the in-target cloud-config seed so on first boot
# of the target, it reconfigures datasource_list to none for subsequent boots
#    12_ds_to_none: [curtin, in-target, --, sh, '-c', "echo 'datasource_list: [ None ]' > /etc/cloud/cloud.cfg.d/
POST_INSTALL = '''
late_commands:
    10_set_hostname: curtin in-target -- sh -c 'echo $(petname) > /etc/hostname'
    11_postinst_seed: [curtin, in-target, --, sh, '-c',"/bin/echo -e '#cloud-config\\npassword: passw0rd\\nchpasswd: { expire: False }\\n' > /var/lib/cloud/seed/nocloud-net/user-data"]
    12_disable_subiquity: curtin in-target -- systemctl disable subiquity.service
    13_delete_subiquity: curtin in-target -- rm -f /lib/systemd/system/subiquity.service
    14_remove_subiquity: curtin in-target -- sh -c 'for d in probert curtin subiquity; do rm -rf /usr/local/${d}; rm -rf /usr/local/bin/${d}*; done'
'''


def curtin_write_storage_actions(actions):
    curtin_config = yaml.dump(actions, default_flow_style=False)
    curtin_config = "    " + "\n    ".join(curtin_config.splitlines())
    datestr = '# Autogenerated by SUbiquity: {} UTC'.format(
        str(datetime.datetime.utcnow()))
    with open(CURTIN_STORAGE_CONFIG_FILE, 'w') as conf:
        conf.write(datestr)
        conf.write(CURTIN_STORAGE_CONFIG_HEADER)
        conf.write(curtin_config)
        conf.close()


def curtin_write_storage_template(disk_name, disk_model, disk_serial):
    ''' write out the storage yaml template for curtin
        params:
            disk_name: kernel name of disk (/dev/sda)
            disk_model: disk model name
            disk_serial:  serial of disk from probert storage  output
    '''
    template = jinja2.Template(CURTIN_STORAGE_CONFIG_TEMPLATE,
                               undefined=jinja2.StrictUndefined)

    ctxt = {
        'DATE': str(datetime.datetime.utcnow()),
        'TARGET_DISK_NAME': os.path.basename(disk_name),
        'TARGET_DISK_MODEL': disk_model,
        'TARGET_DISK_SERIAL': disk_serial,
    }
    curtin_config = template.render(ctxt)
    with open(CURTIN_STORAGE_CONFIG_FILE, 'w') as conf:
        conf.write(curtin_config)
        conf.close()

    return CURTIN_STORAGE_CONFIG_FILE


def curtin_write_postinst_config():
    with open(POST_INSTALL_CONFIG_FILE, 'w') as conf:
        datestr = '# Autogenerated by SUbiquity: {} UTC'.format(
            str(datetime.datetime.utcnow()))
        conf.write(datestr)
        conf.write(POST_INSTALL)
        conf.close()
