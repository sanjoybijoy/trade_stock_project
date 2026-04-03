from django.db import models
from django.contrib.auth.models import User


class ThreeMonthsShortVolume(models.Model):
    Date = models.DateField(db_index=True)  # Add an index for faster filtering and querying
    Symbol = models.CharField(max_length=10, db_index=True)  # Index Symbol for efficient queries
    ShortVolume = models.FloatField()
    ShortExemptVolume = models.FloatField()
    TotalVolume = models.FloatField()
    Market = models.CharField(max_length=50, db_index=True)  # Index Market for filtering
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)  # Index creation timestamp
    updated_at = models.DateTimeField(auto_now=True, db_index=True)      # Index update timestamp

    def __str__(self):
        return f"{self.Date} - {self.Symbol} - {self.Market}"


class ThreeMonthsRegSHO(models.Model):
    Date = models.DateField(db_index=True)  # Add an index for faster filtering and querying
    Symbol = models.CharField(max_length=20, db_index=True)  # Index Symbol for efficient queries
    security_name = models.CharField(max_length=255, blank=True, null=True)
    market_category = models.CharField(max_length=1, blank=True, null=True, db_index=True)  # Index market_category
    reg_sho_threshold_flag = models.CharField(max_length=1, blank=True, null=True, db_index=True)  # Index reg_sho_threshold_flag
    rule_3210 = models.CharField(max_length=1, blank=True, null=True)
    filler = models.TextField(blank=True, null=True)  # No index needed for large text fields
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)  # Index creation timestamp
    updated_at = models.DateTimeField(auto_now=True, db_index=True)      # Index update timestamp

    def __str__(self):
        return f"{self.Date} - {self.Symbol} - {self.security_name}"







from django.db import models

class Symbol(models.Model):
    """Model to represent a unique stock symbol."""
    symbol = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.symbol

class SECData(models.Model):
    """Model to store SEC filings related to each stock symbol."""
    id = models.AutoField(primary_key=True)
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name='filings')
    form_type = models.CharField(max_length=50)
    form_description = models.TextField()
    filing_date = models.DateField(null=True)
    #report_date = models.DateField(null=True, blank=True)
    filing_href = models.URLField(null=True, blank=True)  # Allow null values here
    document_url = models.URLField(null=True, blank=True)

    def __str__(self):
        return f"{self.symbol.symbol} - {self.form_type} ({self.filing_date})"




'''
class WatchList(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.PositiveIntegerField(default=0)  # New field for ordering

    class Meta:
        ordering = ['order']  # Set the default ordering by 'order' field

    def __str__(self):
        return self.name
'''
def get_default_user():
    #return 1  # Return the user ID directly if you know it exists, or use the commented-out approach below 
    return User.objects.get(id=1)  # Set a default user, or add logic to pick one

def get_default_superuser():
    # Retrieve the first superuser
    try:
        return User.objects.filter(is_superuser=True).first()
    except User.DoesNotExist:
        # Handle the case where no superuser exists (raise an error or return None)
        return None
'''
class WatchList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, default=get_default_superuser)  # Dynamic default
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name
    
class WatchListSymbol(models.Model):
    watch_list = models.ForeignKey(WatchList, on_delete=models.CASCADE, related_name='symbols')
    symbol = models.CharField(max_length=10)

    def __str__(self):
        return self.symbol
'''

class WatchList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, default=get_default_superuser, db_index=True)  # Add db_index to ForeignKey
    name = models.CharField(max_length=255, db_index=True)  # Index for faster querying
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)  # Index for creation timestamp
    updated_at = models.DateTimeField(auto_now=True, db_index=True)      # Index for update timestamp
    order = models.PositiveIntegerField(default=0, db_index=True)        # Index for sorting and unique constraint

    class Meta:
        ordering = ['user', 'order']  # Ordering by user and then order
        unique_together = ('user', 'order')  # Ensure order is unique for a user

    def save(self, *args, **kwargs):
        # Assign the next available order value for the user if the order is 0
        if self.order == 0:
            max_order = WatchList.objects.filter(user=self.user).aggregate(models.Max('order'))['order__max']
            self.order = (max_order or 0) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class WatchListSymbol(models.Model):
    watch_list = models.ForeignKey(WatchList, on_delete=models.CASCADE, related_name='symbols', db_index=True)  # Add db_index to ForeignKey
    symbol = models.CharField(max_length=10, db_index=True)  # Index for faster querying
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)  # Index for creation timestamp
    updated_at = models.DateTimeField(auto_now=True, db_index=True)      # Index for update timestamp

    def __str__(self):
        return self.symbol

