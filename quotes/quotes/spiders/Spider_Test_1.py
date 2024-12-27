import scrapy

class QuotesSpider(scrapy.Spider):

    # name the spider
    name = "quotes"

    # specify the URLs to crawl
    start_urls= [
        'https://quotes.toscrape.com/page/5/',
        'https://quotes.toscrape.com/page/6/',
        'https://quotes.toscrape.com/page/7/',


    ]

    # define a parser
    def parse(self,response):
    
        # get the divs with the tag 'quote'
        quotes = response.css('div.quote')

        # iterate over each quote
        for quote in quotes:

            # extract the text and author of the quote
            yield{
                'text': quote.css('.text::text').get(),
                'author': quote.css('.author::text').get(),

            }