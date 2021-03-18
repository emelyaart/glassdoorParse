import argparse
import json
import re
import time

import requests
from bs4 import BeautifulSoup

from config import headers


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


class VacanciesParser(object):
    def __init__(self, args):
        try:
            print('Инициализация объекта...')
            self.host = 'https://www.glassdoor.com'
            self.url = self.host + '/Job/jobs.htm'
            self.headers = headers
            if args.remote == 'yes':
                args.location = 'remote'
            location = self.get_location_id(args.location)
            keywords = ' + '.join(args.keywords)
            self.payload = {
                'suggestCount': '0',
                'suggestChosen': 'false',
                'clickSource': 'searchBtn',
                'typedKeyword': keywords,
                'sc.keyword': keywords,
                'locT': location[0]['locationType'],
                'locId': location[0]['realId'],
                'p': ''
            }
            select_location = location[0]['longName']
            select_keywords = keywords
            print(f'Location: { select_location }')
            print(f'Keywords: { select_keywords }')
            print('Инициализация объекта завершена...')
            print(20 * '-')
        except json.JSONDecodeError as e:
            print(e)
            print('Ошибка парсинга JSON в функции get_location.'
                  ' Умерли cookie :(')
            exit()
        except Exception as e:
            print(e)
            print('Протухли cookies, инициализация не удалась...')
            exit()

    def get_urls(self):
        print('Запускаем парсинг URLs...')
        response = requests.get(
            self.url, headers=self.headers, params=self.payload
        )
        soup = BeautifulSoup(response.text, 'lxml')
        pages = soup.find(
                    'div',
                    {'data-test': 'ResultsFooter'}
                ).find(class_='py-sm').text.split(' ')[-1]
        print(f'Обработка страницы 1 из { int(pages) }')
        script = soup.find(
                'div', {'id': 'PageBodyContents'}
                ).find('script')
        all_urls = re.findall(
            r'[\'\"]seoJobLink[\'\"]\s*\:\s*[\'\"]([^\'\"]*)[\'\"]',
            script.string, flags=re.I
        )
        if int(pages) > 1:
            for i in range(2, int(pages) + 1):
                print(f'Обработка страницы { i } из { int(pages) }')
                time.sleep(1)
                self.payload['p'] = str(i)
                response = requests.get(
                    self.url, headers=self.headers, params=self.payload
                )
                soup = BeautifulSoup(response.text, 'lxml')
                script = soup.find(
                    'div', {'id': 'PageBodyContents'}
                    ).find('script')
                urls = re.findall(
                    r'[\'\"]seoJobLink[\'\"]\s*\:\s*[\'\"]([^\'\"]*)[\'\"]',
                    script.string, flags=re.I
                )
                all_urls += urls
        print(f'Нашлось {len(all_urls)} URL(s). Задача завершена...')
        print(20 * '-')
        return all_urls

    def get_data(self, urls):
        print('Запускаю парсинг вакансий...')
        output = []
        count = 0
        for url in urls:
            try:
                time.sleep(1)
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
                print(f'Вакансия # {count} из {len(urls)} сохранена')
            except TypeError as e:
                print(e)
                print('Ошибка в парсинге вакансии, переходим к следующей')
                continue

        with open('output.txt', 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=4)
        print('Работа по сбору вакансий завершена...')

    def get_location_id(self, location):
        url = self.host + (f'/findPopularLocationAjax.htm?term={ location }'
                           '&maxLocationsToReturn=10')
        response = requests.get(url, headers=self.headers)
        countries = json.loads(response.content)
        return countries

    def get_vacancies(self):
        urls = self.get_urls()
        self.get_data(urls)


def main():
    parser = argparse.ArgumentParser(description='Glassdoor Parser')
    parser.add_argument('-l', dest='location', required=True,
                        help='Input location for search')
    parser.add_argument('-k', dest='keywords', default='', nargs='*',
                        help='Input keywords for search vacancies')
    parser.add_argument('-t', dest='job_type', default='',
                        choices=['fulltime', 'intership'],
                        help='Set "fulltime" or "intership"'
                             ' to choose the type of work')
    parser.add_argument('-r', dest='remote', default='', choices=['yes', ''],
                        help='Set "yes", if your need remote work')
    args = parser.parse_args()
    vacancies_parser = VacanciesParser(args)
    vacancies_parser.get_vacancies()


if __name__ == '__main__':
    main()