from django.db import models


class StockSymbolData(models.Model):
    """Model to represent a unique stock symbol."""
    symbol = models.CharField(max_length=10, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)  # Index for creation timestamp
    updated_at = models.DateTimeField(auto_now=True, db_index=True)      # Index for update timestamp

    class Meta:
        ordering = ['symbol']  # Order alphabetically by symbol

    def __str__(self):
        return self.symbol


class StockPriceData(models.Model):
    """Model to represent price data for each stock symbol."""
    stock_symbol = models.ForeignKey(StockSymbolData, on_delete=models.CASCADE, related_name='price_data', db_index=True)
    timestamp = models.DateField(db_index=True)  # Use DateField with index for faster date filtering
    open = models.DecimalField(max_digits=10, decimal_places=2)
    high = models.DecimalField(max_digits=10, decimal_places=2)
    low = models.DecimalField(max_digits=10, decimal_places=2)
    close = models.DecimalField(max_digits=10, decimal_places=2)
    adj_close = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.BigIntegerField()
    ShortVolume = models.FloatField(null=True, blank=True)
    ShortExemptVolume = models.FloatField(null=True, blank=True)
    regSho = models.CharField(max_length=10, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)  # Index for creation timestamp
    updated_at = models.DateTimeField(auto_now=True, db_index=True)      # Index for update timestamp

    class Meta:
        ordering = ['-timestamp']  # Ensure default ordering by timestamp (latest first)

    def __str__(self):
        return f"{self.stock_symbol.symbol} - {self.timestamp}"


class NewsSymbolData(models.Model):
    """Model to represent a unique stock symbol."""
    symbol = models.CharField(max_length=10, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)  # Index for creation timestamp
    updated_at = models.DateTimeField(auto_now=True, db_index=True)      # Index for update timestamp

    class Meta:
        ordering = ['symbol']  # Order alphabetically by symbol

    def __str__(self):
        return self.symbol


class NewsData(models.Model):
    """Model to represent news data for each stock symbol."""
    news_symbol = models.ForeignKey(NewsSymbolData, on_delete=models.CASCADE, related_name='news_data', db_index=True)
    Date = models.DateField(db_index=True)  # Use DateField with index for faster date filtering
    NewsTitle = models.CharField(max_length=255, db_index=True)  # Index for title searches
    NewsLink = models.URLField()
    providerPublishTime = models.DateTimeField(db_index=True)  # Index for publication timestamp
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)  # Index for creation timestamp
    updated_at = models.DateTimeField(auto_now=True, db_index=True)      # Index for update timestamp

    class Meta:
        ordering = ['-Date']  # Ensure default ordering by date (latest first)

    def __str__(self):
        return f"{self.news_symbol.symbol} - {self.NewsTitle} - {self.providerPublishTime}"

    



