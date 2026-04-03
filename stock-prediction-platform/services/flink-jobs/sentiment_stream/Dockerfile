FROM flink:1.19

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3 /usr/local/bin/python \
    && ln -sf /usr/bin/python3 /usr/local/bin/python3

RUN pip3 install "apache-flink==1.19.*" vaderSentiment==3.3.2 pandas

RUN wget -q -O /opt/flink/lib/flink-sql-connector-kafka-3.2.0-1.19.jar \
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.2.0-1.19/flink-sql-connector-kafka-3.2.0-1.19.jar

# JDBC connector for PostgreSQL sink
RUN wget -q -O /opt/flink/lib/flink-connector-jdbc-3.2.0-1.19.jar \
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-jdbc/3.2.0-1.19/flink-connector-jdbc-3.2.0-1.19.jar

# PostgreSQL JDBC driver
RUN wget -q -O /opt/flink/lib/postgresql-42.7.3.jar \
    https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.3/postgresql-42.7.3.jar

COPY sentiment_stream.py /opt/flink/usrlib/sentiment_stream.py

USER flink
