import json
import os
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

        return urls

    def get_data(self, urls):
        output = []
        for url in urls:
            response = requests.get(
                url, headers=self.headers, params=self.payload
            )
            soup = BeautifulSoup(response.text, 'lxml')
            vacancy = Vacancy()
            vacancy.id = soup.find(class_='e1ulk49s0')['data-job-id']
            vacancy.source = url
            vacancy.city = soup.find(class_='e11nt52q2').text
            employer_name = soup.find(class_='e11nt52q1')
            span = employer_name.find('span')
            span.extract()
            vacancy.employer_name = employer_name.text
            vacancy.employer_link = (
                self.host + soup.find(class_='epu0oo21')['href']
            )
            vacancy.position = soup.find(class_='e11nt52q6').text
            output.append(vacancy)
        with open('output.txt', 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=4)

    def get_vacancies(self):
        urls = self.get_urls()
        self.get_data(urls)


def main():
    parser = VacancyParser(args=os.sys.argv)
    parser.get_vacancies()


if __name__ == '__main__':
    main()
