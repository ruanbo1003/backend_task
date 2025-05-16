

## build docker image
```shell
docker build -t task_api:v1 -f docker/Dockerfile .
```

## start database
```shell
docker compose -f docker/docker-compose.yml up backend_task_mongo_local
```

## start api
```shell
docker compose -f docker/docker-compose.yml up backend_task_api_local
```

