#YouTube Subscription Manager

A self-hosted tool which manages your YouTube subscriptions, and downloads files automatically.

## Dependencies

* python3: `$ apt install python3`
* pip: `$ apt install python3-pip`
* django: `$ pip3 install django`
* crispy_forms: `$ pip3 install django-crispy-forms`
* youtube-dl: `$ pip3 install youtube-dl`
* google-api-python-client: `$ pip3 install google-api-python-client`
* google_auth_oauthlib: `$ pip3 install google_auth_oauthlib`
* apscheduler (v3.5+): `$ pip3 install apscheduler`
* (recommended) oauth2client: `$ pip3 install oauth2client`

## Installation

1. Install all the dependencies listed above.

    ```bash
    sudo apt install python3 python3-pip
    sudo pip3 install apscheduler django django-crispy-forms youtube-dl google-api-python-client google_auth_oauthlib oauth2client
    ```

2. Clone this repository: 

    ```bash
    git clone https://github.com/chibicitiberiu/ytsm.git
    cd ytsm
    ```

3. Set up the database: `python3 manage.py migrate`
 
    By default, a SQLite database is used, which is located in the project's folder.
    You can customize that in `YtManager/settings.py`, by modifying the `DATABASES` variable (search Django documentation for details).
     
4. Set up the `MEDIA_ROOT` variable in `YtManager/settings.py`. This is where the thumbnails will be downloaded. 
(note: this will be moved to `config.ini` in the future).

5. Obtain an YouTube API developer key from [https://console.developers.google.com/apis/dashboard](https://console.developers.google.com/apis/dashboard).
You can find a detailed guide on [this page](https://www.slickremix.com/docs/get-api-key-for-youtube/).

    The `defaults.ini` file already has an API key, but if the quotas are reached, you won't be able to use this program 
    any more. Also, I might decide to delete that key, which will break your installation.

6. Modify `config/config.ini` to your liking. All the settings should be documented through comments.
All these settings apply server-wide. The settings in the `user` section can be overriden from the web page for each 
individual user. 

    The most important settings are:

    * `[Global] YoutubeApiKey` - put your YouTube API key here    
    * `[User] DownloadPath` - sets the folder where videos will be downloaded

7. Start the server: `python3 manage.py runserver [port] --noreload`

    The `port` parameter is optional.
    
    The `--noreload` option is necessary, otherwise the scheduler will run on 2 separate processes at the same time, 
    which is not ideal. 
     
8. Open the server's page in your browser, by entering `http://localhost:port` in your address bar.

9. Create an admin user by going to the *register* page, and creating an user account.

10. Add some subscriptions, and enjoy!

### Correct deploying procedure

This is a *django* project, so the correct way to deploy it to a server would be by using *mod_wsgi*. Since this project 
is still in development, I haven't really thought about getting it ready for production. 

If you are willing to try that, you can find the information on how to deploy this application on the 
[Django website](https://docs.djangoproject.com/en/2.1/howto/deployment/).
