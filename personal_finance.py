import wx
import wx.adv
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
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData
import wx.lib.mixins.listctrl as listmix

matplotlib.use('WXAgg')
plt.style.use('ggplot')
engine = create_engine(config.uri)
Session = sessionmaker(bind=engine)
session = Session()
conn = engine.connect()
meta = MetaData(engine,reflect=True)

class personalFinance(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self,parent=None)
        self.locale = wx.Locale(wx.LANGUAGE_ENGLISH_US)
        self.SetTitle('Personal Finance Application')
        self.menuBar()
        self.panel = wx.Panel(self)
        self.Maximize(True)
        self.createCharts()
        self.boxSizers()
        self.SetFocus()
        self.Centre()

    def menuBar(self):
        menuBar = wx.MenuBar()
        fileMenu = wx.Menu()
        newItem = wx.Menu()
        
        bank_account = newItem.Append(wx.ID_ANY,"Bank account")
        category = newItem.Append(wx.ID_ANY,"Category")
        transaction = newItem.Append(wx.ID_ANY,"Transaction")
        fileMenu.Append(wx.ID_ANY,"New",newItem)
        editItem = wx.MenuItem(fileMenu,wx.ID_ANY,"Edit\tCtrl+E")
        fileMenu.Append(editItem)
        fileMenu.AppendSeparator()
        exitItem = wx.MenuItem(fileMenu,wx.ID_EXIT,"Quit\tCtrl+Q")
        fileMenu.Append(exitItem)
        menuBar.Append(fileMenu,'File')
        self.SetMenuBar(menuBar)
        self.Bind(wx.EVT_MENU,self.addBank,bank_account)
        self.Bind(wx.EVT_MENU,self.addCategory,category)
        self.Bind(wx.EVT_MENU,self.addTransaction,transaction)
        self.Bind(wx.EVT_MENU,self.editTransaction,editItem)
        self.Bind(wx.EVT_MENU,lambda x:self.Destroy(),exitItem)

    def addBank(self,event):
        bank = Bank_Accounts()
        bank.Show()

    def editTransaction(self,event):
        transactionslookup = TransactionsLookup()
        transactionslookup.Show()

    def addTransaction(self,event):
        transactions = Transactions()
        transactions.Show()
        self.updateValues(event)

    def addCategory(self,event):
        categories = Categories()
        categories.Show()
        self.updateValues(event)

    def accountsListBox(self):
        choices = pd.read_sql("SELECT name FROM accounts",conn)
        choices = choices.name.to_list()
        choices.append("All")
        choices.sort()
        self.accountslistbox = wx.ListBox(self.panel,id = wx.ID_ANY,choices=choices,style=wx.LB_SORT,pos=wx.DefaultPosition)
        self.accountslistbox.SetSelection(0)
        self.accountslistbox.Bind(wx.EVT_LISTBOX,self.updateValues)
        self.Box.Add(self.accountslistbox,0,wx.ALL|wx.EXPAND,10)

    def updateValues(self,event):
        accounts = self.accountslistbox.GetString(self.accountslistbox.GetSelection())
        timeFrame = {'1M':1,'3M':3,'6M':6,'1Y':12,'5Y':60}
        currMonth = timeFrame[self.rb.GetItemLabel(self.rb.GetSelection())]
        datePrev = datetime(datetime.today().year,datetime.today().month,1) - relativedelta(months=int(currMonth)-1)
        self.transactionslistctrl.DeleteAllItems()
        self.transactionslistctrl.DeleteAllColumns()
        self.downloadData()
        self.new_df = self.df[self.df['date'] >=datePrev]
        if accounts !="All": self.new_df = self.new_df[self.new_df['account_name']==accounts]
        self.new_df['dateString'] = self.new_df['date'].dt.date
        self.new_df.reset_index(inplace=True,drop=True)
        val_dict = {0:'Date',1:'Account Name',2:'Category',3:'Description',4:"Amount"}
        for val in val_dict: self.transactionslistctrl.InsertColumn(val,val_dict[val])
        for i,v in self.new_df.iterrows():
            if v[0] !="":
                self.transactionslistctrl.InsertItem(i,str(v[9]))
                self.transactionslistctrl.SetItem(i,1,str(v[8]))
                self.transactionslistctrl.SetItem(i,2,str(v[6]))
                self.transactionslistctrl.SetItem(i,3,str(v[1]))
                self.transactionslistctrl.SetItem(i,4,'{:,.2f}'.format(v[2]))
        for val in val_dict: self.transactionslistctrl.SetColumnWidth(val,150)
        self.updateCharts()
        self.updateBalances()

    def boxSizers(self):
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.Box = wx.BoxSizer(wx.HORIZONTAL)
        self.buttonsSizer = wx.BoxSizer(wx.VERTICAL)
        self.accountsListBox()
        self.radioButtons()
        self.transactionsListCtrl()
        mainSizer.Add(self.Box,0,wx.ALL|wx.EXPAND,5)
        self.panel.SetSizer(mainSizer)
        mainSizer.Add(self.chartSizer,1,wx.ALL|wx.EXPAND,5)
        mainSizer.Fit(self)

    def balances(self):
        self.staticbox = wx.StaticBox(self.panel,label="Balances")
        self.bsizer = wx.StaticBoxSizer(self.staticbox,wx.VERTICAL)
        self.Box.Add(self.bsizer,1,wx.ALL|wx.EXPAND,10)
        sum_df = self.new_df.groupby('account_name').sum()
        sum_df = sum_df['amount']
        s=""
        for i in range(len(sum_df)):
            s += sum_df.index[i] + "     " +  '{:,.2f}'.format(sum_df[i]) + "\n"
        self.stext = wx.StaticText(self.panel,id=wx.ID_ANY,label=s)
        self.bsizer.Add(self.stext, 0, wx.TOP|wx.LEFT, 10)

    def updateBalances(self):
        sum_df = self.new_df.groupby('account_name').sum()
        sum_df = sum_df['amount']
        self.stext.SetLabel("")
        s=""
        for i in range(len(sum_df)):
            s += sum_df.index[i] + "     " +  '{:,.2f}'.format(sum_df[i]) + "\n"
        self.stext.SetLabel(s)

    def transactionsListCtrl(self):
        self.transactionslistctrl = wx.ListCtrl(self.panel,style=wx.LC_REPORT| wx.LC_ALIGN_LEFT,size=(750,200))
        self.downloadData()
        self.new_df = self.df[self.df['date'].dt.month==datetime.now().month]
        self.balances()
        self.updateValues(wx.EVT_LISTBOX)
        self.Box.Add(self.transactionslistctrl,1,wx.ALL|wx.EXPAND,10)

    def downloadData(self):
        self.df = pd.read_sql("""SELECT t.date as date
                                ,t.description as description
                                ,t.amount as amount
                                ,t.category as category
                                ,t.bank as bank
                                ,ec.id as expense_id
                                ,ec.name as expense_name
                                ,a.id as account_id
                                ,a.name as account_name
                                FROM transactions t
                                JOIN expense_categories ec ON ec.id = t.category
                                JOIN accounts a ON a.ID = t.bank
                                WHERE ec.name <>'Misc'
                                ORDER BY t.date DESC""",conn)

    def radioButtons(self):
        self.rb = wx.RadioBox(self.panel,wx.ID_ANY,"Time Frame",choices=["1M","3M","6M","1Y","5Y"],style=wx.VERTICAL)
        self.rb.SetSelection(0)
        self.buttonsSizer.Add(self.rb,1,wx.ALL|wx.EXPAND,10)
        self.Bind(wx.EVT_RADIOBOX, self.updateValues)
        self.Box.Add(self.buttonsSizer,1,wx.ALL|wx.EXPAND,10)

    def createCharts(self):
        self.figure = plt.figure()
        self.chartSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.canvas = FigureCanvas(self.panel,-1,self.figure)
        self.chartSizer.Add(self.canvas,1,10)
        self.ax1 = plt.subplot2grid((1,4),(0,0))
        self.ax2 = plt.subplot2grid((1,4),(0,1),colspan=2)
        self.ax2.set_xlim(left=0,right=10)
        self.ax3 = plt.subplot2grid((1,4),(0,3))

    def lineChart(self):
        self.ax1.clear()
        df = self.new_df.copy()
        df.sort_values('date',ascending=True,inplace=True)
        df['Cumulative'] = df['amount'].cumsum()
        df.plot(x='date',y='Cumulative',ax=self.ax1,rot=30,legend=False,title='Cash Flow')
        self.ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        self.ax1.xaxis.set_major_locator(plt.MaxNLocator(5))

    def pieChart(self):
        self.ax2.clear()
        df = self.new_df.copy()
        df = df[df['amount']<0]
        df['Amount'] = df['amount'].abs()
        df = df.groupby('description').sum()
        df.plot(kind='pie',y='Amount',labels=df.index,ax=self.ax2,autopct='%1.1f%%',fontsize=6,legend=False,title='Expenses')
        self.ax2.set_ylabel('')

    def barChart(self):
        self.ax3.clear()
        df = self.new_df.copy()
        df.set_index('date',drop=True,inplace=True)
        df = df.groupby([df.index.year,df.index.month,df.category]).sum()
        df = df['amount'].unstack()
        df.fillna(value=0,axis=0,inplace=True)
        df.plot(kind='bar',stacked=True,ax=self.ax3,rot=35,title='Expense/Revenue')
        self.ax3.legend(['Expense','Revenue'])
        self.ax3.set_xlabel('')

    def updateCharts(self):
        self.figure.set_canvas(self.canvas)
        self.lineChart()
        self.pieChart()
        self.barChart()
        self.canvas.draw()

