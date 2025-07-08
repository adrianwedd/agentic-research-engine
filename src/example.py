"""Example module containing simple greeting utilities."""


def hello(name: str) -> str:
    """Return a friendly greeting string.

    Args:
        name (str): Name to greet.

    Returns:
        str: Greeting message.
    """

    return f"Hello, {name}!"


if __name__ == "__main__":
    print(hello("World"))