class StockSymbolInfo(models.Model):
    """Model to represent a unique stock symbol."""
    symbol = models.CharField(max_length=10, unique=True, db_index=True)  # Index for faster querying
    company_name = models.CharField(max_length=100, unique=True, db_index=True)  # Index for faster querying
    custom_text = models.TextField(null=True, blank=True)

    # Additional fields
    volume = models.FloatField(null=True, blank=True)
    averageVolume3months = models.FloatField(null=True, blank=True)
    averageVolume10days = models.FloatField(null=True, blank=True)
    marketCap = models.BigIntegerField(null=True, blank=True)  # Market cap is typically a large number
    fiftyTwoWeekLow = models.FloatField(null=True, blank=True)
    fiftyTwoWeekHigh = models.FloatField(null=True, blank=True)
    fiftyDayAverage = models.FloatField(null=True, blank=True)
    floatShares = models.FloatField(null=True, blank=True)
    sharesOutstanding = models.BigIntegerField(null=True, blank=True)
    sharesShort = models.BigIntegerField(null=True, blank=True)
    sharesShortPriorMonth = models.BigIntegerField(null=True, blank=True)
    sharesShortPreviousMonthDate = models.DateField(null=True, blank=True, db_index=True)  # Allow null
    dateShortInterest = models.DateField(null=True, blank=True, db_index=True)  # Allow null
    shortPercentOfFloat = models.FloatField(null=True, blank=True)
    heldPercentInsiders = models.FloatField(null=True, blank=True)
    heldPercentInstitutions = models.FloatField(null=True, blank=True)
    lastSplitFactor = models.FloatField(null=True, blank=True)
    lastSplitDate = models.DateField(null=True, blank=True, db_index=True)  # Allow null
    total_revenue = models.BigIntegerField(null=True, blank=True)
    net_income = models.BigIntegerField(null=True, blank=True)
    total_assets = models.BigIntegerField(null=True, blank=True)
    total_liabilities = models.BigIntegerField(null=True, blank=True)
    total_equity = models.BigIntegerField(null=True, blank=True)

    # Timestamp fields
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)  # Index for creation timestamp
    updated_at = models.DateTimeField(auto_now=True, db_index=True)      # Index for update timestamp

    class Meta:
        ordering = ['symbol']  # Order alphabetically by symbol

    def __str__(self):
        return self.symbol


class DayStockSymbolInfo(models.Model):
    """Model to represent daily stock information."""
    symbol = models.CharField(max_length=10, unique=True, db_index=True)  # Index for faster querying
    company_name = models.CharField(max_length=100,  blank=True, db_index=True)  # Index for faster querying
    # Additional fields
    previousClose = models.FloatField(null=True, blank=True)
    open = models.FloatField(null=True, blank=True)
    currentPrice = models.FloatField(null=True, blank=True)
    dayLow = models.FloatField(null=True, blank=True)
    dayHigh = models.FloatField(null=True, blank=True)
    volume = models.FloatField(null=True, blank=True)
    averageVolume3months = models.FloatField(null=True, blank=True)
    averageVolume10days = models.FloatField(null=True, blank=True)
    marketCap = models.BigIntegerField(null=True, blank=True)  # Market cap is typically a large number

    # Timestamp fields
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)  # Index for creation timestamp
    updated_at = models.DateTimeField(auto_now=True, db_index=True)      # Index for update timestamp

    class Meta:
        ordering = ['symbol']  # Order alphabetically by symbol

    def __str__(self):
        return self.symbol


from django.db import models
from datetime import date

class TickerSplit(models.Model):
    date = models.DateField()
    symbol = models.CharField(max_length=20)
    name = models.CharField(max_length=255)
    sector = models.CharField(max_length=255,blank=True, null=True)
    ratio = models.CharField(max_length=20)

    def is_past(self):
        return self.date < date.today()

    def is_today_or_future(self):
        return self.date >= date.today()

    def __str__(self):
        return f"{self.symbol} - {self.date}"


 
from django.contrib.auth.models import User
from django.db import models
from datetime import date

