import argparse
from .main import crawl_repo  
def main() -> None:
    # Main entry point for the GitHub crawler script.
    parser = argparse.ArgumentParser(
        prog="python -m crawler_github",
        description="Crawl a public GitHub repository and extract metadata"
    )
    parser.add_argument(
        "url",
        help="Repository URL, e.g. https://github.com/Annaseanna/Redes-Neuronales"
    )
    parser.add_argument(
        "--out",
        default="output",
        metavar="DIR",
        help="Directory where Crawlee will write storage/ (default: %(default)s)"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=300,
        help="Maximum number of pages/requests to crawl (default: %(default)s)"
    )

    args = parser.parse_args()
    crawl_repo(args.url, max_pages=args.max_pages)   # out_dir

if __name__ == "__main__":
    main()
