FROM python:3.8

RUN mkdir /covid19-csv
WORKDIR /covid19-csv

RUN pip install pipenv

ADD Pipfile .
ADD Pipfile.lock .

RUN pipenv install

CMD ["pipenv", "run", "python"]