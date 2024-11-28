from __future__ import annotations

import asyncio

from crawlee import ConcurrencySettings
from crawlee.beautifulsoup_crawler import BeautifulSoupCrawler, BeautifulSoupCrawlingContext

from apify import Actor

ProductDetails = dict[str, str]


async def process_top_page(context: BeautifulSoupCrawlingContext, desired_categories: set[str]) -> None:
    """Enqueue links to category pages that are in desired categories."""
    for category_element in context.soup.findAll('a', 'level-top'):
        category_selector = '.' + '.'.join(category_element['class'])
        category = category_element.text
        if not desired_categories or category.lower() in desired_categories:
            await context.enqueue_links(
                selector=category_selector,
                label=f'CATEGORY-{category}',
            )


async def process_category_page(context: BeautifulSoupCrawlingContext, category: str) -> None:
    """Enqueue product links and pagination link to next page of products of this category."""
    await context.enqueue_links(
        selector='.action.next',
        label=f'CATEGORY-{category}',
    )
    await context.enqueue_links(
        selector='.product-item-link',
        label=f'PRODUCT-{category}',
    )


def get_product_details(context: BeautifulSoupCrawlingContext, category: str) -> ProductDetails:
    """Scrape details of specific product."""
    soup = context.soup
    details = {
        'name': soup.find('span', {'itemprop': 'name'}).text,
        'sku': soup.find('div', {'itemprop': 'sku'}).text,
        'category': category,
        'price': soup.find('div', 'product-info-price').find('span', 'price').text,
        'imageUrl': soup.select('.gallery-placeholder__image')[0]['src'].split('?')[0],
        'url': context.request.url,
        'description': soup.select('div.product.attribute.description > div.value')[0].text,
    }

    for detail_element in list(soup.select('.col.label')):
        detail_name = detail_element.text
        details[detail_name] = soup.find('td', {'data-th': detail_name}).text
    return details


def is_relevant(product_details: ProductDetails, include_keywords: set[str]) -> bool:
    """Return true if no include keywords are defined or if any of them match product details."""
    return not include_keywords or product_includes_keyword(product_details, include_keywords)


def product_includes_keyword(product_details: ProductDetails, keywords: set[str]) -> bool:
    """Return true if any of the product details is containing any of the keywords. Not case-sensitive."""
    for detail_text in product_details.values():
        for keyword in keywords:
            if keyword in detail_text.lower():
                return True
    return False


async def main() -> None:
    """Main entry point for RexScraper."""
    async with Actor:
        actor_input = await Actor.get_input() or {}
        desired_categories = {category.lower() for category in actor_input.get('desired_categories', [])}
        include_keywords = {word.lower() for word in actor_input.get('include_keywords', [])}
        exclude_keywords = {word.lower() for word in actor_input.get('exclude_keywords', [])}
        Actor.log.info(f'{desired_categories=}, {include_keywords=},{exclude_keywords=}')

        crawler = BeautifulSoupCrawler(_logger=Actor.log,
                                       proxy_configuration=await Actor.create_proxy_configuration(),
                                       concurrency_settings=ConcurrencySettings(desired_concurrency=10))

        @crawler.router.default_handler
        async def request_handler(context: BeautifulSoupCrawlingContext) -> None:
            match (context.request.label or '').split('-'):
                case ['PRODUCT', category_name]:
                    product_details = get_product_details(context, category_name)
                    if is_relevant(product_details, include_keywords) and not product_includes_keyword(
                        product_details,
                        exclude_keywords,
                    ):
                        await context.push_data(product_details)

                case ['CATEGORY', category_name]:
                    await process_category_page(context, category_name)
                case _:
                    await process_top_page(context, desired_categories)

        await crawler.run(['https://somosrex.com/'])


if __name__ == '__main__':
    asyncio.run(main())
