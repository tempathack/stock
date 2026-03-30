FROM flink:1.19

# Install Python 3 with dev tools and numpy/pandas build deps
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3 /usr/local/bin/python \
    && ln -sf /usr/bin/python3 /usr/local/bin/python3

# Install PyFlink + pandas + numpy for UDAF helper logic
RUN pip3 install "apache-flink==1.19.*" pandas numpy

# Download connector JARs into /opt/flink/lib/ so Flink classloader picks them up
# flink-sql-connector-kafka: bundles all Kafka connector dependencies
RUN wget -q -O /opt/flink/lib/flink-sql-connector-kafka-3.2.0-1.19.jar \
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.2.0-1.19/flink-sql-connector-kafka-3.2.0-1.19.jar

# flink-connector-jdbc: JDBC sink connector (not used by indicator-stream but
# kept for consistency with ohlcv-normalizer base image pattern)
RUN wget -q -O /opt/flink/lib/flink-connector-jdbc-3.2.0-1.19.jar \
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-jdbc/3.2.0-1.19/flink-connector-jdbc-3.2.0-1.19.jar

# PostgreSQL JDBC driver (kept for consistency with base image pattern)
RUN wget -q -O /opt/flink/lib/postgresql-42.7.3.jar \
    https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.3/postgresql-42.7.3.jar

# Copy pure Python UDAF logic helper and the Flink Table API job
COPY indicator_udaf_logic.py /opt/flink/usrlib/indicator_udaf_logic.py
COPY indicator_stream.py /opt/flink/usrlib/indicator_stream.py

USER flink
