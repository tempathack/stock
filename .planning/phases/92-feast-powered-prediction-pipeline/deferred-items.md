# Deferred Items — Phase 92

## Pre-existing Test Failures (Out of Scope)

These failures were present before plan 92-02 changes and are unrelated to the Feast integration work:

1. `ml/tests/test_training_pipeline.py::TestRunTrainingPipeline::test_pipeline_with_feature_store`
   - Failure: `AttributeError: ml.pipelines.components.feature_engineer does not have the attribute 'read_features'`
   - The test patches `feature_engineer.read_features` which does not exist as a module attribute
   - Pre-existing issue, not introduced by 92-02

2. `ml/tests/test_training_pipeline.py::TestRunTrainingPipeline::test_pipeline_feature_store_fallback`
   - Same root cause as above
   - Pre-existing issue, not introduced by 92-02

These should be fixed in a separate plan targeting the feature_engineer test suite.
