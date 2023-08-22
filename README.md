# Yatube
![Python](https://img.shields.io/badge/-Python-3776AB?style=flat&logo=python&logoColor=white) 
![Django](https://img.shields.io/badge/-Django-092E20?style=flat&logo=django&logoColor=white) 
![SQLite](https://img.shields.io/badge/-SQLite-003B57?style=flat&logo=sqlite&logoColor=white) 
![HTML](https://img.shields.io/badge/-HTML-E34F26?style=flat&logo=html5&logoColor=white) 
![CSS](https://img.shields.io/badge/-CSS-1572B6?style=flat&logo=css3&logoColor=white) 
![Bootstrap](https://img.shields.io/badge/-Bootstrap-7952B3?style=flat&logo=bootstrap&logoColor=white) 
![Unittest](https://img.shields.io/badge/-Unittest-0E8EE9?style=flat&logo=python&logoColor=white)
## Описание проекта
[Yatube](http://yaroslav8belyanski.pythonanywhere.com/) – социальная сеть для публикации личных дневников. 
Пользователи могут заходить на чужие страницы, подписываться на авторов и комментировать их записи.
## Запуск проекта в dev-режиме
- Клонировать репозиторий и перейти в него в командной строке:
```
git clone git@github.com:Belyanski/hw05_final.git
```
```
cd hw05_final/
```
- Cоздать и активировать виртуальное окружение
```
python -m venv venv # Для Windows
python3 -m venv venv # Для Linux и macOS
```
```
source venv/Scripts/activate # Для Windows
source venv/bin/activate # Для Linux и macOS
```
- Установите зависимости из файла requirements.txt
```
pip install -r requirements.txt
``` 
- Перейти в папку со скриптом управления и выполнить миграции
```
cd yatube/
```
- Выполните миграции
```
python manage.py migrate
```

- Запустить проект
```
python manage.py runserver
```
## Создание суперпользователя для доступа к панели администратора
- В директории с файлом manage.py выполнить команду
```
python manage.py createsuperuser
```
- Заполнить поля в терминале
```
Имя пользователя:
Адрес электронной почты:
Password: <ваш_пароль>
Password (again): <повторите_ваш_пароль>
```
- Перейдите по адресу http://127.0.0.1:8000/admin/ и авторизуйтесь

#### Автор работы
[Ярослав Белянский](https://github.com/Belyanski)
