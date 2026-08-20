# fetch_stocks.py
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
import time
import os

def fetch_stock_data():
    stock_codes = [
        '2800', '2800','2800','2800', '0001', '0001', '0019', '0019', '0087', '0087', '0087', '0087','0087','0026', '0012',
        '0017', '0083', '0251', '0823','0700','2633', '9988', '9618','9618', '0002', '0002', '0002', '0002',
        '0006', '0006', '0006', '0003', '0836','0916', '1816','1088','0883','0005', '0005', '0011', '0023', '0023', '0023', '2888',
        '3988', '3988', '3988', '6818', '6818','0066', '0066', '0066', '0066','0066', '0026',
        '0293', '0941', '0941', '0941','0728', '0008', '0046', '0374', '0345', '0052',
        '0341', '6811', '0883', '1919', '1109', '0857', '1898', '1211', '0819',
        '6960', '3931', '0476', '3677', '3750', '0951', '0729','1810','0366','0422','0855','0855','0371','0371','0045','0053','0992','2318','1177','0867','3692','1093','0950','3320'
    ]
    
    tickers = [f"{code.zfill(4)}.HK" for code in stock_codes]
    unique_tickers = list(set(tickers))

    ticker_to_price = {}
    ticker_to_assets = {}
    ticker_to_liab = {}
    ticker_to_equity = {}
    ticker_to_cash = {}
    ticker_to_shares = {}
    ticker_to_net_profit = {}
    ticker_to_tax = {}
    ticker_to_dividend_yield = {}
    ticker_to_dividend_rate = {}
    ticker_to_payout_ratio = {}
    ticker_to_dividend_amount = {}

    print("Fetching data from Yahoo Finance...")
    for ticker in unique_tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            price = (info.get('currentPrice') or
                     info.get('regularMarketPrice') or
                     info.get('regularMarketPreviousClose'))
            ticker_to_price[ticker] = round(price, 2) if price else None

            total_assets = total_liab = total_equity = cash_and_equiv = None
            bs = stock.balance_sheet
            if not bs.empty:
                latest = bs.columns[0]
                for idx in bs.index:
                    k = str(idx).lower()
                    if any(x in k for x in ['total assets', 'total asset']):
                        total_assets = bs.loc[idx, latest]
                    if any(x in k for x in ['total liabilities', 'total liab', 'total liabilities net minority interest']):
                        total_liab = bs.loc[idx, latest]
                    if any(x in k for x in ['total equity', 'total equity gross minority interest',
                                            'stockholders equity', 'shareholders equity',
                                            'total shareholders equity']):
                        total_equity = bs.loc[idx, latest]
                    if cash_and_equiv is None and any(x in k for x in ['cash and cash equivalents', 'cash equivalents',
                                                                       'cash and due from banks', 'bank balances',
                                                                       'cash', 'short term investments']):
                        cash_and_equiv = bs.loc[idx, latest]

            if total_assets is None:
                total_assets = info.get('totalAssets')
            if cash_and_equiv is None:
                cash_and_equiv = info.get('totalCash') or info.get('cashAndCashEquivalents')
            if total_equity is None and total_assets is not None and total_liab is not None:
                total_equity = total_assets - total_liab

            ticker_to_assets[ticker] = total_assets
            ticker_to_liab[ticker] = total_liab
            ticker_to_equity[ticker] = total_equity
            ticker_to_cash[ticker] = cash_and_equiv

            shares = info.get('sharesOutstanding') or info.get('impliedSharesOutstanding') or info.get('floatShares')
            ticker_to_shares[ticker] = shares

            net_profit = tax = None
            is_stmt = stock.income_stmt if not stock.income_stmt.empty else stock.financials
            if not is_stmt.empty:
                latest = is_stmt.columns[0]
                for idx in is_stmt.index:
                    k = str(idx).lower()
                    if net_profit is None and any(x in k for x in ['net income', 'net profit', 'profit for the year', 'profit attributable']):
                        net_profit = is_stmt.loc[idx, latest]
                    if tax is None and any(x in k for x in ['income tax expense', 'tax provision', 'tax expense', 'taxation', 'income tax']):
                        tax = is_stmt.loc[idx, latest]

            ticker_to_net_profit[ticker] = net_profit
            ticker_to_tax[ticker] = tax

            dividend_yield = info.get('dividendYield')
            if dividend_yield is not None:
                dividend_yield *= 100
            ticker_to_dividend_yield[ticker] = round(dividend_yield, 2) if dividend_yield else None

            dividend_rate = info.get('dividendRate') or info.get('trailingAnnualDividendRate') or info.get('lastDividendValue')
            ticker_to_dividend_rate[ticker] = round(dividend_rate, 2) if dividend_rate else None

            total_dividend_amount = None
            if dividend_rate is not None and shares is not None:
                total_dividend_amount = dividend_rate * shares
                ticker_to_dividend_amount[ticker] = round(total_dividend_amount, 0)

            payout_ratio = info.get('payoutRatio')
            if payout_ratio is not None:
                payout_ratio *= 100
            if payout_ratio is None and net_profit and total_dividend_amount and net_profit > 0:
                payout_ratio = (total_dividend_amount / net_profit) * 100
            ticker_to_payout_ratio[ticker] = round(payout_ratio, 2) if payout_ratio else None

            time.sleep(0.4)

        except Exception as e:
            print(f"⚠️ Error {ticker}: {e}")
            for d in [ticker_to_price, ticker_to_assets, ticker_to_liab, ticker_to_equity, ticker_to_cash,
                      ticker_to_shares, ticker_to_net_profit, ticker_to_tax, ticker_to_dividend_yield,
                      ticker_to_dividend_rate, ticker_to_payout_ratio, ticker_to_dividend_amount]:
                d[ticker] = None
            time.sleep(0.4)

    # Build DataFrame
    df = pd.DataFrame({
        'Stock Number': stock_codes,
        'Stock Price (HKD)': [ticker_to_price.get(t) for t in tickers],
        'Total Assets': [ticker_to_assets.get(t) for t in tickers],
        'Total Liabilities': [ticker_to_liab.get(t) for t in tickers],
        'Total Equity': [ticker_to_equity.get(t) for t in tickers],
        'Bank and Cash': [ticker_to_cash.get(t) for t in tickers],
        'Shares Outstanding': [ticker_to_shares.get(t) for t in tickers],
        'Net Profit': [ticker_to_net_profit.get(t) for t in tickers],
        'Tax': [ticker_to_tax.get(t) for t in tickers],
        'Dividend Payout Amount': [ticker_to_dividend_amount.get(t) for t in tickers],
        'Dividend Yield (%)': [ticker_to_dividend_yield.get(t) for t in tickers],
        'Dividend Rate (HKD)': [ticker_to_dividend_rate.get(t) for t in tickers],
        'Dividend Payout Ratio (%)': [ticker_to_payout_ratio.get(t) for t in tickers]
    })

    df['Assets - Liabilities'] = df['Total Assets'] - df['Total Liabilities']
    df['ROA'] = (df['Net Profit'] / df['Total Assets'] * 100).round(2)
    df['ROE'] = (df['Net Profit'] / df['Total Equity'] * 100).round(2)
    df['Debt to Equity'] = (df['Total Liabilities'] / df['Total Equity']).round(2)
    df['Book Value per Share'] = (df['Total Equity'] / df['Shares Outstanding']).round(2)
    df['EPS'] = (df['Net Profit'] / df['Shares Outstanding']).round(2)
    df['Dividend per Share (calc)'] = (df['Dividend Payout Amount'] / df['Shares Outstanding']).round(2)
    df['ROA < Payout'] = (df['ROA'] < df['Dividend Payout Ratio (%)']) & df['ROA'].notna() & df['Dividend Payout Ratio (%)'].notna()

    return df


def save_excel(df: pd.DataFrame) -> str:
    hkt = pytz.timezone('Asia/Hong_Kong')
    timestamp = datetime.now(hkt).strftime('%Y%m%d_%H%M%S')
    filename = f"hk_stocks_{timestamp}.xlsx"
    
    os.makedirs("data", exist_ok=True)
    path = os.path.join("data", filename)
    
    with pd.ExcelWriter(path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Stocks')
    
    print(f"✅ Saved: {path}")
    return path


if __name__ == "__main__":
    df = fetch_stock_data()
    save_excel(df)
