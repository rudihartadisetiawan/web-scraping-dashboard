"""Quick test for the database connection."""

from dotenv import load_dotenv

from db import test_connection


def main() -> None:
    load_dotenv()
    ok = test_connection()
    if ok:
        print("SUCCESS: Database connection is working.")
    else:
        print("FAILURE: Could not connect to the database.")


if __name__ == "__main__":
    main()
