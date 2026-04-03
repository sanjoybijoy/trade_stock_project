from django.contrib import admin
from django.contrib.admin import DateFieldListFilter
from .models import ThreeMonthsShortVolume, ThreeMonthsRegSHO

# Action to delete all records
def delete_all(modeladmin, request, queryset):
    modeladmin.model.objects.all().delete()
    modeladmin.message_user(request, "All records have been deleted.")

delete_all.short_description = "Delete All"

# Action to delete records for selected dates
def delete_selected_dates(modeladmin, request, queryset):
    dates = queryset.values_list('Date', flat=True).distinct()
    modeladmin.model.objects.filter(Date__in=dates).delete()
    message_bit = ", ".join([str(date) for date in dates])
    modeladmin.message_user(request, f"All records for the following dates have been deleted: {message_bit}")

delete_selected_dates.short_description = "Delete Selected Dates"

# Admin class for ThreeMonthsShortVolume
class ThreeMonthsShortVolumeAdmin(admin.ModelAdmin):
    list_display = ['Date', 'Symbol', 'ShortVolume', 'ShortExemptVolume', 'TotalVolume', 'Market', 'created_at', 'updated_at']
    search_fields = ['Symbol', 'Market']
    date_hierarchy = 'Date'
    list_filter = [('Date', DateFieldListFilter)]
    actions = [delete_selected_dates, delete_all]

# Registering ThreeMonthsShortVolume model
admin.site.register(ThreeMonthsShortVolume, ThreeMonthsShortVolumeAdmin)

# Admin class for ThreeMonthsRegSHO
@admin.register(ThreeMonthsRegSHO)
class ThreeMonthsRegSHOAdmin(admin.ModelAdmin):
    list_display = [
        'Date', 
        'Symbol', 
        'security_name', 
        'market_category', 
        'reg_sho_threshold_flag', 
        'rule_3210', 
        'created_at', 
        'updated_at'
    ]
    search_fields = ['Symbol', 'security_name', 'market_category']
    date_hierarchy = 'Date'
    list_filter = [('Date', DateFieldListFilter)]
    actions = [delete_selected_dates, delete_all]



# admin.py
from django.contrib import admin
from .models import Symbol, SECData

class SECDataInline(admin.TabularInline):
    model = SECData
    extra = 1
    #can_delete = True  # Enable deletion for each individual SECData entry
    readonly_fields = ('id',)  # Make the ID field readonly, as it should not be editable
    #fields = ('id', 'form_type', 'form_description', 'filing_date', 'report_date', 'filing_href', 'document_url')  # Include 'id' in the displayed fields
    fields = ('id', 'form_type', 'form_description', 'filing_date', 'filing_href', 'document_url')  # Include 'id' in the displayed fields

class SymbolAdmin(admin.ModelAdmin):
    inlines = [SECDataInline]
    list_display = ('symbol',)
    search_fields = ('symbol',)

admin.site.register(Symbol, SymbolAdmin)

from .models import StockSymbolData, StockPriceData

class StockPriceDataInline(admin.TabularInline):
    """Inline configuration for StockPriceData."""
    model = StockPriceData
    extra = 1  # Number of empty rows to display for adding new entries
    fields = ('timestamp', 'open', 'high', 'low', 'close', 'adj_close', 'volume', 'ShortVolume', 'ShortExemptVolume','regSho')

    #ordering = ['timestamp']  # Explicitly order by timestamp
    #readonly_fields = ('timestamp',)  # Example: making `timestamp` readonly


from django.db.models import Min, Max

