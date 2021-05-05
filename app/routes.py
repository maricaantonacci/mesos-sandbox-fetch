# Copyright (c) Istituto Nazionale di Fisica Nucleare (INFN). 2021
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from app import app
from flask import Response, request
from . import mesos

# master API /master/tasks --> list of tasks get task id, state, slave_id, framework_id

# master API /master/slaves?slave_id=2e948d20-a448-44d1-9efc-3b1d0c57f96a-S0 --> get hostname, port

# agent API /state --> .completed_frameworks['framework_id']['completed_executors'][id=task_id] get directory

# API /files/download
# query param: path=/<work_dir>/slaves/<slave_id>/frameworks/<framework_id>/executors/
# example http://172.30.15.214:5051/files/download?path=/var/lib/mesos/slaves/dc90f45b-c648-4de6-99aa-eca9c452c8af-S0/frameworks/dc90f45b-c648-4de6-99aa-eca9c452c8af-0000/executors/ct:1599051346111:0:zabbix-test-job:/runs/3188881e-500d-4484-b9c4-582c187d9dc8/stdout


@app.route('/fetch/<deployment_uuid>')
def fetch_file(deployment_uuid=None):

    filename = request.args.get('filename')

    if not filename:
        return Response('Missing filename query parameter', status=400)


    try:

        tasks = mesos.get_tasks(deployment_uuid)
        wdir = None

        if tasks:
            task = tasks[0]
            task_id = task['id']
            slave_id = task['slave_id']
            framework_id = task['framework_id']
            slave_ip, slave_port = mesos.get_slave(slave_id)

            wdir = mesos.get_task_wdir(slave_ip, slave_port, framework_id, task_id)

        if wdir:
            print('Task wdir: {}'.format(wdir))
            return mesos.get_file(slave_ip, slave_port, wdir, filename)

        else:
            return Response("Not found", status=404)

    except Exception as error:
        print("[ERROR] Retrieving {} for dep {}: {}".format(filename, deployment_uuid, error))
        return Response("Something went wrong: {}".format(error), status=500)


