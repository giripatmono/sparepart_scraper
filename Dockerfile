FROM python:3.6.5-slim-stretch as build

WORKDIR /app
COPY requirements.txt /app/
COPY oracleinstantclient/* /tmp/

RUN apt-get update && apt-get install -y alien gcc libaio1 procps && \
    alien -iv /tmp/oracle-instantclient12.2-basiclite-12.2.0.1.0-1.x86_64.rpm && \
    alien -iv /tmp/oracle-instantclient12.2-devel-12.2.0.1.0-1.x86_64.rpm && \
    pip install -r requirements.txt && \
    apt-get purge -y gcc alien perl perl5 && apt-get -y autoremove && apt-get clean && \
    rm -rf /tmp/oracle-* && rm -rf /usr/share/docs && rm -rf /usr/share/man

FROM scratch
COPY --from=build / /

# Bundle app source
WORKDIR /app
RUN mkdir -p dbs logs sparepart templates data/crawljobs
COPY sparepart /app/sparepart/
COPY templates /app/templates/
COPY create_table.py queue_check.py crawler_queue.py entrypoint.sh scrapy.cfg scrapyd.conf start.py config.ini /app/

# Make ports available to the world outside this container
EXPOSE 6800
EXPOSE 9000

ENV ORACLE_HOME=/usr/lib/oracle/12.2/client64
ENV LD_LIBRARY_PATH=$ORACLE_HOME/lib
ENV PATH=$ORACLE_HOME/bin:$PATH

ENV LOG_LEVEL="WARNING"

# Run script when the container launches
CMD /app/entrypoint.sh
