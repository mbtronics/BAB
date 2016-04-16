# BAB
BUDA::lab Administrative Backend

# Instalation

## getting the code
    $ git clone https://github.com/mbtronics/BAB.git <appdir>

## virtualenv
    $ cd <appdir>
    $ virtualenv venv
    $ source venv/bin/activate

## python dependencies
    $ pip install -r requirements.txt

## configuration
Copy env.example to .env and fill in the variables:

* **SECRET_KEY**: the flask secret key
* **MAIL_SERVER**: mailserver for sending mails
* **MAIL_PORT**: mailserver port (TLS enabled by default, see config.py)
* **MAIL_USERNAME**: username for mailserver
* **MAIL_PASSWORD**: password for mailserver
* **APP_NAME**: name for your application
* **APP_MAIL_SUBJECT_PREFIX**: prefix for email subjects (eg. [MyCoolApp])
* **APP_MAIL_SENDER**: the 'from' in emails (eg. App Admin \<app_admin@mycoolapp.blah\>)   
* **APP_ADMIN**: the administrator's email address
* **APP_URL_PREFIX**: default '/', no '/' at the end
* **DEV_DATABASE_URL**: development database url (eg. mysql://test:test@localhost/test)
* **DATABASE_URL**: production database url
* **FLASK_CONFIG**: the config to use (development, production)
* **UPLOAD_DIR**: the upload dir for files
* **MOLLIE_KEY**: Mollie payment system key

If you choose *development* for **FLASK_CONFIG**, you need to fill in **DEV_DATABASE_URL**.<br>
If you choose *production* for **FLASK_CONFIG**, you need to fill in **DATABASE_URL**.

It is best to create a seperate user with it's own database.

## deployment
    $ ./manage.py deploy

# Running

## manually
    $ ./manage.py runserver

## nginx & ubuntu service

### ubuntu service
*/etc/init/flaskapp.conf* (replace <appdir> and make changes where necessary)

    description "uWSGI server instance configured to serve flask app"
    
    start on runlevel [2345]
    stop on runlevel [!2345]
    
    setuid www-data
    setgid www-data
    
    chdir <appdir>
    exec uwsgi --ini uwsgi.ini --virtualenv <appdir>/venv

Start service:

    $ service flaskapp restart

### uwsgi gateway configuration
    location /APP_URL_PREFIX {
        include uwsgi_params;
        uwsgi_pass unix:/tmp/flask_app.sock;
    }
