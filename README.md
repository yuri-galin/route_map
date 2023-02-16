Hello.

This is a django project that shows routes on the map of a chosen city.

It was done as a test task for a company I applied to, and it was required that I use Django, WebSocket (Channels), Postgis and Yandex.Maps API.

The DB schema was predetermined.

## REQUIREMENTS

In order for the project to work you must have installed:
- Python 3.11
- PostgreSQL 15.2
- Postgis 3.3.2
- OSGeo4W (GDAL)
- Redis
- Git


## SETUP

First, create a directory for the project and clone it there.
```
mkdir project; cd project
git clone git@github.com:yuri-galin/route_map.git .
```

Create a database and activate Postgis
```
  psql -U postgres
	CREATE USER admin WITH PASSWORD 'admin_pass';
	CREATE DATABASE route_map OWNER admin;
  \c route_map;
  CREATE EXTENSION postgis;
  \q
```

Then create a virtual environment and activate it.
```
python -m venv route_map_env
```

Windows:
```
route_map_env\Scripts\activate
```

Unix:
```
source route_map_env/bin/activate
```

Then install the dependencies:
```
pip install -r requirements.txt
```

Finally, make initial migration for the database, create a superuser and start the server.
```
cd route_map
python manage.py makemigrations map
python manage.py migrate	
python manage.py createsuperuser
python manage.py runserver
```

All done, you can find the project on http://localhost:8000/routes/map/
