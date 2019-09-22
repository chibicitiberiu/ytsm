# YouTube Subscription Manager

A self-hosted tool which manages your YouTube subscriptions, and downloads files automatically.

## Current state

Currently, the program will do what it's main job is to do: download videos, and keep track of the subscriptions.

Of course, there are a lot of things that still need to be done. The web interface is still pretty limited, and there might still be uncaught bugs. These are some of the things that need to be done:

* OAuth YouTube authentication, so private playlists can be obtained
* Web UI improvements:
    * Handle drag & drop for the subscription folders
    * Update UI when something changes
* Improve stability  
* Bonus: Plex integration
* Bonus: Support for additional services (Twitch, Vimeo)

## Dependencies

* python3: `$ apt install python3`
* pip: `$ apt install python3-pip`
* ffmpeg: `$ apt install ffmpeg`
* django: `$ pip3 install django`
* crispy_forms: `$ pip3 install django-crispy-forms`
* dj-config-url: `$ pip3 install dj-config-url`
* youtube-dl: `$ pip3 install youtube-dl`
* google-api-python-client: `$ pip3 install google-api-python-client`
* google_auth_oauthlib: `$ pip3 install google_auth_oauthlib`
* apscheduler (v3.5+): `$ pip3 install apscheduler`
* (recommended) oauth2client: `$ pip3 install oauth2client`

## Installation

There are 2 ways you can install this server. Using docker is the quickest and easiest method.

### Normal installation for development/testing

1. Clone this repository: 

    ```bash
    git clone https://github.com/chibicitiberiu/ytsm.git
    cd ytsm
    ```

2. Install all the dependencies listed above.

    ```bash
    sudo apt install python3 python3-pip ffmpeg
    sudo pip3 install --no-cache-dir -r requirements.txt
    ```

3. Modify `config/config.ini` to your liking. All the settings should be documented through comments.
All these settings apply server-wide. The settings in the `user` section can be overriden from the web page for each 
individual user. 

4. Obtain an YouTube API developer key from [https://console.developers.google.com/apis/dashboard](https://console.developers.google.com/apis/dashboard).
You can find a detailed guide on [this page](https://www.slickremix.com/docs/get-api-key-for-youtube/).

    The program already has a default API key, but if the quotas are reached, you won't be able to use this program 
    any more. Also, I might decide to delete that key, which will break your installation.
    
    You will be prompted for this key during the initial setup.

5. Set up the database:

    ```bash
    cd app
    python3 manage.py migrate
    ```
 
    By default, a SQLite database is used, which is located in the project's folder. The database can be configured
    in `settings.ini`.
         
6. Start the server: `python3 manage.py runserver [port] --noreload --insecure`

    The `port` parameter is optional.
    
    The `--noreload` option is necessary, otherwise the scheduler will run on 2 separate processes at the same time, 
    which is not ideal.
    
    The `--insecure` option is required only if `Debug=False` in `config.ini`, Without this option, the static resources 
    (CSS, javascript) won't work. 
     
7. Open the server's page in your browser, by entering `http://localhost:port` in your address bar.

8. Create an admin user by going to the *register* page, and creating an user account.

9. Add some subscriptions, and enjoy!

### Docker

1. Clone this repository: 

    ```bash
    git clone https://github.com/chibicitiberiu/ytsm.git
    cd ytsm
    ```

2. Install docker (if not installed)

3. Modify `config/config.ini` to your liking. All the settings should be documented through comments.
All these settings apply server-wide. The settings in the `user` section can be overriden from the web page for each 
individual user. 

    **Attention**: you cannot modify the download location from `settings.ini` when using docker. 
    To do so, you will need to modify the volume mapping in `docker-compose.yml`. 

4. Obtain an YouTube API developer key from [https://console.developers.google.com/apis/dashboard](https://console.developers.google.com/apis/dashboard).
You can find a detailed guide on [this page](https://www.slickremix.com/docs/get-api-key-for-youtube/).

    The program already has a default API key, but if the quotas are reached, you won't be able to use this program 
    any more. Also, I might decide to delete that key, which will break your installation.
    
    You will be prompted for this key during the initial setup.

5. Build and run docker compose image:

    ```bash
    docker-compose up -d
    ```
    
6. Open the server's page in your browser, by entering `http://localhost` in your address bar.

7. Create an admin user by going to the *register* page, and creating an user account.

8. Add some subscriptions, and enjoy!

The docker image uses a sqlite database, and stores the data in a folder `data/` located in the project directory. 
You can edit the default download locations in the `docker-compose.yml` file.

For more information about using Docker, check [this page](Docker_README.md).

### Deploying for production

This is a *django* project, so the correct way to deploy it to a server would be by using *mod_wsgi*. Since this project 
is still in development, I haven't really thought about getting it ready for production. 

If you are willing to try that, you can find the information on how to deploy this application on the 
[Django website](https://docs.djangoproject.com/en/2.1/howto/deployment/).
