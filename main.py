import json
import sys
import re

import requests
from bs4 import BeautifulSoup

import config


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
    def __init__(self, args):
        self.host = 'https://www.glassdoor.com'
        self.url = self.host + '/Job/jobs.htm'
        self.payload = {
            'suggestCount': '0',
            'suggestChosen': 'false',
            'clickSource': 'searchBtn',
            'typedKeyword': 'Python+Developer',
            'sc.keyword': 'Python+Developer',
            'locT': 'N',
            'locId': '205'
        }
        self.headers = config.headers

    def get_urls(self):
        print('Запускаем парсинг URLs...')
        print(20 * '-')
        response = requests.get(
            self.url, headers=config.headers, params=self.payload
        )
        with open('index.html', 'w') as tempfile:
            tempfile.write(response.text)
        soup = BeautifulSoup(response.text, 'lxml')
        script = soup.find(
            'div', {'id': 'PageBodyContents'}
            ).find('script')
        urls = re.findall(
            r'[\'\"]seoJobLink[\'\"]\s*\:\s*[\'\"]([^\'\"]*)[\'\"]',
            script.string, flags=re.I
        )
        print(f'Парсинг {len(urls)} URL завершен...')
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

    def get_country_id(self, country):
        url = self.host + (f'/findPopularLocationAjax.htm?term={ country }'
                           '&maxLocationsToReturn=10')
        response = requests.get(url, headers=self.headers)
        countries = json.loads(response.content)
        print(countries)

    def get_vacancies(self):
        urls = self.get_urls()
        self.get_data(urls)


def main():
    parser = VacancyParser(
        **dict(arg.split('=') for arg in sys.argv[1:])
    )
    # parser.get_vacancies()
    parser.get_country_id('Moscow')


if __name__ == '__main__':
    main()