class Bank_Accounts(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self,parent=None)
        self.basicGUI()
        self.SetFocus()
        self.Centre()

    def basicGUI(self):
        account = wx.TextEntryDialog(None,"Please enter a new bank account","Add a new account")
        if account.ShowModal() == wx.ID_OK:
            account = account.GetValue()
            self.add_accounts([account])
            wx.MessageBox("You have successfully added a new bank account!","Success!",wx.OK | wx.ICON_INFORMATION)
            wx.MessageBox("Requires application to start in order for changes to take effect!","Restart Application",wx.OK|wx.ICON_INFORMATION)
        self.Destroy()

    def add_accounts(self,bank_accounts):
        status = 'active'
        Accounts = meta.tables['accounts']
        engine.execute(Accounts.insert(),[dict(name=bank_account,status=status) for bank_account in bank_accounts])

class Categories(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self,parent=None)
        self.Categories = meta.tables['expense_categories']
        self.basicGUI()
        self.SetFocus()
        self.Centre()

    def basicGUI(self):
        name = wx.TextEntryDialog(None,"Please enter a new category.","Add a new category")
        if name.ShowModal() == wx.ID_OK:
            name = name.GetValue()
        self.add_categories(name)
        wx.MessageBox("You have successfully added a new category!","Success!",wx.OK | wx.ICON_INFORMATION)
        self.Destroy()

    def add_categories(self,name):
        engine.execute(self.Categories.insert(),[dict(name=name)])