class BuyNSell(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('B', 'B'),  
        ('S', 'S'),  
        ('O', 'O'), 
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Associate transaction with a user
    date = models.DateField(default=date.today)
    symbol = models.CharField(max_length=20)
    name = models.CharField(max_length=255, default='Unknown Name')
    sector = models.CharField(max_length=255,blank=True, null=True)
    quantity = models.PositiveIntegerField(blank=True, null=True)
    fill_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    transaction_type = models.CharField(max_length=1, choices=TRANSACTION_TYPE_CHOICES)
    order_id = models.CharField(max_length=50, blank=True, null=True)  # New field for unique order ID


    def __str__(self):
        return f"{self.symbol} ({self.transaction_type})"

class EarningsData(models.Model):
    EVENT_CHOICES = [
        ('Q1', 'Q1'),
        ('Q2', 'Q2'),
        ('Q3', 'Q3'),
        ('Q4', 'Q4'),
        ('Others', 'Others'),
    ]
    TIME_CHOICES = [
        ('AMC', 'AMC'),
        ('BMO', 'BMO'),
        ('DMT', 'DMT'),
        ('Others', 'Others'),
    ]

    symbol = models.CharField(max_length=10, unique=True, db_index=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    
    # --- Upcoming / Slot 1 ---
    earnings_date_1 = models.DateField(null=True, blank=True, db_index=True)
    event_name_1 = models.CharField(max_length=20, choices=EVENT_CHOICES, default='Others')
    eps_estimate_1 = models.FloatField(null=True, blank=True)
    reported_eps_1 = models.FloatField(null=True, blank=True)
    revenue_estimate_avg_1 = models.FloatField(null=True, blank=True)
    surprise_pct_1 = models.FloatField(null=True, blank=True)
    earning_call_time_1 = models.CharField(max_length=20, choices=TIME_CHOICES, default='Others')

    # --- Historical 1 / Slot 2 ---
    earnings_date_2 = models.DateField(null=True, blank=True)
    event_name_2 = models.CharField(max_length=20, choices=EVENT_CHOICES, default='Others')
    eps_estimate_2 = models.FloatField(null=True, blank=True)
    reported_eps_2 = models.FloatField(null=True, blank=True)
    revenue_estimate_avg_2 = models.FloatField(null=True, blank=True)
    surprise_pct_2 = models.FloatField(null=True, blank=True)
    earning_call_time_2 = models.CharField(max_length=20, choices=TIME_CHOICES, default='Others')

    # --- Historical 2 / Slot 3 ---
    earnings_date_3 = models.DateField(null=True, blank=True)
    event_name_3 = models.CharField(max_length=20, choices=EVENT_CHOICES, default='Others')
    eps_estimate_3 = models.FloatField(null=True, blank=True)
    reported_eps_3 = models.FloatField(null=True, blank=True)
    revenue_estimate_avg_3 = models.FloatField(null=True, blank=True)
    surprise_pct_3 = models.FloatField(null=True, blank=True)
    earning_call_time_3 = models.CharField(max_length=20, choices=TIME_CHOICES, default='Others')

    # --- Historical 3 / Slot 4 ---
    earnings_date_4 = models.DateField(null=True, blank=True)
    event_name_4 = models.CharField(max_length=20, choices=EVENT_CHOICES, default='Others')
    eps_estimate_4 = models.FloatField(null=True, blank=True)
    reported_eps_4 = models.FloatField(null=True, blank=True)
    revenue_estimate_avg_4 = models.FloatField(null=True, blank=True)
    surprise_pct_4 = models.FloatField(null=True, blank=True)
    earning_call_time_4 = models.CharField(max_length=20, choices=TIME_CHOICES, default='Others')
    
    # Extra General Metrics
    volume = models.BigIntegerField(null=True, blank=True)
    averageVolume10days = models.BigIntegerField(null=True, blank=True)
    averageVolume3months = models.BigIntegerField(null=True, blank=True)
    marketCap = models.BigIntegerField(null=True, blank=True)
    fiftyDayAverage = models.FloatField(null=True, blank=True)
    fiftyTwoWeekLow = models.FloatField(null=True, blank=True)
    fiftyTwoWeekHigh = models.FloatField(null=True, blank=True)
    sharesOutstanding = models.BigIntegerField(null=True, blank=True)
    stock_index = models.CharField(max_length=50, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Earnings Data"
        verbose_name_plural = "Earnings Data"
        ordering = ['symbol']

    def __str__(self):
        return f"{self.symbol} Earnings Info"

class SP500Ticker(models.Model):
    symbol = models.CharField(max_length=10, unique=True, db_index=True)

    class Meta:
        ordering = ['symbol']
        verbose_name = "S&P 500 Ticker"
        verbose_name_plural = "S&P 500 Tickers"

    def __str__(self):
        return self.symbol