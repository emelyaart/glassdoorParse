import json
import sys
import re

import requests
from bs4 import BeautifulSoup


class Vacancy(object):
    def __init__(self):
        self.id = None
        self.source = None
        self.country = None
        self.city = None
        self.employer_name = None
        self.employer_link = None
        self.position = None
        self.salary = None

    def dict(self):
        return {
            'id': self.id,
            'source': self.source,
            'location': {
                'country': self.country,
                'city': self.city
            },
            'employer': {
                'name': self.employer_name,
                'link': self.employer_link
            },
            'position': self.position,
            'salary': self.salary
        }


class VacancyParser(object):
    def __init__(self, kwargs):
        print('Инициализация объекта...')
        try:
            self.host = 'https://www.glassdoor.com'
            self.url = self.host + '/Job/jobs.htm'
            self.headers = {
                'authority': 'www.glassdoor.com',
                'pragma': 'no-cache',
                'cache-control': 'no-cache',
                'sec-ch-ua': ('"Google Chrome";v="89", "Chromium";v="89", ";'
                              'Not A Brand";v="99"'),
                'sec-ch-ua-mobile': '?0',
                'upgrade-insecure-requests': '1',
                'user-agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X '
                               '10_15_7) AppleWebKit/537.36 (KHTML, '
                               'like Gecko) Chrome/'
                               '89.0.4389.82 Safari/537.36'),
                'accept': ('text/html,application/xhtml+xml,application/xml;'
                           'q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,'
                           'application/signed-exchange;v=b3;q=0.9'),
                'sec-fetch-site': 'same-origin',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'referer': 'https://www.glassdoor.com/',
                'accept-language': 'ru,en;q=0.9,en-US;q=0.8',
                'cookie': self.get_cookie()
            }
            location = self.get_location_id(kwargs['location'])[0]

            if kwargs.get('keywords', None) is not None:
                keywords = ' + '.join(kwargs['keywords'].split('+'))
            else:
                keywords = ''

            self.payload = {
                'suggestCount': '0',
                'suggestChosen': 'false',
                'clickSource': 'searchBtn',
                'typedKeyword': keywords,
                'sc.keyword': keywords,
                'locT': location['locationType'],
                'locId': location['realId']
            }
            print('Инициализация объекта завершена...')
            print(20 * '-')

        except Exception:
            print('Протухли cookies, инициализация не удалась...')
            exit()

    def get_urls(self):
        print('Запускаем парсинг URLs...')
        session = requests.Session()
        print(session.cookies.get_dict())
        response = session.get(
            self.url, headers=self.headers, params=self.payload
        )
        print(session.cookies.get_dict())
        exit()
        soup = BeautifulSoup(response.text, 'lxml')
        script = soup.find(
            'div', {'id': 'PageBodyContents'}
            ).find('script')
        urls = re.findall(
            r'[\'\"]seoJobLink[\'\"]\s*\:\s*[\'\"]([^\'\"]*)[\'\"]',
            script.string, flags=re.I
        )
        print(f'Нашлось {len(urls)} URL завершен...')
        print(20 * '-')
        return urls

    def get_data(self, urls):
        print('Запускаю парсинг вакансий...')
        output = []
        count = 0
        for url in urls:
            count += 1
            response = requests.get(
                url, headers=self.headers, params=self.payload
            )
            soup = BeautifulSoup(response.text, 'lxml')
            vacancy = Vacancy()
            vacancy.id = soup.find(class_='css-1m0gkmt')['data-job-id']
            vacancy.source = url
            vacancy.city = soup.find(class_='css-1v5elnn').text
            employer_name = soup.find(class_='css-16nw49e')
            span = employer_name.find('span')
            if span is not None:
                span.decompose()
            vacancy.employer_name = employer_name.text
            link = soup.find(class_='css-1sltc87')
            if link is not None:
                vacancy.employer_link = (
                    self.host + link['href']
                )
            vacancy.position = soup.find(class_='css-17x2pwl').text
            output.append(vacancy.dict())
            print(f'Вакансия #{count} из {len(urls)} сохранена')
        with open('output.txt', 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=4)

    def get_location_id(self, location):
        url = self.host + (f'/findPopularLocationAjax.htm?term={ location }'
                           '&maxLocationsToReturn=10')
        response = requests.get(url, headers=self.headers)
        countries = json.loads(response.content)
        return countries

    def get_cookie(self):
        with open('cookie.txt', 'rb') as cookie:
            return cookie.read()

    def get_vacancies(self):
        urls = self.get_urls()
        self.get_data(urls)


def main():
    kwargs = dict(arg.split('=') for arg in sys.argv[1:])
    if 'help' in kwargs:
        print(20 * '-')
        print('"location" - страна или город.'
              ' Например: "location=Russia"')
        print('"keywords" - Ключевые слова запроса, несколько слов'
              ' разделите знаком "+". Например: "keywords=Python+Junior"')
        print('"location=remote" - для поиска удаленной работы укажите '
              'Remote в поле location')
        print(20 * '-')
    elif 'location' in kwargs:
        parser = VacancyParser(kwargs)
        parser.get_vacancies()
    else:
        print(20 * '-')
        print('Укажите как минимум параметр location, '
              'например: "location=Russia"')
        print('Для вызова списка всех методов отправьте параметр "help="')
        print(20 * '-')


if __name__ == '__main__':
    main()
