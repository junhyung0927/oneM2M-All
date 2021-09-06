FROM node:14.17.0

WORKDIR /usr/src/app
COPY . .

ADD entrypoint.sh /usr/src/app
RUN ["chmod", "+x", "/usr/src/app/entrypoint.sh"]

RUN npm i && apt-get update && apt-get install netcat-openbsd -y

ENTRYPOINT ["./entrypoint.sh"]
