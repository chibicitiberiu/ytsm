Running with Docker
===

Sample Run command
-----
```bash
docker run -d --name ytsm -p 80:8000 --env-file sqlite3.env.env --volume ./downloads:/usr/src/app/data/downloads chibicitiberiu/ytsm:latest
```
### Quick Rundown:
- `--expose 80:8000` maps the Host OS port 80 to the container port 80
- `--env-file sqlite3.env.env` points to the env file with the desired variable settings (saves from typing them in the command line)
- `--volume ./downloads:/usr/src/app/data/downloads` maps the downloads folder of the current directory to the container folder `downloads` (where you could set the program to download to)
- `chibicitiberiu/ytsm:latest` tells Docker which image to run the container with (in this case, the latest version)

**Note:** Replace `./downloads` in the command to where you want the downloads folder to be mapped to on the Host OS. Ex: `/path/to/host/download/folder:/path/to/container/download/folder`


Environment variables
-----
- YTSM_DATABASE_ENGINE
- YTSM_DATABASE_NAME
- YTSM_YOUTUBE_API_KEY


Volumes
-----
- /usr/src/app/data/media
- /usr/src/app/data/db


Notes
----
If you experience any issues with the app running, make sure to run the following command to apply Django migrations to the database

### When using just the Dockerfile/Image
- `docker exec ytsm python manage.py migrate`

### When using the docker-compose file
- `docker exec ytsm_web_1 python manage.py migrate`
