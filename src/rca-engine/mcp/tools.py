def fetch_metrics():
    return {
        "db_connections": 95,
        "api_latency":    320,
        "cache_hit":      60,
    }


def fetch_logs():
    return [
        "DB connection pool nearing limit",
        "Timeout errors observed",
        "Service degradation detected",
    ]
