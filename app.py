import base64
from flask import Flask, render_template, request
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from io import BytesIO
import pandas as pd
import yfinance as yf

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def plot():
    if request.method == 'POST':
        # Get the x and y values from the form
        ticker = request.form['ticker']
        ticker=ticker.upper()
        data = yf.download(ticker, period="5y")
        
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.plot(data['Adj Close'])
        ax.set_ylabel('Stock Price')
        stock_info = yf.Ticker(ticker)
        fin=0
        pd.options.display.float_format
        pd.options.display.precision = 3
        def financialratiocalc(string):
            stock_info = yf.Ticker(string)
            
            #function def
            
            def avg(df,a):
                l=[]
                for i in range(0,df.shape[0]-1):
                    d=(df[a][i]+df[a][i+1])/2
                    l.append(d)
                l.append(1)
                r="Avg "+a
                df[r]=l
                return df
                
            def get_first_n_strings(strings, n):
                return strings[:n]
            

            
            def stringfinder(outer_list,search_string):
                if all(x in outer_list for x in search_string):
                    return True
                else:
                    return False
            def nanfiller(n,FY):
                nan_list=[]
                for i in range(n):
                    nan_list.append(float('nan'))
                dnan=pd.DataFrame(nan_list)
                dnan=dnan.transpose()
                dnan.columns=get_first_n_strings(FY,n)
                dnaN=dnan
                dnaN=dnaN.transpose()
                return dnaN
            # Fetch the income statement data for the ticker
            income_statement_data = stock_info.financials
            income_statement_data=pd.DataFrame(income_statement_data)
            income_statement_data.columns=income_statement_data.columns.year
            FY=list(map(str, income_statement_data.columns))
            income_statement_data.columns=get_first_n_strings(FY,income_statement_data.shape[1])
            income_statement_data=income_statement_data.transpose()

            # Fetch the cash flow statement data for the ticker
            cashflow_statement_data = stock_info.cashflow
            cashflow_statement_data=pd.DataFrame(cashflow_statement_data)
            cashflow_statement_data.columns=cashflow_statement_data.columns.year
            FY=list(map(str, cashflow_statement_data.columns))
            cashflow_statement_data.columns=get_first_n_strings(FY,cashflow_statement_data.shape[1])
            cashflow_statement_data=cashflow_statement_data.transpose()
            

            
            # Fetch the balance sheet data for the ticker
            balance_sheet_data = stock_info.balance_sheet
            balance_sheet_data=pd.DataFrame(balance_sheet_data)
            balance_sheet_data.columns=balance_sheet_data.columns.year
            FY=list(map(str, balance_sheet_data.columns))
            balance_sheet_data.columns=get_first_n_strings(FY,balance_sheet_data.shape[1])
            balance_sheet_data=balance_sheet_data.transpose()
            
            
            listi=income_statement_data.columns.to_list()
            listc=cashflow_statement_data.columns.to_list()
            listb=balance_sheet_data.columns.to_list()
            
            if stringfinder(balance_sheet_data,['Payables And Accrued Expenses']):
                balance_sheet_data=balance_sheet_data.rename(columns={'Payables And Accrued Expenses':'Accounts Payables'})
            
            
            inv=0
            
            avg(balance_sheet_data,'Total Assets')
            avg(balance_sheet_data,'Total Equity Gross Minority Interest')
            if stringfinder(listb,['Inventory'])==True:
                avg(balance_sheet_data,'Inventory')
                inv=1
            avg(balance_sheet_data,'Accounts Payables')
            avg(balance_sheet_data,'Receivables')
            

            
            #purchases
            if stringfinder(listb,['Inventory'])==True:
                pur=[]
                for i in range(0,balance_sheet_data.shape[0]-1):
                    pur.append(balance_sheet_data['Inventory'][i]-balance_sheet_data['Inventory'][i+1]+income_statement_data['Cost Of Revenue'][i])
                pur.append(1)
                balance_sheet_data['Purchases']=pur
            #Performance Ratios
            Cashflowtorevenue=cashflow_statement_data['Cash Flow From Continuing Operating Activities']/income_statement_data['Net Income']
            Cashreturnonassets=cashflow_statement_data['Cash Flow From Continuing Operating Activities']/balance_sheet_data['Avg Total Assets']
            Cashreturnonequity=cashflow_statement_data['Cash Flow From Continuing Operating Activities']/balance_sheet_data['Avg Total Equity Gross Minority Interest']
            Cashtoincome=cashflow_statement_data['Cash Flow From Continuing Operating Activities']/income_statement_data['Operating Income']
            PerformanceR=pd.concat([Cashflowtorevenue,Cashreturnonassets,Cashreturnonequity,Cashtoincome],axis=1)
            PerformanceR.columns=['Cashflow to Revenue','Cash Returns on Assets','Cash return on equity','Cash to Income']
            PerformanceR=PerformanceR.drop(PerformanceR.index[-1])

            #Coverage Ratio
            Debtcoverage=cashflow_statement_data['Cash Flow From Continuing Operating Activities']/balance_sheet_data['Total Debt']
            if stringfinder(listi,['Normalized EBITDA'])==True:
                Debtpaymentratio=balance_sheet_data['Total Debt']/income_statement_data['Normalized EBITDA']
            else:
                Debtpaymentratio=nanfiller(balance_sheet_data.shape[0],FY)
            if stringfinder(listi,['EBIT','Interest Expense']):
                Interestcoverage=income_statement_data['EBIT']/income_statement_data['Interest Expense']
            else:
                Interestcoverage=nanfiller(income_statement_data.shape[0],FY)
            CoverageR=pd.concat([Debtcoverage,Debtpaymentratio,Interestcoverage],axis=1)
            CoverageR.columns=['Debt Coverage','Debt Payment Ratio','Interest Coverage']
            CoverageR=CoverageR.drop(CoverageR.index[-1])
            CoverageR=CoverageR.transpose()
            CoverageR.columns=get_first_n_strings(FY,CoverageR.shape[1])
            CoverageR=CoverageR.transpose()
            
            
            #Activity Turnover Ratios
            if inv==1:
                Inventoryturnover=income_statement_data['Cost Of Revenue']/balance_sheet_data['Avg Inventory']
                Payablesturnover=balance_sheet_data['Purchases']/balance_sheet_data['Avg Accounts Payables']
            else:
                Inventoryturnover=nanfiller(income_statement_data.shape[0],FY)
                Payablesturnover=nanfiller(income_statement_data.shape[0],FY)

            Receivableturnover=income_statement_data['Total Revenue']/balance_sheet_data['Avg Receivables']
            Totalassetturnover=income_statement_data['Total Revenue']/balance_sheet_data['Total Assets']
            ActivityTR=pd.concat([Inventoryturnover,Payablesturnover,Receivableturnover,Totalassetturnover],axis=1)
            ActivityTR.columns=['Inventory Turnover','Payables Turnover','Receivalbes Turnover','Total Asset Turnover']
            ActivityTR=ActivityTR.drop(ActivityTR.index[-1])

            #Days of Ratio
            
            Daysofpayables=365/Payablesturnover
            Daysofsales=365/Receivableturnover

            if inv==1:
                Daysofinventory=365/Inventoryturnover
                #Netcashconversioncycle=Daysofinventory+Daysofsales-Daysofpayables
            else:
                Daysofinventory=nanfiller(balance_sheet_data.shape[0],FY)
                #Netcashconversioncycle=nanfiller(balance_sheet_data.shape[0],FY)
            
            DaysofR=pd.concat([Daysofinventory,Daysofpayables,Daysofsales],axis=1)
            DaysofR.columns=['Days of Inventory','Days of Payables','Days of Sales']
            DaysofR=DaysofR.drop(DaysofR.index[-1])

            #LiquidityRatios
            Currentratio=balance_sheet_data['Current Assets']/balance_sheet_data['Current Liabilities']
            if inv==1:
                Quickratio=(balance_sheet_data['Current Assets']-balance_sheet_data['Inventory'])/balance_sheet_data['Current Liabilities']
            else:
                Quickratio=Currentratio
            Cashratio=(balance_sheet_data['Cash Cash Equivalents And Short Term Investments'])/balance_sheet_data['Current Liabilities']
            #Workingcapital=balance_sheet_data['Current Assets']-balance_sheet_data['Current Liabilities']
            LiquidityR=pd.concat([Currentratio,Quickratio,Cashratio],axis=1)
            LiquidityR.columns=['Current Ratio','Quick Ratio','Cash Ratio']
            LiquidityR=LiquidityR.drop(LiquidityR.index[-1])

            #Solvency Ratios
            Debttoequity=balance_sheet_data['Total Debt']/balance_sheet_data['Total Equity Gross Minority Interest']
            Debttocapital=balance_sheet_data['Total Debt']/(balance_sheet_data['Total Equity Gross Minority Interest']+balance_sheet_data['Total Debt'])
            Debttoassets=balance_sheet_data['Total Debt']/balance_sheet_data['Total Assets']
            Financialleverage=balance_sheet_data['Avg Total Assets']/balance_sheet_data['Avg Total Equity Gross Minority Interest']
            Debttoebitda=balance_sheet_data['Total Debt']/income_statement_data['Normalized EBITDA']
            SolvencyR=pd.concat([Debttoequity,Debttocapital,Debttoassets,Financialleverage,Debttoebitda],axis=1)
            SolvencyR.columns=['Debt to equity','Debt to capital','Debt to Assets','Financial Leverage','Debt to EBITDA']
            SolvencyR=SolvencyR.drop(SolvencyR.index[-1])

            #Profitability Ratios
            Netprofitmargin=income_statement_data['Net Income']/income_statement_data['Total Revenue']
            Grossprofit=income_statement_data['Gross Profit']/income_statement_data['Total Revenue']
            Operatingprofitmargin=income_statement_data['EBIT']/income_statement_data['Total Revenue']
            Roa=income_statement_data['Net Income']/balance_sheet_data['Avg Total Assets']
            Roe=income_statement_data['Net Income']/balance_sheet_data['Avg Total Equity Gross Minority Interest']
            ProfitabilityR=pd.concat([Netprofitmargin,Grossprofit,Operatingprofitmargin,Roa,Roe],axis=1)
            ProfitabilityR.columns=['Net Profit Margin','Gross Profit','Operating Profit Margin','Return on Assets','Return on Equity']
            ProfitabilityR=ProfitabilityR.drop(ProfitabilityR.index[-1])

            total=pd.concat([LiquidityR,SolvencyR,ProfitabilityR,PerformanceR,CoverageR,ActivityTR,DaysofR],axis=1)
            return total
        def financialratiointegrator(ticker):
            d=financialratiocalc(ticker)
            d=d.iloc[0]
            d=pd.DataFrame(d)
            d.columns=[ticker]
            d=d.fillna("Not Available")
            return d
        def reportfile(sec):
            
            if sec=='Industrials':
                df=pd.read_csv('https://raw.githubusercontent.com/RishikeshMahadevan/SectorAnalyzer/main/Industrials.csv')
                #return df
            elif sec=='Health Care':
                df=pd.read_csv('https://raw.githubusercontent.com/RishikeshMahadevan/SectorAnalyzer/main/Healthcare.csv')
                #return df
            elif sec=='Information Technology':
                df=pd.read_csv('https://raw.githubusercontent.com/RishikeshMahadevan/SectorAnalyzer/main/Informationtechnology.csv')
                #return df
            elif sec=='Communication Services':
                df=pd.read_csv('https://raw.githubusercontent.com/RishikeshMahadevan/SectorAnalyzer/main/Communicationservices.csv')
                #return df
            elif sec=='Consumer Staples':
                df=pd.read_csv('https://raw.githubusercontent.com/RishikeshMahadevan/SectorAnalyzer/main/Consumerstaples.csv')
                #return df
            elif sec=='Consumer Discretionary':
                df=pd.read_csv('https://raw.githubusercontent.com/RishikeshMahadevan/SectorAnalyzer/main/Consumerdiscretionary.csv')
                #return df
            elif sec=='Utilities':
                df=pd.read_csv('https://raw.githubusercontent.com/RishikeshMahadevan/SectorAnalyzer/main/Utilities.csv')
                #return df
            elif sec=='Materials':
                df=pd.read_csv('https://raw.githubusercontent.com/RishikeshMahadevan/SectorAnalyzer/main/Materials.csv')
                #return df
            elif sec=='Real Estate':
                df=pd.read_csv('https://raw.githubusercontent.com/RishikeshMahadevan/SectorAnalyzer/main/Realestate.csv')
                #return df
            elif sec=='Energy':
                df=pd.read_csv('https://github.com/RishikeshMahadevan/SectorAnalyzer/blob/main/Energy.csv')
                #return df
            elif sec=='Financials':
                return 0
            else:
                return 0
    
            
            l=df.columns.to_list()
            l=l[1::]
            pd.options.display.float_format = '{:.3f}'.format
            df['Sector Top 5 Average']=df.mean(axis=1)
            df.style.format({'Sector Top 5 Average': '{:,.2f}'.format})
            df=df.fillna("Not Available")
            #df=df.iloc[::,-1]
            df.rename(columns={'Unnamed: 0':'Financial Ratios'},inplace=True)
            df=df.set_index(df['Financial Ratios'])
            df=df.drop(l,axis=1)
            df=df.drop(['Financial Ratios'],axis=1)
            df=df.T
            df = df.drop('Working Capital', axis=1)
            df=df.drop('Net Cash Conversion Cycle',axis=1)
            df=df.T

            return df
        sector=pd.read_csv('https://raw.githubusercontent.com/RishikeshMahadevan/SectorAnalyzer/main/sp500.csv')
        
        tick=sector['Symbol'].to_list()
        sect=sector['GICS Sector'].to_list()
     
        stringfinderindex=0
        for i in range(0,len(tick)-1):
            if ticker==tick[i]:
                stringfinderindex=i
        sec=sect[stringfinderindex]
        if sec=='Financials':
            fin=1
            def finfinancialratiocalc(string):
                pd.options.display.precision = 3
                stock=yf.Ticker(string)
                df = pd.DataFrame.from_dict(stock.info, orient='index', columns=['Values'])
                df=df.T
                profitmargin=df['profitMargins']
                revenuegrowth=df['revenueGrowth']
                current=df['currentRatio']
                roa=df['returnOnAssets']
                roe=df['returnOnEquity']
                de=df['debtToEquity']
                quick=df['quickRatio']
                beta=df['beta']
                pe=df['trailingPE']
                eps=df['trailingEps']
                divy=df['dividendYield']
                pb=df['priceToBook']
                summary=pd.concat([profitmargin,revenuegrowth,pe,eps,divy,pb,beta,current,quick,roa,roe],axis=1)
                summary.columns=['Profit Margin','Revenue Growth','Price to Earnings Ratio','Earnings per Share','Dividend Yield','Price to Book value','Beta','Current Ratio', 'Quick Ratio', 'Return on Assets','Return on Equity']
                summary= summary.fillna("Not Available")
                summary=summary.T
                return summary
            df=finfinancialratiocalc(ticker)
            finalratios=df.to_html()
        else:
            pd.options.display.float_format
            df=reportfile(sec)
            dt=financialratiointegrator(ticker)
            pq=financialratiocalc(ticker)
            pq=pq.transpose()
            d=pd.concat([pq,df],axis=1)     
            finalratios=d.to_html()  
    
    
    
        #Technical Analysis
        from yahoo_fin import stock_info as si

        # Get 5-minute stock data for a specific stock
        data = si.get_data(ticker,start_date='2022-6-9' ,interval='1d')
        # calculate the 20-day moving average
        data['20-day MA'] = data['adjclose'].rolling(window=20).mean()

        # calculate the 50-day moving average
        data['50-day MA'] = data['adjclose'].rolling(window=50).mean()

        # calculate the 200-day moving average
        #data['200-day MA'] = data['adjclose'].rolling(window=200).mean()

        # plot the stock data, 20-day MA, 50-day MA, and 200-day MA

        ma = plt.figure()
        ax = ma.add_subplot(111)
        ax.plot(data['adjclose'], label='Stock Data', color='blue')
        ax.plot(data['20-day MA'], label='20-day MA', color='red')
        ax.plot(data['50-day MA'], label='50-day MA', color='purple')
        #ax.plot(data['200-day MA'], label='200-day MA', color='green')
        ax.xaxis.set_major_locator(plt.MaxNLocator(5))
        ax.set_xlabel('Date')
        ax.set_ylabel('Price')
        ax.set_title('Stock Data with Moving Averages')
        ax.legend()
        
        #Bollinger Bands

        # calculate the moving average and standard deviation
        data['SMA'] = data['adjclose'].rolling(window=20).mean()
        data['STD'] = data['adjclose'].rolling(window=20).std()

        # calculate the upper and lower bands
        data['Upper Band'] = data['SMA'] + (data['STD'] * 2)
        data['Lower Band'] = data['SMA'] - (data['STD'] * 2)

        # plot the stock data and Bollinger Bands
        
        bol = plt.figure()
        ax = bol.add_subplot(111)
        ax.plot(data['adjclose'], label='Close')
        ax.plot(data['SMA'], label='SMA', color='black')
        ax.plot(data['Upper Band'], label='Upper Band', color='red')
        ax.plot(data['Lower Band'], label='Lower Band', color='green')
        ax.xaxis.set_major_locator(plt.MaxNLocator(5))
        ax.set_xlabel('Date')
        ax.set_ylabel('Price')
        ax.set_title('Bollinger Bands')
        ax.legend()

        #Momentum oscillator
        #ROC
        data['ROC'] = data['adjclose'].pct_change(periods=10)*100

        # plot the stock data and ROC
        roc = plt.figure()
        ax = roc.add_subplot(111)
        ax.plot(data['adjclose'], label='Close')
        ax.plot(data['ROC'], label='ROC', color='red')
        
        ax.set_xlabel('Date')
        ax.set_ylabel('Price')
        ax.axhline(y=0, color='black', linestyle='--')
        ax.xaxis.set_major_locator(plt.MaxNLocator(5))
        ax.set_title('ROC Oscillator')
        ax.legend()

        #RSI
        delta = data['adjclose'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        rsI = 100 - (100 / (1 + rs))

        # plot the stock data and RSI
        rsi = plt.figure()
        ax = rsi.add_subplot(111)
        ax.plot(rsI, label='RSI', color='blue')
        ax.axhline(y=30, color='black', linestyle='--') # add the horizontal line at 30
        ax.axhline(y=70, color='black', linestyle='--') # add the horizontal line at 70
        ax.xaxis.set_major_locator(plt.MaxNLocator(5))
        ax.set_xlabel('Date')
        ax.set_ylabel('RSI')
        ax.set_title('Relative Strength Indicator')
        ax.legend()

        #stochastic
        low_low = data['adjclose'].rolling(window=14).min()
        high_high = data['adjclose'].rolling(window=14).max()
        stochastic_osc = (data['adjclose'] - low_low) / (high_high - low_low) * 100

        # plot the stock data and Stochastic Oscillator
        so = plt.figure()
        ax = so.add_subplot(111)
        ax.plot(data['adjclose'], label='Close')
        ax.plot(stochastic_osc, label='Stochastic Oscillator', color='red')
        ax.xaxis.set_major_locator(plt.MaxNLocator(5))
        ax.axhline(y=80, color='black', linestyle='--') 
        ax.axhline(y=20, color='black', linestyle='--')
        ax.set_xlabel('Date')
        ax.set_ylabel('Price')
        ax.set_title('Stochastic Oscillator')
        ax.legend()

        data['26-day EMA'] = data['adjclose'].ewm(span=26).mean()

        #MACD

        data['12-day EMA'] = data['adjclose'].ewm(span=12).mean()

        # calculate the MACD
        data['MACD'] = data['12-day EMA'] - data['26-day EMA']


        # calculate the signal line
        data['Signal Line'] = data['MACD'].ewm(span=9).mean()

        # calculate the histogram
        data['Histogram'] = data['MACD'] - data['Signal Line']

        # plot the MACD and Histogram
        mcd = plt.figure()
        ax = mcd.add_subplot(111)
        ax.plot(data['MACD'], label='MACD', color='blue')
        ax.plot(data['Signal Line'], label='Signal Line', color='red')
        ax.bar(data.index, data['Histogram'], label='Histogram')
        ax.xaxis.set_major_locator(plt.MaxNLocator(5))
        ax.set_xlabel('Date')
        ax.set_ylabel('MACD')
        ax.set_title('Moving Average Convergence Divergence')
        ax.legend()











        #############################################################################3
       

        # Convert the plot to a PNG image
        png_output = BytesIO()
        FigureCanvas(fig).print_png(png_output)

        # Encode the image as a base64 string
        png_output_b64 = base64.b64encode(png_output.getvalue()).decode('utf-8')
        
        png_output = BytesIO()
        FigureCanvas(ma).print_png(png_output)

        # Encode the image as a base64 string
        MA = base64.b64encode(png_output.getvalue()).decode('utf-8')

        png_output = BytesIO()
        FigureCanvas(bol).print_png(png_output)

        # Encode the image as a base64 string
        bol = base64.b64encode(png_output.getvalue()).decode('utf-8')

        png_output = BytesIO()
        FigureCanvas(roc).print_png(png_output)

        # Encode the image as a base64 string
        roc = base64.b64encode(png_output.getvalue()).decode('utf-8')


        png_output = BytesIO()
        FigureCanvas(rsi).print_png(png_output)

        # Encode the image as a base64 string
        rsi = base64.b64encode(png_output.getvalue()).decode('utf-8')

        png_output = BytesIO()
        FigureCanvas(so).print_png(png_output)

        # Encode the image as a base64 string
        so = base64.b64encode(png_output.getvalue()).decode('utf-8')
        png_output = BytesIO()
        FigureCanvas(mcd).print_png(png_output)

        # Encode the image as a base64 string
        mcd= base64.b64encode(png_output.getvalue()).decode('utf-8')

        # Render the template with the base64-encoded image
        return render_template('plot.html', png_output_b64=png_output_b64,ma=MA,bol=bol,roc=roc,rsi=rsi,so=so,mcd=mcd,ticker=ticker,Finaltable=finalratios)
    else:
        # Render the form template
        return render_template('index.html')

if __name__=="__main__":
    app.run(debug=True)