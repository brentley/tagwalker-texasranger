FROM python:3-alpine

RUN pip install boto3 tenacity
RUN apk --update --no-cache add \
	bash

ADD *.py /usr/local/bin/
ADD *.sh /usr/local/bin/
RUN chmod -v +x /usr/local/bin/*

CMD ["/usr/local/bin/tagwalker-texasranger.sh"]