class Transactions(wx.Dialog):
    def __init__(self):
        wx.Dialog.__init__(self,parent=None)
        self.SetTitle("Add a transaction")
        self.basicGUI()
        self.Centre()
        self.SetFocus()

    def basicGUI(self):
        self.mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.leftSizer = wx.BoxSizer(wx.VERTICAL)
        self.rightSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.leftSizer,1,wx.ALL|wx.EXPAND)
        self.mainSizer.Add(self.rightSizer,1,wx.ALL)
        self.dateSizer()
        self.bankSizer()
        self.catSizer()
        self.descriptionSizer()
        self.amountSizer()
        self.buttonSizer()
        self.SetSizer(self.mainSizer)

    def dateSizer(self):
        box = wx.BoxSizer(wx.HORIZONTAL)
        locale = wx.Locale(wx.LANGUAGE_ENGLISH_US)
        date = wx.StaticText(self,label="Date: ",size=(65,18))
        self.date = wx.adv.GenericDatePickerCtrl(self,wx.ID_ANY,wx.DefaultDateTime,size=(200,23))
        box.Add(date,0,wx.ALL,5)
        box.Add(self.date,0,wx.ALL,5)
        self.leftSizer.Add(box,1)

    def bankSizer(self):
        box = wx.BoxSizer(wx.HORIZONTAL)
        self.bank_accounts = pd.DataFrame(conn.execute(meta.tables['accounts'].select()).fetchall(),columns=['ID','Name'])
        bank = wx.StaticText(self,label="Bank Account: ",size=(65,18))
        self.bank = wx.ComboBox(self,wx.ID_ANY,choices=self.bank_accounts['Name'].tolist(),size=(200,23))
        box.Add(bank,0,wx.ALL,5)
        box.Add(self.bank,0,wx.ALL,5)
        self.leftSizer.Add(box,1)

    def catSizer(self):
        box = wx.BoxSizer(wx.HORIZONTAL)
        category = wx.StaticText(self,label="Category: ",size=(65,18))
        self.categories = pd.DataFrame(conn.execute(meta.tables['expense_categories'].select()).fetchall(),columns=['ID','Name'])
        self.category = wx.ComboBox(self,wx.ID_ANY,choices=self.categories['Name'].tolist(),size=(200,23))
        box.Add(category,0,wx.ALL,5)
        box.Add(self.category ,0,wx.ALL,5)
        self.leftSizer.Add(box,1)

    def descriptionSizer(self):
        box = wx.BoxSizer(wx.HORIZONTAL)
        description = wx.StaticText(self,label="Description: ",size=(65,18))
        self.desc = wx.TextCtrl(self,wx.ID_ANY,size=(200,23))
        box.Add(description,0,wx.ALL,5)
        box.Add(self.desc,1,wx.ALL,5)
        self.leftSizer.Add(box,1)

    def amountSizer(self):
        box = wx.BoxSizer(wx.HORIZONTAL)
        amount = wx.StaticText(self,label="Amount: ",size=(65,18))
        self.amount = wx.TextCtrl(self,wx.ID_ANY,size=(200,23))
        box.Add(amount,0,wx.ALL,5)
        box.Add(self.amount,0,wx.ALL,5)
        self.leftSizer.Add(box,1)

    def buttonSizer(self):
        save = wx.Button(self,label="Save")
        cxl = wx.Button(self,label="Cancel")
        self.rightSizer.Add(save,0,wx.ALL,5)
        self.rightSizer.Add(cxl,0,wx.ALL,5)
        save.Bind(wx.EVT_BUTTON,self.add_transaction)
        cxl.Bind(wx.EVT_BUTTON,lambda x:self.Destroy())

    def add_transaction(self,event):
        self.Transactions = meta.tables['transactions']
        bank_index = self.bank_accounts[self.bank_accounts['Name']==self.bank.GetValue()].index
        bank_id = self.bank_accounts.iloc[bank_index]['ID']
        cat_index = self.categories[self.categories['Name']==self.category.GetValue()].index
        cat_id = self.categories.iloc[cat_index]['ID']
        engine.execute(self.Transactions.insert(),[dict(date=self.date.GetValue().Format("%m-%d-%Y"),
                                                        description=self.desc.GetValue(),
                                                        amount=self.amount.GetValue(),
                                                        category=int(cat_id.values[0]),
                                                        bank=int(bank_id.values[0]))])
        wx.MessageBox("You have successfully added a new transaction!","Success!",wx.OK|wx.ICON_INFORMATION)
        self.Destroy()

