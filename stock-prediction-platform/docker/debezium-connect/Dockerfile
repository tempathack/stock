FROM debezium/connect:2.7

# Install Confluent Elasticsearch Sink Connector 14.2.0
# Required: download the JAR into the Kafka Connect plugin path
USER root
RUN mkdir -p /kafka/connect/elasticsearch && \
    curl -L https://packages.confluent.io/maven/io/confluent/kafka-connect-elasticsearch/14.2.0/kafka-connect-elasticsearch-14.2.0.jar \
        -o /kafka/connect/elasticsearch/kafka-connect-elasticsearch-14.2.0.jar
USER kafka

# Build instructions (run from repo root):
# docker build -t debezium-connect-custom:latest -f docker/debezium-connect/Dockerfile .
# minikube image load debezium-connect-custom:latest