class StockSymbolDataAdmin(admin.ModelAdmin):
    """Admin configuration for StockSymbolData with inline StockPriceData."""
    
    list_display = ('symbol', 'total_price_data_entries', 'beginning_date', 'latest_date','created_at', 'updated_at')  # Add the new methods
    
    search_fields = ('symbol',)
    inlines = [StockPriceDataInline]
    
    actions = ['delete_all']

    def delete_all(self, request, queryset):
        queryset.model.objects.all().delete()
        self.message_user(request, "All records have been deleted.")

    def total_price_data_entries(self, obj):
        """Count the total number of StockPriceData entries for a given StockSymbolData symbol."""
        return obj.price_data.count()
    total_price_data_entries.short_description = 'Total Price'

    def beginning_date(self, obj):
        """Get the earliest date (beginning date) of the related StockPriceData entries."""
        # Using `aggregate` to get the minimum timestamp
        min_date = obj.price_data.aggregate(Min('timestamp'))['timestamp__min']
        return min_date
    beginning_date.short_description = 'Beginning Date'

    def latest_date(self, obj):
        """Get the latest date (most recent date) of the related StockPriceData entries."""
        # Using `aggregate` to get the maximum timestamp
        max_date = obj.price_data.aggregate(Max('timestamp'))['timestamp__max']
        return max_date
    latest_date.short_description = 'Latest Date'

# Register the admin class
admin.site.register(StockSymbolData, StockSymbolDataAdmin)



from .models import NewsSymbolData, NewsData

class NewsDataInline(admin.TabularInline):
    """Inline configuration for NewsData under a stock symbol."""
    model = NewsData
    extra = 1  # Number of empty rows to display for adding new entries
    fields = ('Date', 'NewsTitle', 'NewsLink', 'providerPublishTime')
    # Optionally, you can make some fields readonly:
    # readonly_fields = ('providerPublishTime',)

class NewsSymbolDataAdmin(admin.ModelAdmin):
    """Admin configuration for NewsSymbolData with inline NewsData."""
    
    list_display = ('symbol', 'total_news_entries', 'beginning_date', 'latest_date','created_at', 'updated_at')  # Add the new methods
    
    search_fields = ('symbol',)
    inlines = [NewsDataInline]
    actions = ['delete_all']

    def delete_all(self, request, queryset):
        queryset.model.objects.all().delete()
        self.message_user(request, "All records have been deleted.")

    def total_news_entries(self, obj):
        """Count the total number of NewsData entries for a given NewsSymbolData symbol."""
        return obj.news_data.count()
    total_news_entries.short_description = 'Total News '

    def beginning_date(self, obj):
        """Get the earliest date (beginning date) of the related NewsData entries."""
        # Using `aggregate` to get the minimum Date
        min_date = obj.news_data.aggregate(Min('Date'))['Date__min']
        return min_date
    beginning_date.short_description = 'Beginning Date'

    def latest_date(self, obj):
        """Get the latest date (most recent date) of the related NewsData entries."""
        # Using `aggregate` to get the maximum Date
        max_date = obj.news_data.aggregate(Max('Date'))['Date__max']
        return max_date
    latest_date.short_description = 'Latest Date'

# Register the admin class
admin.site.register(NewsSymbolData, NewsSymbolDataAdmin)

from django.contrib import admin
from django.urls import path, reverse
from django.shortcuts import redirect
from django.utils.html import format_html
from django.views.decorators.csrf import csrf_exempt
from .models import WatchList, WatchListSymbol

class WatchListSymbolInline(admin.TabularInline):
    model = WatchListSymbol
    extra = 1

