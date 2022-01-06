import pandas_datareader as datar


def get_price(symbol, source='yahoo'):
    """ give a symobl -> get a price """

    price = datar.DataReader(symbol, source)
    price = price["Close"][price.last_valid_index()]
    return price
