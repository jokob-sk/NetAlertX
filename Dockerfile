FROM debian:bookworm-slim

# default UID and GID
ENV USER=pi USER_ID=1000 USER_GID=1000  PORT=20211 
#TZ=Europe/London

# Todo, figure out why using a workdir instead of full paths don't work
# Todo, do we still need all these packages? I can already see sudo which isn't needed

RUN apt-get update 
RUN apt-get install sudo -y 


# create pi user and group
# add root and www-data to pi group so they can r/w files and db
RUN groupadd --gid "${USER_GID}" "${USER}" && \
    useradd \
        --uid ${USER_ID} \
        --gid ${USER_GID} \
        --create-home \
        --shell /bin/bash \
        ${USER} && \
    usermod -a -G ${USER_GID} root && \
    usermod -a -G ${USER_GID} www-data

COPY --chmod=775 --chown=${USER_ID}:${USER_GID} . /home/pi/pialert/

# ENTRYPOINT ["tini", "--"]

CMD ["/home/pi/pialert/dockerfiles/start.sh"]

## command to build docker:  DOCKER_BUILDKIT=1  docker build . --iidfile dockerID