@admin.register(WatchList)
class WatchListAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at','updated_at', 'user', 'move_up', 'move_down')
    search_fields = ('name', 'user__username')
    list_filter = ('user',)
    inlines = [WatchListSymbolInline]

    def get_queryset(self, request):
        """Ensure that superusers see all watchlists, while other users see only their own."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:watchlist_id>/move-up/', self.admin_site.admin_view(self.move_up_view), name='watchlist-move-up'),
            path('<int:watchlist_id>/move-down/', self.admin_site.admin_view(self.move_down_view), name='watchlist-move-down'),
        ]
        return custom_urls + urls

    @csrf_exempt
    def move_up_view(self, request, watchlist_id):
        watchlist = WatchList.objects.get(id=watchlist_id)
        if request.user != watchlist.user and not request.user.is_superuser:
            return redirect(request.META.get('HTTP_REFERER'))  # Prevent unauthorized changes

        prev_watchlist = WatchList.objects.filter(
            user=watchlist.user, order__lt=watchlist.order
        ).order_by('-order').first()

        if prev_watchlist:
            watchlist.order, prev_watchlist.order = prev_watchlist.order, watchlist.order
            watchlist.save()
            prev_watchlist.save()

        return redirect(request.META.get('HTTP_REFERER'))

    @csrf_exempt
    def move_down_view(self, request, watchlist_id):
        watchlist = WatchList.objects.get(id=watchlist_id)
        if request.user != watchlist.user and not request.user.is_superuser:
            return redirect(request.META.get('HTTP_REFERER'))  # Prevent unauthorized changes

        next_watchlist = WatchList.objects.filter(
            user=watchlist.user, order__gt=watchlist.order
        ).order_by('order').first()

        if next_watchlist:
            watchlist.order, next_watchlist.order = next_watchlist.order, watchlist.order
            watchlist.save()
            next_watchlist.save()

        return redirect(request.META.get('HTTP_REFERER'))

    def move_up(self, obj):
        return format_html(
            '<a class="button" href="{}">Move Up</a>',
            reverse('admin:watchlist-move-up', args=[obj.id])
        )

    def move_down(self, obj):
        return format_html(
            '<a class="button" href="{}">Move Down</a>',
            reverse('admin:watchlist-move-down', args=[obj.id])
        )

    move_up.short_description = 'Move Up'
    move_down.short_description = 'Move Down'

@admin.register(WatchListSymbol)
class WatchListSymbolAdmin(admin.ModelAdmin):
    list_display = ('symbol','created_at','updated_at', 'watch_list')
    search_fields = ('symbol',)
    list_filter = ('watch_list',)


from django.contrib import admin
from .models import StockSymbolInfo

class StockSymbolInfoAdmin(admin.ModelAdmin):
    # Fields to display in the list view
    list_display = (
        'symbol', 'company_name','created_at', 'updated_at','volume', 'averageVolume3months', 'marketCap', 
        'fiftyTwoWeekLow', 'fiftyTwoWeekHigh', 'fiftyDayAverage', 'floatShares', 
        'sharesOutstanding', 'sharesShort', 'sharesShortPriorMonth', 
        'sharesShortPreviousMonthDate', 'dateShortInterest', 'shortPercentOfFloat',
        'heldPercentInsiders', 'heldPercentInstitutions', 'lastSplitFactor', 
        'lastSplitDate', 'total_revenue', 'net_income', 'total_assets', 
        'total_liabilities', 'total_equity'
    )
    
    # Fields to include in the search box in the list view
    search_fields = ('symbol', 'company_name', 'custom_text')
    
    # List filter options to narrow down the displayed records
    #list_filter = ('lastSplitDate', 'dateShortInterest', 'sharesShortPreviousMonthDate')
    
    # Customize how the model is displayed in the detail page
    fieldsets = (
        (None, {
            'fields': ('symbol', 'company_name', 'custom_text')
        }),
        ('Stock Information', {
            'fields': (
                'volume','averageVolume3months', 'averageVolume10days', 'marketCap', 
                'fiftyTwoWeekLow', 'fiftyTwoWeekHigh', 'fiftyDayAverage', 
                'floatShares', 'sharesOutstanding', 'sharesShort', 
                'sharesShortPriorMonth', 'sharesShortPreviousMonthDate', 
                'dateShortInterest', 'shortPercentOfFloat', 
                'heldPercentInsiders', 'heldPercentInstitutions', 
                'lastSplitFactor', 'lastSplitDate', 'total_revenue', 
                'net_income', 'total_assets', 'total_liabilities', 
                'total_equity'
            )
        }),
    )
    
    # Optionally, ordering of records in the list view
    ordering = ('symbol',)

# Register the model with the admin site
admin.site.register(StockSymbolInfo, StockSymbolInfoAdmin)


from .models import DayStockSymbolInfo

class DayStockSymbolInfoAdmin(admin.ModelAdmin):
    # Fields to display in the list view
    list_display = (
        'symbol','company_name','created_at', 'updated_at', 'previousClose', 'open', 'currentPrice', 'dayLow', 
        'dayHigh', 'volume','averageVolume10days', 'averageVolume3months',  'marketCap'
    )

    # Fields to include in the search box in the list view
    search_fields = ('symbol',)

    # Customize how the model is displayed in the detail page
    fieldsets = (
        (None, {
            'fields': ('symbol','company_name')
        }),
        ('Stock Information', {
            'fields': (
                'previousClose', 'open', 'currentPrice', 'dayLow', 'dayHigh', 
                'volume','averageVolume10days', 'averageVolume3months',  'marketCap'
            )
        }),
    )

    # Optionally, ordering of records in the list view
    ordering = ('symbol',)

# Register the model with the admin site
admin.site.register(DayStockSymbolInfo, DayStockSymbolInfoAdmin)



from .models import TickerSplit
from datetime import date 

class TickerSplitAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name','sector', 'date', 'ratio', 'is_past', 'is_today_or_future')
    list_filter = ('date',)
    search_fields = ('symbol', 'name')
    ordering = ('-date',)  # Orders by date in descending order by default

    def is_past(self, obj):
        return obj.date < date.today()
    is_past.boolean = True  # Displays a checkmark in the admin list
    is_past.short_description = "Is Past"

    def is_today_or_future(self, obj):
        return obj.date >= date.today()
    is_today_or_future.boolean = True  # Displays a checkmark in the admin list
    is_today_or_future.short_description = "Is Today/Future"

admin.site.register(TickerSplit, TickerSplitAdmin)

from django.contrib import admin
from .models import BuyNSell

@admin.register(BuyNSell)
class BuyNSellAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'date', 'symbol', 'name','sector', 'quantity', 'fill_price','order_id', 'transaction_type')
    list_filter = ('user', 'transaction_type', 'date')
    search_fields = ('symbol', 'name', 'user__username')
    ordering = ('-date',)
    autocomplete_fields = ['user']  # Enables a search box for selecting users

from .models import EarningsData

@admin.register(EarningsData)
class EarningsDataAdmin(admin.ModelAdmin):
    list_display = (
        'symbol', 'company_name', 'earnings_date_1', 'earnings_date_2', 
        'marketCap', 'volume'
    )
    search_fields = ('symbol', 'company_name')
    ordering = ('symbol',)

    fieldsets = (
        (None, {
            'fields': ('symbol', 'company_name')
        }),
        ('Upcoming Earnings (Slot 1)', {
            'fields': (
                'earnings_date_1', 'event_name_1', 'earning_call_time_1',
                'eps_estimate_1', 'reported_eps_1', 'revenue_estimate_avg_1', 'surprise_pct_1'
            )
        }),
        ('Historical Earnings 1 (Slot 2)', {
            'fields': (
                'earnings_date_2', 'event_name_2', 'earning_call_time_2',
                'eps_estimate_2', 'reported_eps_2', 'revenue_estimate_avg_2', 'surprise_pct_2'
            )
        }),
        ('Historical Earnings 2 (Slot 3)', {
            'fields': (
                'earnings_date_3', 'event_name_3', 'earning_call_time_3',
                'eps_estimate_3', 'reported_eps_3', 'revenue_estimate_avg_3', 'surprise_pct_3'
            )
        }),
        ('Historical Earnings 3 (Slot 4)', {
            'fields': (
                'earnings_date_4', 'event_name_4', 'earning_call_time_4',
                'eps_estimate_4', 'reported_eps_4', 'revenue_estimate_avg_4', 'surprise_pct_4'
            )
        }),
        ('General Stock Metrics', {
            'fields': (
                'volume', 'averageVolume10days', 'averageVolume3months',
                'marketCap', 'fiftyDayAverage', 'fiftyTwoWeekLow',
                'fiftyTwoWeekHigh', 'sharesOutstanding','stock_index'
            )
        }),
    )

from .models import SP500Ticker

class SP500TickerAdmin(admin.ModelAdmin):
    list_display = ('symbol',)
    search_fields = ('symbol',)
    ordering = ('symbol',)

admin.site.register(SP500Ticker, SP500TickerAdmin)
