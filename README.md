# mesos-sandbox-fetcher

This is a simple proxy service that allows to fetch small files (e.g. stdout, sterr) from the Mesos task sandbox.
The service must be able to reach the Mesos Master (default port 5050) and all the slave nodes (default port 5051). 

## Usage:

It exposes the following REST API:

`GET /fetch/{task_id}?filename={filename}`

### Response codes:

| Code     | Reason          |
| --------- | --------------- 
| 200 - OK  | Request was successful
| 400 - Bad Request      | The size of the requested file exceeds the maximum size of 1GB
| 404 - Not Found      | The requested file was not found
| 500 - Internal Server Error | Something went wrong inside the service. This should not happen usually. If it does happen, it means the server has experienced some serious problems.

### Request Parameters

| Name      | In      | Type   | Description
| --------- | --------|--------|------------
|  task_id  | path    | string |  ID of the task
|  filename (mandatory) | query | string | name of the file to be fetched from the sandbox 


## Usage with the INDIGO PaaS Orchestrator

### How to fetch files for a Marathon task deployed through the Orchestrator

In this case the `task_id` is the deployment `UUID`.

```
orchent depshow 11ebadab-8394-76fe-b870-02427cf8dc4c
Deployment [11ebadab-8394-76fe-b870-02427cf8dc4c]:
  status: CREATE_COMPLETE
  creation time: 2021-05-05T14:09+0000
  update time: 2021-05-05T14:10+0000
  outputs:
  {
      "endpoint": "https://mesoslb.example.it:10033",
      "username": "rstudio"
  }  
```

Fetch the stdout providing the deployment `UUID` as `task_id`:

```
curl https://mesos-sandbox-fetch.example.it/fetch/11ebadab-8394-76fe-b870-02427cf8dc4c?filename=stdout
```

Output:
```
[s6-init] making user provided files available at /var/run/s6/etc...exited 0.
[s6-init] ensuring user provided files have correct perms...exited 0.
[fix-attrs.d] applying ownership & permissions fixes...
[fix-attrs.d] done.
[cont-init.d] executing container initialization scripts...
[cont-init.d] userconf: executing...
[cont-init.d] userconf: exited 0.
[cont-init.d] done.
[services.d] starting services
[services.d] done.
```

### How to fetch files for a Chronos task deployed through the Orchestrator

In this case the `task_id` is the UUID of the deployment resource of type `tosca.nodes.indigo.Container.Application.Docker.Chronos` 

```
orchent resls 11ebadaf-17d1-cf14-b870-02427cf8dc4c
retrieving resource list:
  page: 0/1 [ #Elements: 2, size: 10 ]
  links:
    self [https://indigo-paas.cloud.ba.infn.it/orchestrator/deployments/11ebadaf-17d1-cf14-b870-02427cf8dc4c/resources?page=0&size=10&sort=createdAt,desc]
Resource [11ebadaf-1805-3b25-b870-02427cf8dc4c]:
  creation time: 2021-05-05T14:35+0000
  state: INITIAL
  toscaNodeType: tosca.nodes.indigo.Container.Runtime.Docker
  toscaNodeName: docker_runtime1
  requiredBy:
  links:
    deployment [https://indigo-paas.cloud.ba.infn.it/orchestrator/deployments/11ebadaf-17d1-cf14-b870-02427cf8dc4c]
    self [https://indigo-paas.cloud.ba.infn.it/orchestrator/deployments/11ebadaf-17d1-cf14-b870-02427cf8dc4c/resources/11ebadaf-1805-3b25-b870-02427cf8dc4c]

Resource [11ebadaf-1805-3b26-b870-02427cf8dc4c]:
  creation time: 2021-05-05T14:35+0000
  state: CONFIGURING
  toscaNodeType: tosca.nodes.indigo.Container.Application.Docker.Chronos
  toscaNodeName: chronos_job
  requiredBy:
  links:
    deployment [https://indigo-paas.cloud.ba.infn.it/orchestrator/deployments/11ebadaf-17d1-cf14-b870-02427cf8dc4c]
    self [https://indigo-paas.cloud.ba.infn.it/orchestrator/deployments/11ebadaf-17d1-cf14-b870-02427cf8dc4c/resources/11ebadaf-1805-3b26-b870-02427cf8dc4c]
```


Fetch the stdout providing the deployment `UUID` as `task_id`:

```
curl https://mesos-sandbox-fetch.example.it/fetch/11ebadaf-1805-3b26-b870-02427cf8dc4c?filename=stdout
```

Output:

````
Starting...
Wed May  5 14:35:52 UTC 2021
Job Done
````


## How to deploy the service with docker

Create the `config.json` file setting the following variables:

| Parameter name  | Description | Mandatory (Y/N) | Default Value 
| -------------- | ------------- |------------- |------------- |
| MESOS_URL | Url of the Mesos Master | Y | N/A
| MESOS_USERNAME | Mesos username to be used if basic http auth is enabled on Mesos | Y | N/A
| MESOS_PASSWORD | Mesos Password | Y | N/A
| LOG_LEVEL      | logging level  | N | info 

Then you can start the service using the docker image, for example, running the following command:

```
docker run -d -p 5001:5001 -v $PWD/config.json:/app/instance/config.json -d --name mesos-sandbox-fetch marica/mesos-sandbox-fetch:master
```

or using the following docker-compose file:

```
version: '3.3'

services:
   mesos-sandbox-fetcher:
     image: marica/mesos-sandbox-fetch:master
     container_name: mesos-sandbox-fetch
     ports:
       - "5001:5001"
     restart: always
     volumes:
       - $PWD/config.json:/app/instance/config.json
```
⚠️ Check the local path for the config.json file

Run the docker container:
```
docker run -d -p 443:5001 --name='mesos-sandbox-fetch' \
           -e ENABLE_HTTPS=True \
           -v $PWD/cert.pem:/certs/cert.pem \
           -v $PWD/key.pem:/certs/key.pem \
           -v $PWD/config.json:/app/app/config.json \
           marica/mesos-sandbox-fetch:master
```


### Using an HTTPS Proxy 

Example of configuration for nginx:
```
server {
      listen         80;
      server_name    YOUR_SERVER_NAME;
      return         301 https://$server_name$request_uri;
}

server {
  listen        443 ssl;
  server_name   YOUR_SERVER_NAME;
  access_log    /var/log/nginx/proxy-paas.access.log  combined;

  ssl on;
  ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
  ssl_certificate           /etc/nginx/cert.pem;
  ssl_certificate_key       /etc/nginx/key.pem;
  ssl_trusted_certificate   /etc/nginx/trusted_ca_cert.pem;

  location / {
                # Pass the request to Gunicorn
                proxy_pass http://127.0.0.1:5001/;

                proxy_set_header        X-Real-IP $remote_addr;
                proxy_set_header        X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header        X-Forwarded-Proto https;
                proxy_set_header        Host $http_host;
                proxy_redirect          http:// https://;
                proxy_buffering         off;
  }

}
```




