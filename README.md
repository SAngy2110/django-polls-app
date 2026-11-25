#Create the Virtual Environment
python -m venv venv

pip install django django-debug-toolbar

#Install dependencies:
pip install django django-debug-toolbar

#Run database migrations:
python manage.py makemigrations
python manage.py migrate

#Create a superuser (for admin access):
python manage.py createsuperuser

#Run the development server:
python manage.py runserver



