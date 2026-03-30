FROM flink:1.19

# Install Python 3.10 — Feast 0.61.0 requires Python 3.9+;
# flink:1.19 ships Python 3.8, so we install 3.10 explicitly.
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3.10-distutils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Bootstrap pip for Python 3.10 and set it as the default python3 and python
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1 && \
    ln -sf /usr/bin/python3.10 /usr/local/bin/python && \
    ln -sf /usr/bin/python3.10 /usr/local/bin/python3

# Use python3.10 -m pip explicitly to ensure packages install into Python 3.10
# (not the flink:1.19 base's Python 3.8 pip).
# setuptools provides pkg_resources required by apache-beam at runtime.
# Install apache-flink first, then feast to avoid joint resolver conflicts.
RUN python3.10 -m pip install "setuptools<75"
RUN python3.10 -m pip install "apache-flink==1.19.*"
RUN python3.10 -m pip install "feast[redis]==0.61.0" pandas

# Tell PyFlink to use Python 3.10 for all UDF workers
ENV PYFLINK_PYTHON=/usr/bin/python3.10

# Download Kafka connector JAR (only Kafka needed — no JDBC for Feast writer)
RUN wget -q -O /opt/flink/lib/flink-sql-connector-kafka-3.2.0-1.19.jar \
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.2.0-1.19/flink-sql-connector-kafka-3.2.0-1.19.jar

# Copy the Feast writer job to usrlib (visible to PyFlink driver)
COPY feast_writer.py /opt/flink/usrlib/feast_writer.py

# Feature store config is mounted at runtime via ConfigMap volume or init container.
# The expected path is /opt/feast/feature_store.yaml.
# Example K8s volume mount (in FlinkDeployment podTemplate):
#   volumeMounts:
#     - name: feast-feature-store-config
#       mountPath: /opt/feast
#   volumes:
#     - name: feast-feature-store-config
#       configMap:
#         name: feast-feature-store-config

USER flink
