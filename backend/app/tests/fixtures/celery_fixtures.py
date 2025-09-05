import pytest


@pytest.fixture(scope="session")
def celery_app():
    from celery import Celery

    app = Celery("test_app")

    app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
        broker_url="memory://",
        result_backend="cache+memory://",
        task_routes={"app.tasks.*": {"queue": "test_queue"}},
    )

    return app
