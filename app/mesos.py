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
from flask import Response
import requests

CHUNK_SIZE = 1024 #bytes
MAX_CONTENT_LENGTH = 2**30 #1GB

def get_tasks(task_name):

    response = requests.get(app.config.get('MESOS_URL') + '/master/state',
                            auth=(app.config.get('MESOS_USERNAME'), app.config.get('MESOS_PASSWORD')), verify=False)

    response.raise_for_status()

    mytasks = []
    if response.ok:
        frameworks = response.json()['frameworks']
        if frameworks:
            active_tasks = [f['tasks'] for f in frameworks if f['tasks']]
            completed_tasks = [f['completed_tasks'] for f in frameworks if f['completed_tasks']]
            mytasks = [t for elem in active_tasks + completed_tasks for t in elem if task_name in t['name']]


    return mytasks


def get_slave(id):
    response = requests.get(app.config.get('MESOS_URL') + '/master/slaves', params={"slave_id": id},
                            auth=(app.config.get('MESOS_USERNAME'), app.config.get('MESOS_PASSWORD')), verify=False)

    slave_ip = None
    slave_port = None

    if response.ok:
        slave = response.json()['slaves']
        if slave:
            slave_ip = slave[0]['hostname']
            slave_port = slave[0]['port']

    return slave_ip, slave_port


def get_task_wdir(slave_ip, slave_port, framework_id, task_id):

    wdir = None

    response = requests.get('http://{}:{}/state'.format(slave_ip,slave_port),
                            auth=(app.config.get('MESOS_USERNAME'), app.config.get('MESOS_PASSWORD')), verify=False)

    if response.ok:
        state = response.json()

        frameworks = state['frameworks'] + state['completed_frameworks']

        if frameworks:
            myframework = next(f for f in frameworks if f['id'] == framework_id)

            if myframework:
                executors = myframework['executors'] + myframework['completed_executors']
                mytask = next((e for e in executors if e['id'] == task_id), None)

                if mytask:
                    wdir = mytask['directory']

    return wdir


def get_file(slave_ip, slave_port, wdir, filename):

    r = requests.get('http://{}:{}/files/download'.format(slave_ip,slave_port), params={"path": "{}/{}".format(wdir,filename) },
                        auth=(app.config.get('MESOS_USERNAME'), app.config.get('MESOS_PASSWORD')), verify=False, stream=True)

    def generate():
        for chunk in r.iter_content(decode_unicode=False, chunk_size=CHUNK_SIZE):
            yield chunk


    if int(r.headers['Content-Length']) > MAX_CONTENT_LENGTH:

        return Response("The requested file exceeds the allowed maximum length (1 GB)", status=400)

    headers = dict(r.raw.headers)
    out = Response(generate(), headers=headers)
    out.status_code = r.status_code

    return out
