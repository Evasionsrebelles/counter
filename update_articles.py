import json
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone


SITEMAP_INDEX = "https://evasionsrebelles.com/sitemap_index.xml"

JSON_FILE = Path("articles.json")

HEADERS = {
    "User-Agent": "EvasionsRebelles-Counter/1.0"
}


def get_xml(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    return ET.fromstring(response.content)


def is_french_article(url):
    """
    Vérifie qu'une URL correspond à un article français.
    """

    url = url.lower()

    # Exclusion anglais
    if "/en/" in url:
        return False

    # Exclusion autres langues éventuelles
    language_prefixes = [
        "/es/",
        "/de/",
        "/it/",
        "/pt/",
        "/nl/",
        "/ja/",
        "/zh/"
    ]

    for prefix in language_prefixes:
        if prefix in url:
            return False

    # Exclusion contenus WordPress non-articles
    excluded = [
        "/category/",
        "/tag/",
        "/author/",
        "/page/",
        "/wp-content/",
        "/wp-json/"
    ]

    for item in excluded:
        if item in url:
            return False

    # Uniquement le domaine Evasions Rebelles
    if not url.startswith(
        "https://evasionsrebelles.com/"
    ):
        return False

    return True


def get_article_sitemaps():

    root = get_xml(SITEMAP_INDEX)

    namespace = {
        "sm": "http://www.sitemaps.org/schemas/sitemap/0.9"
    }

    sitemaps = []

    for sitemap in root.findall(
        "sm:sitemap",
        namespace
    ):

        loc = sitemap.find(
            "sm:loc",
            namespace
        )

        if loc is None:
            continue

        url = loc.text.strip().lower()

        # Sitemaps contenant les articles
        if (
            "post" in url
            or "article" in url
        ):

            # Exclusion autres contenus
            excluded = [
                "page",
                "category",
                "tag",
                "author",
                "attachment",
                "media"
            ]

            if not any(
                item in url
                for item in excluded
            ):

                sitemaps.append(
                    loc.text.strip()
                )

    return sitemaps


def get_french_articles():

    article_sitemaps = get_article_sitemaps()

    articles = set()

    print(
        f"{len(article_sitemaps)} sitemap(s) d'articles."
    )

    for sitemap in article_sitemaps:

        print(
            f"Analyse : {sitemap}"
        )

        try:

            root = get_xml(sitemap)

            namespace = {
                "sm":
                "http://www.sitemaps.org/schemas/sitemap/0.9"
            }

            for url_node in root.findall(
                "sm:url",
                namespace
            ):

                loc = url_node.find(
                    "sm:loc",
                    namespace
                )

                if loc is None:
                    continue

                url = loc.text.strip()

                if is_french_article(url):

                    articles.add(url)

        except Exception as error:

            print(
                f"Erreur : {error}"
            )

    return articles


def load_data():

    if not JSON_FILE.exists():

        return {
            "count": 1102,
            "updated": "2026-08-04"
        }

    with open(
        JSON_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def main():

    print(
        "=========================================="
    )

    print(
        "EVASIONS REBELLES - COMPTEUR ARTICLES FR"
    )

    print(
        "=========================================="
    )

    data = load_data()

    old_count = int(
        data.get("count", 1102)
    )

    print(
        f"Compteur actuel : {old_count}"
    )

    articles = get_french_articles()

    sitemap_count = len(articles)

    print(
        f"Articles FR dans les sitemaps : "
        f"{sitemap_count}"
    )

    # --------------------------------------------------
    # IMPORTANT
    # --------------------------------------------------
    #
    # On ne descend jamais en dessous de 1102.
    #
    # Cela protège le compteur de départ si le sitemap
    # est temporairement incomplet.
    #

    new_count = max(
        old_count,
        sitemap_count
    )

    added = new_count - old_count

    print(
        f"Nouveaux articles détectés : {added}"
    )

    print(
        f"Nouveau compteur : {new_count}"
    )

    now = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d")

    new_data = {
        "count": new_count,
        "updated": now
    }

    with open(
        JSON_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            new_data,
            file,
            indent=2,
            ensure_ascii=False
        )

    print(
        "articles.json mis à jour."
    )


if __name__ == "__main__":
    main()