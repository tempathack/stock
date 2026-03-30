FROM flink:1.19

# Install Python 3
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install PyFlink (no Feast — Job 1 does not use feature store)
RUN pip3 install "apache-flink==1.19.*"

# Download connector JARs into /opt/flink/lib/ so Flink classloader picks them up
# flink-sql-connector-kafka: bundles all Kafka connector dependencies
RUN wget -q -O /opt/flink/lib/flink-sql-connector-kafka-3.2.0-1.19.jar \
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.2.0-1.19/flink-sql-connector-kafka-3.2.0-1.19.jar

# flink-connector-jdbc: JDBC sink connector
RUN wget -q -O /opt/flink/lib/flink-connector-jdbc-3.2.0-1.19.jar \
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-jdbc/3.2.0-1.19/flink-connector-jdbc-3.2.0-1.19.jar

# PostgreSQL JDBC driver
RUN wget -q -O /opt/flink/lib/postgresql-42.7.3.jar \
    https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.3/postgresql-42.7.3.jar

# Copy job script and pure Python logic helper to usrlib (visible to PyFlink driver)
COPY normalizer_logic.py /opt/flink/usrlib/normalizer_logic.py
COPY ohlcv_normalizer.py /opt/flink/usrlib/ohlcv_normalizer.py

USER flink
