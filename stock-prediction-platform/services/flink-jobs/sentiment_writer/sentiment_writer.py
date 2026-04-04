"""sentiment_writer — ARCHIVED (Phase 93)

This Flink job pushed Reddit sentiment features to Feast via
the reddit_sentiment PushSource. The PushSource and the
reddit_sentiment_fv FeatureView were removed from feature_repo.py
in Phase 93 (macro feature enrichment). Retaining this push job
would cause a Feast RegistryError at every execution.

The job is preserved here for reference only. Do not deploy.
"""


def push_batch_to_feast(records: list, store_path: str = "/opt/feast") -> None:
    """ARCHIVED — reddit_sentiment PushSource removed in Phase 93."""
    raise NotImplementedError(
        "sentiment_writer is archived. The reddit_sentiment PushSource no longer exists in Feast registry."
    )
