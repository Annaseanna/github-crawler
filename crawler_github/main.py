import argparse
from .crawl_repo import crawl_repo   

def main() -> None:
    # Main entry point for the GitHub crawler script.
    parser = argparse.ArgumentParser(
        prog="python -m crawler_github",
        description="Run the GitHub crawler"
    )
    parser.add_argument("url", help="Repo URL, e.g. https://github.com/Annaseanna/Redes-Neuronales")
    parser.add_argument("--max-pages", type=int, default=300)
    args = parser.parse_args()

    crawl_repo(args.url, max_pages=args.max_pages)

if __name__ == "__main__":
    main()
