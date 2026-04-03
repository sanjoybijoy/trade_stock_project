from django import forms

class FileUploadForm(forms.Form):
    file = forms.FileField(label='Select a file')


from django import forms
from .models import WatchList, WatchListSymbol

class WatchListForm(forms.ModelForm):
    class Meta:
        model = WatchList
        fields = ['name']

class WatchListSymbolForm(forms.ModelForm):
    class Meta:
        model = WatchListSymbol
        fields = ['symbol']


from django import forms
from .models import TickerSplit

class TickerSplitForm(forms.ModelForm):
    class Meta:
        model = TickerSplit
        fields = ['date', 'symbol', 'ratio']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
        
from django import forms
from .models import BuyNSell

class BuySellForm(forms.ModelForm):
    class Meta:
        model = BuyNSell
        fields = ['date', 'symbol', 'quantity', 'fill_price', 'transaction_type']
