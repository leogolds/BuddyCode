FROM nginx:alpine

RUN mkdir /etc/nginx/templates
COPY ./editor/default.conf.template /etc/nginx/templates

COPY ./editor/index.html /usr/share/nginx/html