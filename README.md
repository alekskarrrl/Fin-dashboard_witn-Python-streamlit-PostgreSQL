

<a name="readme-top"></a>
# Project Title

A brief description of what this project does and who it's for

![Tinkoff Invest](img/data_pipe.JPG "")


## Навигация
* [Инструменты](#инструменты)
* [Источники данных](#источники-данных)
* [Features](#features)
* [Дополнительно](#дополнительно)
* [ROADMAP](#roadmap)
* [DEMO](#demo)
* [Private settings](#private-settings)
* [Deployment](#deployment)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Инструменты

- UI: streamlit==1.20.0 
- Python 3.9
- PostgreSQL 14
- Apache Superset 
- Docker
- Apache Airflow (soon ...)


<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Источники данных

- Alpha Vantage API  - [документация](https://www.alphavantage.co/documentation/)  
    Квартальные и годовые отчеты по эмитентам
- Tinkoff Invest API  - [документация](https://tinkoff.github.io/investAPI/swagger-ui/#/)    
    рыночные цены, операции по счету
- сайт ЦБ РФ  - [документация](https://cbr.ru/development/SXML/)  
    валютные курсы по ЦБ РФ на дату
- отчеты других брокеров в формате csv


<div><p align="right">(<a href="#readme-top">back to top</a>)</p></div>

## Features

- ...
- ...


<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Дополнительно 
ERD диаграмма базы данных

![ERD](img/ERD_diagram.jpg "")


<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Roadmap

- [x] Add something ...
- [ ] Add something else ...
    - [ ] and more ...


<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Demo

Insert gif or link to demo

![Tinkoff Invest](img/screen_2.gif "Demonstration of the 'Tinkoff Invest' block")

![Fundamental Data](img/screen_3.gif "Demonstration of the 'Fundamental Data' block")

![Wallstreetbets](img/screen_1.gif "Demonstration of the 'Wallstreetbets' block")


<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Private settings

To run this project, you will need to add the following variables to your config.py file

Для подключения к базе данных:  
`DB_HOST` = ""  
`DB_USER` = ""  
`DB_PASS` = ""  
`DB_NAME` = ""  

Alpha Vantage API token:  
`AV_KEY` =  

Tinkoff Invest API token:  
`TCS_API_token`= ""  
`TCS_API_2_token` = ""  


<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Deployment

To deploy this project ...

*Редактируется...*

<p align="right">(<a href="#readme-top">back to top</a>)</p>