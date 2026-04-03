"""Elasticsearch search service using AsyncElasticsearch (elasticsearch-py 8.x)."""
from __future__ import annotations

from elasticsearch import AsyncElasticsearch, NotFoundError

from app.config import settings
from app.models.schemas import (
    DriftEventSearchItem,
    DriftEventSearchResponse,
    ModelSearchItem,
    ModelSearchResponse,
    PredictionSearchItem,
    PredictionSearchResponse,
    StockSearchItem,
    StockSearchResponse,
)

_es_client: AsyncElasticsearch | None = None

INDEX_PREDICTIONS = "debezium.public.predictions"
INDEX_MODELS = "debezium.public.model_registry"
INDEX_DRIFT = "debezium.public.drift_logs"
INDEX_STOCKS = "stocks"


def get_es_client() -> AsyncElasticsearch:
    """Return singleton AsyncElasticsearch client, created on first call."""
    global _es_client
    if _es_client is None:
        _es_client = AsyncElasticsearch(
            hosts=[settings.ELASTICSEARCH_URL],
            connections_per_node=5,
            retry_on_timeout=True,
            max_retries=3,
        )
    return _es_client


async def close_es_client() -> None:
    """Close the AsyncElasticsearch client. Called during application shutdown."""
    global _es_client
    if _es_client is not None:
        await _es_client.close()
        _es_client = None


def _build_pagination(page: int, page_size: int) -> dict:
    """Convert 1-based page + page_size to ES from/size."""
    return {"from": (page - 1) * page_size, "size": page_size}


async def search_predictions(
    *,
    q: str | None = None,
    ticker: str | None = None,
    model_id: int | None = None,
    confidence_min: float | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> PredictionSearchResponse:
    """Search predictions index with optional free-text + structured filters."""
    client = get_es_client()
    must_clauses: list[dict] = []

    if q:
        must_clauses.append({"multi_match": {"query": q, "fields": ["ticker", "notes", "metadata"]}})
    if ticker:
        must_clauses.append({"term": {"ticker.keyword": ticker.upper()}})
    if model_id is not None:
        must_clauses.append({"term": {"model_id": model_id}})
    if confidence_min is not None:
        must_clauses.append({"range": {"confidence": {"gte": confidence_min}}})
    if date_from or date_to:
        date_range: dict = {}
        if date_from:
            date_range["gte"] = date_from
        if date_to:
            date_range["lte"] = date_to
        must_clauses.append({"range": {"prediction_date": date_range}})

    query = {"bool": {"must": must_clauses}} if must_clauses else {"match_all": {}}
    pagination = _build_pagination(page, page_size)

    try:
        resp = await client.search(index=INDEX_PREDICTIONS, query=query, **pagination)
    except NotFoundError:
        return PredictionSearchResponse(items=[], total=0, page=page, page_size=page_size)

    hits = resp["hits"]["hits"]
    total = resp["hits"]["total"]["value"]
    items = [PredictionSearchItem(**h["_source"]) for h in hits]
    return PredictionSearchResponse(items=items, total=total, page=page, page_size=page_size)


async def search_models(
    *,
    q: str | None = None,
    status: str | None = None,
    r2_min: float | None = None,
    rmse_max: float | None = None,
    mae_max: float | None = None,
    page: int = 1,
    page_size: int = 50,
) -> ModelSearchResponse:
    """Search model_registry index with optional metric threshold filters."""
    client = get_es_client()
    must_clauses: list[dict] = []

    if q:
        must_clauses.append({"multi_match": {"query": q, "fields": ["model_name", "version"]}})
    if status:
        must_clauses.append({"term": {"status.keyword": status}})
    if r2_min is not None:
        must_clauses.append({"range": {"r2_oos": {"gte": r2_min}}})
    if rmse_max is not None:
        must_clauses.append({"range": {"rmse_oos": {"lte": rmse_max}}})
    if mae_max is not None:
        must_clauses.append({"range": {"mae_oos": {"lte": mae_max}}})

    query = {"bool": {"must": must_clauses}} if must_clauses else {"match_all": {}}
    pagination = _build_pagination(page, page_size)

    try:
        resp = await client.search(index=INDEX_MODELS, query=query, **pagination)
    except NotFoundError:
        return ModelSearchResponse(items=[], total=0, page=page, page_size=page_size)

    hits = resp["hits"]["hits"]
    total = resp["hits"]["total"]["value"]
    items = [ModelSearchItem(**h["_source"]) for h in hits]
    return ModelSearchResponse(items=items, total=total, page=page, page_size=page_size)


async def search_drift_events(
    *,
    q: str | None = None,
    drift_type: str | None = None,
    severity: str | None = None,
    ticker: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> DriftEventSearchResponse:
    """Search drift_logs index with optional type/severity/ticker/date filters."""
    client = get_es_client()
    must_clauses: list[dict] = []

    if q:
        must_clauses.append({"multi_match": {"query": q, "fields": ["drift_type", "details"]}})
    if drift_type:
        must_clauses.append({"term": {"drift_type.keyword": drift_type}})
    if severity:
        must_clauses.append({"term": {"severity.keyword": severity}})
    if ticker:
        must_clauses.append({"term": {"ticker.keyword": ticker.upper()}})
    if date_from or date_to:
        date_range: dict = {}
        if date_from:
            date_range["gte"] = date_from
        if date_to:
            date_range["lte"] = date_to
        must_clauses.append({"range": {"timestamp": date_range}})

    query = {"bool": {"must": must_clauses}} if must_clauses else {"match_all": {}}
    pagination = _build_pagination(page, page_size)

    try:
        resp = await client.search(index=INDEX_DRIFT, query=query, **pagination)
    except NotFoundError:
        return DriftEventSearchResponse(items=[], total=0, page=page, page_size=page_size)

    hits = resp["hits"]["hits"]
    total = resp["hits"]["total"]["value"]
    items = [DriftEventSearchItem(**h["_source"]) for h in hits]
    return DriftEventSearchResponse(items=items, total=total, page=page, page_size=page_size)


async def search_stocks(
    *,
    q: str | None = None,
    sector: str | None = None,
    exchange: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> StockSearchResponse:
    """Full-text search on stocks index (company_name, sector, industry)."""
    client = get_es_client()
    must_clauses: list[dict] = []

    if q:
        must_clauses.append({
            "multi_match": {
                "query": q,
                "fields": ["company_name^2", "ticker^3", "sector", "industry"],
                "type": "best_fields",
            }
        })
    if sector:
        must_clauses.append({"term": {"sector.keyword": sector}})
    if exchange:
        must_clauses.append({"term": {"exchange.keyword": exchange.upper()}})

    query = {"bool": {"must": must_clauses}} if must_clauses else {"match_all": {}}
    pagination = _build_pagination(page, page_size)

    try:
        resp = await client.search(index=INDEX_STOCKS, query=query, **pagination)
    except NotFoundError:
        return StockSearchResponse(items=[], total=0, page=page, page_size=page_size)

    hits = resp["hits"]["hits"]
    total = resp["hits"]["total"]["value"]
    items = [StockSearchItem(**h["_source"]) for h in hits]
    return StockSearchResponse(items=items, total=total, page=page, page_size=page_size)
