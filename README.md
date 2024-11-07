# actor-RexScraper

Very simple Apify based product scraper for https://somosrex.com/

**Inputs to the actor**: 

- **Desired categories**: List of product categories that will be used to search for products. Keeping this list empty will search all categories. (not case-sensitive)
- **Include keywords**: Scrapper will search in all product fields for any of the keywords. If at least one match is found, product is included. Keeping this list empty will include all products. (not case-sensitive)
- **Exclude keywords**: Scrapper will search in all product fields for any of the keywords. If at least one match is found, product is excluded. Keeping this list empty will not do any exclusion.(not case-sensitive)

If product contains both one of the include keywords and one of the excluded keyword, then it is excluded.
(Simple order of evaluation: find product from desired category, include product if it contains any include keyword and does not contain any exclude keyword.)

**Source code**: https://github.com/Pijukatel/actor-RexScraper
Report any issues or improvements proposals on GitHub please.