class TransactionsLookup(wx.Dialog):
    def __init__(self):
        wx.Dialog.__init__(self,parent=None,size=(467,350))
        self.SetTitle('Transaction lookup')
        self.getData()
        self.basicGUI()
        self.bankAccounts()
        self.datePicker()
        self.createSearchCtrl()
        self.createButtons()
        self.createListCtrl()
        self.SetFocus()
        self.Centre()

    def basicGUI(self):
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        topSizer = wx.BoxSizer(wx.HORIZONTAL)
        bottomSizer = wx.BoxSizer(wx.VERTICAL)
        self.filterSizer = wx.BoxSizer(wx.VERTICAL)
        self.buttonSizer = wx.BoxSizer(wx.VERTICAL)
        self.listSizer=wx.BoxSizer(wx.VERTICAL)
        topSizer.Add(self.filterSizer,1,wx.ALL|wx.EXPAND,5)
        topSizer.Add(self.buttonSizer,1,wx.ALL|wx.EXPAND,5)
        bottomSizer.Add(self.listSizer,1)
        mainSizer.Add(topSizer,1,wx.ALL|wx.EXPAND)
        mainSizer.Add(bottomSizer,1,wx.ALL|wx.EXPAND)
        self.SetSizer(mainSizer,0)

    def getData(self):
        self.df = pd.read_sql("""SELECT
                                t.id as transaction_id
                                ,t.date as date
                                ,t.description as description
                                ,t.amount as amount
                                ,t.category as category
                                ,t.bank as bank
                                ,ec.id as expense_id
                                ,ec.name as expense_name
                                ,a.id as account_id
                                ,a.name as account_name
                                FROM transactions t
                                JOIN expense_categories ec ON ec.id = t.category
                                JOIN accounts a ON a.ID = t.bank
                                WHERE ec.name <>'Misc'
                                ORDER BY t.date DESC""",conn)
        self.df['dateString'] = self.df['date'].dt.date
        
    def bankAccounts(self):
        bankaccounts = wx.BoxSizer(wx.HORIZONTAL)
        accounts = pd.DataFrame(conn.execute(meta.tables['accounts'].select()).fetchall(),columns=['id','name'])
        bank = wx.StaticText(self,label="Bank",size=(65,19))
        self.bankCombo = wx.ComboBox(self,wx.ID_ANY,choices=accounts['name'].tolist(),size=(275,23))
        bankaccounts.Add(bank,0,wx.ALL,1)
        bankaccounts.Add(self.bankCombo,0,wx.ALL,5)
        self.filterSizer.Add(bankaccounts,0,wx.ALL,5)

    def createButtons(self):
        searchButton = wx.Button(self,wx.ID_ANY,label="Search")
        saveButton = wx.Button(self,wx.ID_ANY,label="Save")
        clearButton = wx.Button(self,wx.ID_ANY,label="Clear")
        removeButton = wx.Button(self,wx.ID_ANY,label="Remove")
        cancelButton = wx.Button(self,wx.ID_ANY,label="Cancel")
        self.buttonSizer.Add(searchButton,0,wx.ALL,5)
        self.buttonSizer.Add(saveButton,0,wx.ALL,5)
        self.buttonSizer.Add(clearButton,0,wx.ALL,5)
        self.buttonSizer.Add(removeButton,0,wx.ALL,5)
        self.buttonSizer.Add(cancelButton,0,wx.ALL,5)
        searchButton.Bind(wx.EVT_BUTTON,self.refreshData)
        saveButton.Bind(wx.EVT_BUTTON,self.saveData)
        clearButton.Bind(wx.EVT_BUTTON,self.clearFilters)
        cancelButton.Bind(wx.EVT_BUTTON,lambda x:self.Destroy())
        removeButton.Bind(wx.EVT_BUTTON,self.removeData)

    def clearFilters(self,event):
        self.datepicker.SetValue(wx.DateTime())
        df = self.df.copy()
        self.loadData(df)
        self.search.SetValue("")
        self.bankCombo.SetValue("")

    def createSearchCtrl(self):
        self.search = wx.SearchCtrl(self,wx.ID_ANY,size=(340,26))
        self.search.ShowCancelButton(True)
        self.filterSizer.Add(self.search,0,wx.ALL|wx.EXPAND,5)

    def createListCtrl(self):
        self.listCtrl = EditableListCtrl(self,style=wx.LC_REPORT|wx.EXPAND,size=(450,125))
        self.listCtrl.SetColumnWidth(2,50)
        self.listCtrl.InsertColumn(0,"ID")
        self.listCtrl.InsertColumn(1,"Date")
        self.listCtrl.InsertColumn(2,"Bank")
        self.listCtrl.InsertColumn(3,"Description")
        self.listCtrl.InsertColumn(4,"Amount")
        if self.datepicker.GetValue().IsValid():
            self.df = self.df[self.df['date']==datetime.strptime(self.datepicker.GetValue().Format("%m-%d-%Y"),"%m-%d-%Y")]
        self.loadData(self.df)
        self.listCtrl.SetColumnWidth(0,30)
        self.listCtrl.SetColumnWidth(1,80)
        self.listCtrl.SetColumnWidth(2,120)
        self.listCtrl.SetColumnWidth(3,120)
        self.listSizer.Add(self.listCtrl,0,wx.EXPAND|wx.ALL)

    def datePicker(self):
        dateSizer = wx.BoxSizer(wx.HORIZONTAL)
        date = wx.StaticText(self,label="Date",size=(65,19))
        locale = wx.Locale(wx.LANGUAGE_ENGLISH_US)
        self.datepicker = wx.adv.GenericDatePickerCtrl(self,wx.ID_ANY,style=wx.adv.DP_ALLOWNONE|wx.adv.DP_DROPDOWN,size=(275,23))
        self.datepicker.SetValue(wx.DateTime())
        dateSizer.Add(date,0,wx.ALL,4)
        dateSizer.Add(self.datepicker,0,wx.ALL,5)
        self.filterSizer.Add(dateSizer,1)

    def refreshData(self,event):
        bankcombo = self.bankCombo.GetStringSelection()
        datepicker = self.datepicker.GetValue()
        search = self.search.GetValue()
        df = self.df.copy()
        df = df[['transaction_id', 'description', 'amount', 'account_name','dateString']]
        df['dateString'] = df['dateString'].astype('str')
        if bankcombo !="":
            df = df[df.account_name==bankcombo]
        if datepicker.IsValid():
            df = df[df.dateString == datepicker.Format("%Y-%m-%d")]
        if search !="":
            df2 = pd.DataFrame()
            for i in range(len(df)):
                listItems = list(map(str,df.iloc[i,:].to_list()))
                if search.upper() in map(str.upper,listItems):
                    df2 = df2.append([listItems])
        self.listCtrl.DeleteAllItems()
        if search!="":
            df2.columns = ['transaction_id','description','amount','account_name','dateString'] 
            self.loadData(df2)
        else:
            self.loadData(df)

    def loadData(self,df):
        self.listCtrl.DeleteAllItems()
        df.reset_index(inplace=True)
        for i in range(len(df)-1,-1,-1):
            self.listCtrl.InsertItem(0,str(df.transaction_id[i]))
            self.listCtrl.SetItem(0,1,str(df.dateString[i]))
            self.listCtrl.SetItem(0,2,str(df.account_name[i]))
            self.listCtrl.SetItem(0,3,str(df.description[i]))
            self.listCtrl.SetItem(0,4,str(df.amount[i]))
    
    def removeData(self,event):
        id = self.listCtrl.GetItem(self.listCtrl.GetFirstSelected()).GetText()
        conn.execute("DELETE FROM transactions where id = {}".format(id))
        self.getData()
        self.clearFilters(event)
        self.loadData(self.df)
        wx.MessageBox("You have successfully removed the transaction!","Success!",wx.OK|wx.ICON_INFORMATION)

    def saveData(self,event):
        id = self.listCtrl.GetItem(self.listCtrl.GetFirstSelected(),0).GetText()
        date = self.listCtrl.GetItem(self.listCtrl.GetFirstSelected(),1).GetText()
        bank = self.listCtrl.GetItem(self.listCtrl.GetFirstSelected(),2).GetText()
        description = self.listCtrl.GetItem(self.listCtrl.GetFirstSelected(),3).GetText()
        amount = self.listCtrl.GetItem(self.listCtrl.GetFirstSelected(),4).GetText()
        conn.execute('UPDATE transactions SET date = %s, description = %s,amount=%s WHERE ID =%s',(date,description,amount,id))
        self.getData()
        self.clearFilters(event)
        self.loadData(self.df)
        wx.MessageBox("You have successfully saved the transaction!","Success!",wx.OK|wx.ICON_INFORMATION)
                     
class EditableListCtrl(wx.ListCtrl,listmix.TextEditMixin):
    def __init__(self,parent,id=wx.ID_ANY,pos=wx.DefaultPosition,size=wx.DefaultSize,style=0):
        wx.ListCtrl.__init__(self,parent,id,pos,size,style)
        listmix.TextEditMixin.__init__(self)
        self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.OnBeginLabelEdit)

    def OnBeginLabelEdit(self, event):
        if event.GetColumn() ==2:
            event.Veto()
        else:
            event.Skip()


def main():
    app = wx.App()
    personalfinance = personalFinance()
    personalfinance.Show()
    app.MainLoop()
    session.commit()
    session.close()
    conn.close()
    engine.dispose()
    plt.show()

if __name__ =='__main__':
    main()
