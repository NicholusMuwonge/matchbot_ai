from app.tests_pre_start import init


def test_init_successful_connection() -> None:
    """Test that init function can run without error when database is available."""
    from app.core.db import engine

    try:
        init(engine)
        connection_successful = True
    except Exception as database_error:
        print(f"Database connection failed: {database_error}")
        connection_successful = False

    assert (
        connection_successful
    ), "The database connection should be successful and not raise an exception."
