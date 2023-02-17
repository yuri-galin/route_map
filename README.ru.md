## ТРЕБОВАНИЯ

Для работы проекта требуется установка:
- Python 3.11
- PostgreSQL 15.2
- Postgis 3.3.2
- OSGeo4W (GDAL)
- Redis
- Git

## УСТАНОВКА

Создайте папку и склонируйте туда проект.
```
mkdir project; cd project
git clone git@github.com:yuri-galin/route_map.git .
```

Создайте базу данных и активируйте postgis:
```
psql -U postgres
CREATE USER admin WITH PASSWORD 'admin_pass';
CREATE DATABASE route_map OWNER admin;
\c route_map;
CREATE EXTENSION postgis;
\q
```

Затем создайте виртуальную среду и активируйте ее:
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

Установить зависимости проекта:
```
pip install -r requirements.txt
```

Сделайте начальные миграции для базы данных, создайте суперпользователя и запустите сервер.
```
cd route_map
python manage.py makemigrations map
python manage.py migrate	
python manage.py createsuperuser
python manage.py runserver
```
	
Готово, проект можно найти по ссылке http://localhost:8000/routes/map/

## ИНФОРМАЦИЯ О ПРОЕКТЕ

Поле point модели Station генерируется автоматически из ее полей "lat" и "lon". Это сделано через замену метода save на модели и через post_save сигнал.

Автоматическое обновление карты в режиме реального времени сделано через вебсокеты и джанговские сигналы. Сигналы запускаются на моделях при следующих условиях:

Route
- поле "is_active" изменилось
- активный маршрут был удален
	
Station
- поля "lat"/"lon"/"point" изменились

Stop
- новая активная остановка была создана на активном маршруте
- поля "index"/"is_active"/"route"/"station" изменились
- активная остановка на активном маршруте была удалена
	
Когда это случается, сигнал передает необходимую информацию на фронтенд через вебсокет, и карта обновляется во всех открытых вкладках у всех пользователей.
