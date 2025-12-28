import pandas as pd
import matplotlib.pyplot as plt



def plot_candlestick_chart(stock_prices: pd.DataFrame) -> None:
    """
    example:
        # DataFrame to represent opening , closing, high 
        # and low prices of a stock for a week
        # stock_prices = pd.DataFrame({'open': [36, 56, 45, 29, 65, 66, 67],
        #                              'close': [29, 72, 11, 4, 23, 68, 45],
        #                              'high': [42, 73, 61, 62, 73, 56, 55],
        #                              'low': [22, 11, 10, 2, 13, 24, 25]},
        #                             index=pd.date_range(
        #                               "2021-11-10", periods=7, freq="d"))
    """
    plt.figure()

    up = stock_prices[stock_prices.close >= stock_prices.open]
    down = stock_prices[stock_prices.close < stock_prices.open]

    up_color = 'green'
    down_color = 'red'

    # Setting width of candlestick elements
    width = .3
    width2 = .03

    # Plotting up prices of the stock
    plt.bar(up.index, up.close-up.open, width, bottom=up.open, color=up_color)
    plt.bar(up.index, up.high-up.low, width2, bottom=up.low, color=up_color)

    # Plotting down prices of the stock
    plt.bar(down.index, down.close-down.open, width, bottom=down.open, color=down_color)
    plt.bar(down.index, down.high-down.low, width2, bottom=down.low, color=down_color)

    # rotating the x-axis tick labels at 30degree 
    # towards right
    plt.xticks(rotation=30, ha='right')

    # displaying candlestick chart of stock data 
    # of a week
    plt.show()
