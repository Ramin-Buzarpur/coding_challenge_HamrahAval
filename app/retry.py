from tenacity import retry, stop_after_attempt, wait_fixed


def retry_policy():
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1)
    )