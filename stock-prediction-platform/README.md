# Stock Prediction Platform

Scalable stock prediction platform for the S&P 500 universe. Ingests real-time and historical market data, trains and evaluates regression models via automated ML pipelines, selects the best-performing model, detects drift, triggers retraining, and presents results through a React dashboard.

## Architecture

```
CronJob -> FastAPI (Ingestion) -> Kafka -> Batch Consumers -> PostgreSQL
                                                                |
                                                Kubeflow (Training Pipeline)
                                                                |
                                                Model Registry -> FastAPI (Serving)
                                                                |
                                                        React Frontend
```

## Tech Stack

- **Orchestration:** Kubernetes (Minikube), Kubeflow Pipelines
- **Backend:** FastAPI (Python)
- **Streaming:** Apache Kafka (Strimzi)
- **Storage:** PostgreSQL + TimescaleDB
- **ML:** scikit-learn, SHAP
- **Frontend:** React, Tailwind CSS
- **Data Source:** Yahoo Finance (yfinance)

## Project Structure

See `Project_scope.md` Section 15 for the complete folder tree.

## Getting Started

Setup instructions will be added as infrastructure phases are completed.
