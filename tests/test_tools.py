from agent.tools import get_news, get_stock_data, analyze_sentiment
from pandas import DataFrame

def test_get_news():
    result = get_news.invoke("AAPL")
    assert isinstance(result, list)
    assert isinstance(result[0], dict)
    assert len(result) == 10
    assert 'title' in result[0]


def test_stock_data():
    result = get_stock_data.invoke('AAPL')
    assert isinstance(result, dict)
    assert 'history' in result.keys()
    assert 'fundamentals' in result.keys()
    assert isinstance(result['history'], DataFrame)
    assert isinstance(result['fundamentals'], dict)
    assert 'marketCap' in result['fundamentals'].keys()


test_articles = ["UK gathers more than 40 countries to plot ways of reopening the Strait of Hormuz - AP News", 
                 "4.6 magnitude earthquake shakes California, centered in Santa Cruz Mountains - San Francisco Chronicle",
                 "Trump administration prepares up to 100% pharmaceutical tariffs on some imported drugs - CNBC"]

def test_analyze_sentiment():
    result = analyze_sentiment.invoke({"titles" : test_articles})
    assert isinstance(result, list)
    assert isinstance(result[0], dict)
    assert 'label' in result[0].keys()
