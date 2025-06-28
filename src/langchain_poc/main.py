#!/usr/bin/env python3
import sys
from config import settings
from pipeline import pipeline


def main():
    if not settings.OPENAI_API_KEY:
        print("Error: встановіть OPENAI_API_KEY у ENV", file=sys.stderr)
        sys.exit(1)

    country = "Japan"
    print(f"Asking: What is the capital of {country}?")
    result = pipeline.invoke({"country": country})
    print("Answer:", result.content)


if __name__ == "__main__":
    main()