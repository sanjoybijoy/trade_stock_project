from django.urls import path
from api import views
from api import stock_ibkr_charts
urlpatterns = [
    path("notes/", views.NoteListCreate.as_view(), name="note-list"),
    path("notes/delete/<int:pk>/", views.NoteDelete.as_view(), name="delete-note"),
    path('stocks-info-data/', views.StockInfoDataView.as_view(), name='stocks-info-data'),
    path('stocks-info-watchlist-data/', views.StockInfoWatchListDataView.as_view(), name='stocks-info-watchlist-data'),
    # WatchList endpoints
    path('watchlists/', views.WatchListViewSet.as_view({'get': 'list', 'post': 'create'}), name='watchlist-list'),
    path('watchlists/<int:pk>/', views.WatchListViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='watchlist-detail'),
    path('watchlists/<int:pk>/add-symbol/', views.WatchListViewSet.as_view({'post': 'add_symbol'}), name='watchlist-add-symbol'),
    path('watchlists/<int:pk>/delete-symbol/', views.WatchListViewSet.as_view({'delete': 'delete_symbol'}), name='watchlist-delete-symbol'),

    path('buy-sell/', views.BuySellListCreateView.as_view(), name='buy_sell_list_create'),
    path('buy-sell/<int:pk>/', views.BuySellDeleteView.as_view(), name='delete_transaction'),
    path('get_order_ids/', views.GetOrderIdsView.as_view(), name='get_order_ids'),

    path('ticker-splits/', views.TickerSplitListView.as_view(), name='ticker_splits_list'),
    path('ticker-splits/<int:pk>/', views.TickerSplitDeleteView.as_view(), name='ticker_split_delete'),
    path("reg-sho-symbols/", views.RegShoSymbolsAPIView.as_view(), name="reg_sho_symbols_api"),   
    path('watchlists/sidebar/', views.WatchListViewSidebarSet.as_view({'get': 'list'}), name='get_watchlists'),
    # Stock Daily Info  
    path('stocks-daily-info-data/', views.StockDailyInfoDataView.as_view(), name='stocks-daily-info-data'),
    path('daily-info/watchlist/', views.StockDailyInfoWatchListDataView.as_view(), name='stocks-daily-info-watchlist-data'),
    path('watchlist-screener/', views.WatchlistScreenerAPIView.as_view(), name='watchlist-screener'),
    path('watchlist-news/', views.WatchlistNewsAPIView.as_view(), name='watchlist-news'),


    path('get_chart_data_from_database/', views.get_chart_data_from_database, name='get_chart_data_from_database'),
    path('get_chart_data_from_database/watchlist/', views.get_chart_watchlist_data_from_database, name='get_historical_watchlist_data'),
    
    path('get_historical_data/', stock_ibkr_charts.get_historical_data, name='get_historical_data'),
    
    #path('live-data/', stock_ibkr_charts.getLiveData, name='stream_live_data'),
    path('live-data/', stock_ibkr_charts.LiveMarketDataAPIView.as_view(), name='stream_live_data'),
    #path('live-bars/', stock_ibkr_charts.LiveBarView.as_view(), name='stream_live_bar'),
]

