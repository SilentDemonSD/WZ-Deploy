FROM mysterysd/wzmlx:v3

WORKDIR /usr/src/app

COPY . .

ENTRYPOINT ["bash", "start.sh"]
