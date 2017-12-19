# Project Name
Otsuka Insights

# Project description
CNS Insights Questions

## Installation

* `virtualenv -p python3 insight`
* `cd insight`
* `source bin/activate`
* `git clone git@bitbucket.org:DeepSine/bpi-insights-cms.git insight`
* `cd insight`
* `pip install -r requirements/development.txt`
* `./manage.py migrate`
* `./manage.py collectstatic`
* `./manage.py loaddata {path_to_the_dump_file}` - if you have it
* `./manage.py createsuperuser` - if you need to create new superuser
* `./manage.py runserver`

Open localhost:8000/admin/ , login and filout the questions if it needed

### Additional installation commands for production server
* `create empty config/settings/.env`
* `create config/settings/production_local.py` (with sample contents)
* `sudo chown :www static/CACHE`
* `sudo chmod g+w static/CACHE`

## Testing

* `pytest --cov`: Run pytest with coverage output
* `pytest --cov=. --cov-report=html` Run html coverage test
* `pytest --pep8 --pylint` : run tests with pep8 and pylint


## Update for dev
* Connect to the server by ssh
* `source /data/virtualenv/bpiinsights/bin/activate`
* `cd /data/www/bpiinsights/`
* `git pull`
* `./manage.py collectstatic` - if you have changed some of static files (css, javascript, images, etc)
* `./manage.py migrate` - if you have changed models
* `sudo /usr/local/etc/rc.d/uwsgi restart bpiinsights`
