import pytest


@pytest.fixture(scope="session")
def redis_client():
    import fakeredis

    client = fakeredis.FakeRedis(decode_responses=True)
    yield client
    client.flushall()


@pytest.fixture(scope="session")
def redis_server():
    class MockRedisServer:
        host = "localhost"
        port = 6379

    return MockRedisServer()
