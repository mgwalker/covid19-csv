FROM python:3.8

RUN mkdir /build
WORKDIR /build

RUN pip install pipenv

ADD Pipfile .
ADD Pipfile.lock .

RUN pipenv install

CMD ["pipenv", "run", "python", "build.py"]