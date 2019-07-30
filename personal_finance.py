import wx
from sqlalchemy import create_engine
import pandas as pd
from datetime import datetime
import matplotlib
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import numpy as np
import config

matplotlib.use('WXAgg')
engine = create_engine(config.uri_keys)

class personalFinance(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self,parent=None)
        self.SetTitle('Personal Finance Application')
        self.menuBar()
        self.panel = wx.Panel(self)
        self.Maximize(True)
        self.boxSizers()
        self.createCharts()

    def menuBar(self):
        menuBar = wx.MenuBar()
        fileButton = wx.Menu()
        exitItem = wx.MenuItem(fileButton,wx.ID_EXIT,"Quit\tCtrl+Q")
        fileButton.Append(exitItem)
        menuBar.Append(fileButton,'File')
        self.SetMenuBar(menuBar)
        self.Bind(wx.EVT_MENU,lambda x:self.Close(),exitItem)

    def accountsListBox(self):
        # choices = list(engine.execute("""SELECT name
        #                           FROM accounts"""))
        # choices = [choice[0] for choice in choices]
        # choices = []
        choices.append('All')
        choices.append('Bank of America')
        choices.append('Cash')
        choices.append('Chase')
        self.accountslistbox = wx.ListBox(self.panel,id = wx.ID_ANY,choices=choices,style=wx.LB_SORT,pos=wx.DefaultPosition)
        self.accountslistbox.SetSelection(0)
        self.accountslistbox.Bind(wx.EVT_LISTBOX,self.updateValues)
        self.Box.Add(self.accountslistbox,0,wx.ALL|wx.EXPAND,10)

    def updateValues(self,event):
        self.transactionslistctrl.DeleteAllItems()
        self.transactionslistctrl.DeleteAllColumns()
        accounts = self.accountslistbox.GetString(self.accountslistbox.GetSelection())
        timeFrame = {'1M':1,'3M':3,'6M':6,'1Y':12,'5Y':60}
        self.month = timeFrame[self.rb.GetItemLabel(self.rb.GetSelection())]
        date = datetime(datetime.today().year,datetime.today().month,1) - relativedelta(months=int(self.month)-1)
        self.new_df = self.df[self.df['DateTime'] >=date]
        if accounts !='All': self.new_df = self.new_df[self.new_df['Account Name']==accounts]
        self.new_df.reset_index(inplace=True,drop=True)
        val_dict = {0:'Date',1:'Account Name',2:'Category',3:'Description',4:"Amount"}
        for val in val_dict: self.transactionslistctrl.InsertColumn(val,val_dict[val])
        for i,v in self.new_df.iterrows():
            self.transactionslistctrl.InsertItem(i,v[1])
            self.transactionslistctrl.SetItem(i,1,v[7])
            self.transactionslistctrl.SetItem(i,2,v[6])
            self.transactionslistctrl.SetItem(i,3,v[2][:50])
            self.transactionslistctrl.SetItem(i,4,str(v[4]))
        for val in val_dict: self.transactionslistctrl.SetColumnWidth(val,wx.LIST_AUTOSIZE_USEHEADER)
        self.updateCharts()
        self.updateBalances()

    def boxSizers(self):
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.Box = wx.BoxSizer(wx.HORIZONTAL)
        self.chartSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.accountsListBox()
        self.transactionsListCtrl()
        self.balances()
        self.buttonsSizer = wx.BoxSizer(wx.VERTICAL)
        self.radioButtons()
        mainSizer.Add(self.Box,0,wx.ALL|wx.EXPAND,5)
        self.panel.SetSizer(mainSizer)
        mainSizer.Add(self.chartSizer,1,wx.ALL|wx.EXPAND,5)
        mainSizer.Fit(self)

    def balances(self):
        self.staticbox = wx.StaticBox(self.panel,label="Balances")
        self.bsizer = wx.StaticBoxSizer(self.staticbox,wx.VERTICAL)
        self.Box.Add(self.bsizer,1,wx.ALL|wx.EXPAND,10)
        sum_df = self.new_df.groupby('Account Name').sum()
        sum_df = sum_df['Amount']
        s=""
        for i in range(len(sum_df)):
            s += sum_df.index[i] + "     " +  '{:,.2f}'.format(sum_df[i]) + "\n"
        self.stext = wx.StaticText(self.panel,id=wx.ID_ANY,label=s)
        self.bsizer.Add(self.stext, 0, wx.TOP|wx.LEFT, 10)

    def updateBalances(self):
        sum_df = self.new_df.groupby('Account Name').sum()
        sum_df = sum_df['Amount']
        s=""
        for i in range(len(sum_df)):
            s += sum_df.index[i] + "     " +  '{:,.2f}'.format(sum_df[i]) + "\n"
        self.stext.SetLabel(s)

    def transactionsListCtrl(self):
        self.df = pd.read_csv('transactions.csv')
        self.df = self.df[self.df['Labels']!='Misc']
        # self.df['DateTime']= self.df['Date'].astype('datetime64[ns]')
        self.df['DateTime'] = pd.to_datetime(self.df['Date'])
        currentMonth = datetime.now().month
        self.df.replace({'Transaction Type':{'credit':1,'debit':-1}},inplace=True)
        self.df['Amount'] = self.df['Amount']*self.df['Transaction Type']
        self.df.reset_index(inplace=True)
        self.transactionslistctrl = wx.ListCtrl(self.panel,style=wx.LC_REPORT| wx.LC_ALIGN_LEFT,size=(750,200))
        self.new_df = self.df[self.df['DateTime'].dt.month==datetime.now().month]
        val_dict = {0:'Date',1:'Account Name',2:'Category',3:'Description',4:"Amount"}
        for val in val_dict: self.transactionslistctrl.InsertColumn(val,val_dict[val])
        self.new_df.reset_index(inplace=True,drop=True)
        for i,v in self.new_df.iterrows():
            self.transactionslistctrl.InsertItem(i,v[1])
            self.transactionslistctrl.SetItem(i,1,v[7])
            self.transactionslistctrl.SetItem(i,2,v[6])
            self.transactionslistctrl.SetItem(i,3,v[2][:50])
            self.transactionslistctrl.SetItem(i,4,str(v[4]))
        for val in val_dict: self.transactionslistctrl.SetColumnWidth(val,wx.LIST_AUTOSIZE_USEHEADER)
        self.Box.Add(self.transactionslistctrl,1,wx.ALL|wx.EXPAND,10)

    def radioButtons(self):
        self.rb = wx.RadioBox(self.panel,wx.ID_ANY,"Time Frame",choices=["1M","3M","6M","1Y","5Y"],style=wx.VERTICAL)
        self.rb.SetSelection(0)
        self.buttonsSizer.Add(self.rb,1,wx.ALL|wx.EXPAND,10)
        self.Bind(wx.EVT_RADIOBOX, self.updateValues)
        self.Box.Add(self.buttonsSizer,1,wx.ALL|wx.EXPAND,10)

    def createCharts(self):
        self.figure = plt.figure()
        self.figure.tight_layout()
        self.canvas = FigureCanvas(self.panel,-1,self.figure)
        self.chartSizer.Add(self.canvas,1,10)
        self.ax1 = self.figure.add_subplot(131)
        self.ax2 = self.figure.add_subplot(132)
        self.ax3 = self.figure.add_subplot(133)
        self.updateCharts()

    def lineChart(self):
        self.ax1.clear()
        df = self.new_df.copy()
        df['Cumulative'] = df['Amount'].cumsum()
        df.plot(x='Date',y='Cumulative',ax=self.ax1,rot=30,legend=False,title='Cash Flow')

    def pieChart(self):
        self.ax2.clear()
        df = self.new_df.copy()
        df = df[df['Amount']<0]
        df['Amount'] = df['Amount'].abs()
        df = df.groupby('Category').sum()
        df.plot(kind='pie',y='Amount',ax=self.ax2,autopct='%1.1f%%',fontsize=6,legend=False,title='Expenses')
        self.ax2.set_ylabel('')

    def barChart(self):
        self.ax3.clear()
        df = self.new_df.copy()
        df.set_index('DateTime',drop=True,inplace=True)
        df = df.groupby([df.index.year,df.index.month,df.Labels]).sum()
        df = df[['Notes','Amount']].unstack()
        df.drop('Notes',axis=1,inplace=True)
        df.fillna(value=0,axis=0,inplace=True)
        df.plot(kind='bar',stacked=True,ax=self.ax3,legend=False,rot=45)

    def updateCharts(self):
        self.figure.set_canvas(self.canvas)
        self.lineChart()
        self.pieChart()
        self.barChart()
        self.canvas.draw()

def main():
    app = wx.App()
    personalfinance = personalFinance()
    personalfinance.Show()
    app.MainLoop()
    plt.show()

if __name__ =='__main__':
    main()
