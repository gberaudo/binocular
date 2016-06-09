FROM debian:jessie

#RUN echo "deb http://deb.nodesource.com/node_4.x jessie main" >> /etc/apt/sources.list
RUN apt-get update && apt-get install -y --no-install-recommends vim git-core openjdk-7-jre make apt-transport-https
RUN echo "deb http://deb.nodesource.com/node_4.x jessie main" >> /etc/apt/sources.list && \
  apt-key adv --recv-keys --keyserver keyserver.ubuntu.com 1655A0AB68576280 && \
  apt-get update && apt-get install -y --no-install-recommends nodejs

COPY build.sh ./

CMD bash
