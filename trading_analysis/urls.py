from django.contrib import admin
from django.urls import path, include   
from analysis import views
from django.contrib.auth import views as auth_views

from api.views import CreateUserView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from analysis.stock_day_info import (
    stock_day_info_watchList_view,
    update_day_stock_info,
    stock_day_info_most_active_view,
    stock_day_info_tranding_view,
    stock_day_info_top_gainers_view,
    stock_day_info_top_losers_view,
    stock_day_info_top_SV_view,
    stock_day_info_reg_show_view,
    stock_day_info_reg_sho_remove_tickers_view,
    stock_day_info_watchlists_tickers_view,
    stock_day_info_splits_all_tickers,
    stock_day_info_last_splits_tickers,
    stock_day_info_upcoming_splits_tickers,
    stock_day_info_last_splits_healthcare_tickers,
    stock_day_info_all_bought_tickers,
    stock_day_info_healthcare_bought_tickers,
    stock_day_info_watchList_info_homepage_view
)
from analysis.stock_data_db_tickers_load import(
    view_test_tickers_load
)
from analysis.stock_data_update_view import(
    update_watchlist_news_all_tickers_view,
    update_watchlist_all_tickers_day_stock_info_view,
    update_watchlist_all_tickers_stock_info_view,
    update_and_merge_missing_short_volume_data_view,
    update_watchlist_tickers_stock_data_view,

    update_y_all_news_view,
    update_y_all_day_stock_info_view,
    update_y_all_stock_info_view,
    update_and_merge_y_all_missing_short_volume_data_view,
    update_y_all_stock_data_view,

    update_regsho_SV_news_view,
    update_regsho_SV_day_stock_info_view,
    update_regsho_SV_stock_info_view,
    update_and_merge_regsho_SV_missing_short_volume_data_view,
    update_regsho_SV_stock_data_view,

    update_all_splits_tickers_news_view,
    update_all_splits_tickers_day_stock_info_view,
    update_all_splits_tickers_stock_info_view,
    update_and_merge_all_splits_tickers_missing_short_volume_data_view,
    update_all_splits_tickers_stock_data_view,

    update_current_all_tickers_news_view,
    update_current_all_tickers_day_stock_info_view,
    update_current_all_tickers_stock_info_view,
    update_and_merge_current_all_tickers_missing_short_volume_data_view,
    update_current_all_tickers_stock_data_view,

    update_user_watchlist_tickers_news_view,
    update_user_current_all_tickers_day_stock_info_view,
    update_user_current_all_tickers_stock_info_view,
    update_and_merge_user_current_all_tickers_missing_short_volume_data_view,
    update_user_current_all_tickers_stock_data_view,

    update_custom_tickers_news_view,
    update_custom_tickers_tickers_day_stock_info_view,
    update_custom_tickers_tickers_stock_info_view,
    update_custom_tickers_tickers_stock_data_view,

    missing_ticker_info_in_stock_data_view,
    earnings_update_view,
    update_snp_500_tickers_view

)

from api.views import UserProfileView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('charts/', views.charts_page, name='charts_page'),
    path('daily-info/', views.daily_info_page, name='daily_info_page'),
    
    path('three-months-short-volume/<str:start_date_str>/', views.display_three_months_short_volume_data, name='three_months_short_volume'),
    path('upload-short-volume-file/', views.upload_short_volume_file, name='upload_file'),
    path('three-months-reg-sho/<str:start_date_str>/', views.display_three_months_reg_sho_data, name='display_three_months_reg_sho'),
    

    path('view-test/', views.view_test, name='view_test'),

    
    path('view-symbol-data/', views.view_test_symbol, name='view_test_symbol'),
  

    path('all-symbols/', views.find_all_symbols, name='find-all-symbols'),

    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='registration/logged_out.html'), name='logout'),


    path('update-watchlist-regsho-stock-data/', views.update_watchlist_regsho_symbol_stock_data_view, name='update_watchlist_regsho_symbol_stock_data'),
    path('update-watchlist-regsho-news-data/', views.update_watchlist_news_data_view, name='update_watchlist_regsho_news_data'),
    path('update-data-page/', views.update_data_page, name='update_data_page'),

    #path('view-stock-data/', views.view_data_for_symbols, name='view_data_for_symbols'),
    path('view-stock-charts/', views.view_stock_charts, name='view_stock_charts'),

    path('show-tickers/', views.show_tickers, name='show_tickers'),

    path('show-watchlist-regsho-tickers/', views.show_agregate_watchlist_regSho_tickers, name='show_agregate_watchlist_regSho_tickers'),
    


    path('get-chart-data/', views.get_chart_data, name='get_chart_data'),
    path('get-chart-data-db/', views.get_chart_data_db, name='get_chart_data_db'),

    path('update-watchlist-regsho-stock-info/', views.update_stock_info, name='update_stock_info'),

    path('update-missing-short-volume/', views.update_missing_short_volume_data, name='update_missing_short_volume_data'),

   
    path('missing-tickers/', views.missing_ticker_in_stock_data_view, name='missing_ticker_in_stock_data'),
    path('show-watchlist-regsho-missing-in-stock-data-tickers/', views.show_regsho_watchlist_sv_tickers_not_in_stock_symbol_data, name='show_regsho_watchlist_tickers_not_in_stock_symbol_data'),
    
    path('settings/', views.setting_page, name='setting_page'),


    path('get_order_ids/', views.get_order_ids, name='get_order_ids'),

    # Logged-in HOME collapsible nav
    path('home/reg-sho-symbols/', views.reg_sho_symbols_view, name='reg_sho_symbols_data'),
    path('home/manage-watch-list/', views.manage_watch_list, name='manage_watch_list'), 
    path('home/splits/', views.ticker_splits_view, name='ticker_splits_view'),
    path('home/splits/delete/<int:pk>/', views.delete_split, name='delete_split'), 
    path('home/buy-sell/', views.buy_sell_view, name='buy_sell_view'),
    path('home/delete-transaction/<int:pk>/', views.delete_transaction, name='delete_transaction'),
    
    path('home/update-earnings-field-ajax/', views.update_earnings_field_ajax, name='update_earnings_field_ajax'),

    # earnings calendar Collapsible nav
    path('earnings/earnings-calendar/', views.earnings_calendar_view, name='earnings_calendar_view'),
    path('earnings/big-earnings-calendar/', views.big_earnings_calendar_view, name='big_earnings_calendar_view'),
    path('earnings/recent-big-earnings-calendar/', views.recent_big_earnings_calendar_view, name='recent_big_earnings_calendar_view'),
    # watch list info Collapsible nav
    path('watchlist-info/watchlist-news/', views.watchlist_news, name='watchlist_news'),
    path('watchlist-info/watchlist-screener/', views.watchlist_screener, name='watchlist_screener'),
    path('watchlist-info/watchlist-stock-info-view/', views.stock_info_view, name='stock_info_view'),

    # UPDATE DATA Collapsible nav


    # From stock_day_info.py
    path('watchlist-info/watchlist-daily-info-view/', stock_day_info_watchList_info_homepage_view, name='stock_day_info_watchList_info_homepage_view'),

    path('daily-info/stock-daily-info-watchlist-view/', stock_day_info_watchList_view, name='stock_day_info_watchList_view'),
    path('daily-info/update-watchlist-regsho-day-stock-info/', update_day_stock_info, name='update_day_stock_info'),
    
    path('daily-info/top-daily-tickers/stock-daily-info-most-active-view/', stock_day_info_most_active_view, name='stock_day_info_most_active_view'),
    path('daily-info/top-daily-tickers/stock-daily-info-tranding-view/', stock_day_info_tranding_view, name='stock_day_info_tranding_view'),
    path('daily-info/top-daily-tickers/stock-daily-info-top-gainers-view/', stock_day_info_top_gainers_view, name='stock_day_info_top_gainers_view'),
    path('daily-info/top-daily-tickers/stock-daily-info-top-losers-view/', stock_day_info_top_losers_view, name='stock_day_info_top_losers_view'),
    
    path('daily-info/stock-daily-info-top-SV-view/', stock_day_info_top_SV_view, name='stock_day_info_top_SV_view'),
    path('daily-info/stock-daily-info-reg-show-view/', stock_day_info_reg_show_view, name='stock_day_info_reg_show_view'),
    path('daily-info/stock-daily-info-reg-sho-remove-tickers-view/', stock_day_info_reg_sho_remove_tickers_view, name='stock_day_info_reg_sho_remove_tickers_view'),
    path('daily-info/watchlist-daily-info/stock-daily-info-watchlists/<str:watch_list_str>/', stock_day_info_watchlists_tickers_view, name='stock_day_info_watchlists_tickers_view'),

    
    
    path('daily-info/stock-daily-info-splits-all-tickers/', stock_day_info_splits_all_tickers, name='stock_day_info_splits_all_tickers'),
    path('daily-info/stock-daily-info-last-splits-tickers/', stock_day_info_last_splits_tickers, name='stock_day_info_last_splits_tickers'),
    path('daily-info/stock-daily-info-upcoming-splits-tickers/', stock_day_info_upcoming_splits_tickers, name='stock_day_info_upcoming_splits_tickers'),
    path('daily-info/stock-daily-info-last-splits-healthcare-tickers/', stock_day_info_last_splits_healthcare_tickers, name='stock_day_info_last_splits_healthcare_tickers'),
    path('daily-info/stock-daily-info-all-bought-tickers/', stock_day_info_all_bought_tickers, name='stock_day_info_all_bought_tickers'),
    path('daily-info/stock-daily-info-healthcare-bought-tickers/', stock_day_info_healthcare_bought_tickers, name='stock_day_info_healthcare_bought_tickers'),
    
    #Charts
    path('charts/reg-sho-charts/', views.as_of_reg_sho_charts_view, name='as_of_reg_sho_charts_view'),
    path('charts/top-average-short-volume-charts/', views.top_average_short_volume_charts, name='top_average_short_volume_charts'),
    path('charts/reg-sho-removed-charts/', views.reg_sho_remove_list_view, name='reg_sho_remove_list_charts'),

    path('charts/watch-list-charts/<str:watch_list_str>/', views.watch_list_links, name='watch-list-detail'),

    path('charts/top-daily-charts/most-active/', views.y_most_active_view, name='y_most_active_view'),
    path('charts/top-daily-charts/tranding/', views.y_tranding_view, name='y_tranding_view'),
    path('charts/top-daily-charts/gainers/', views.y_top_gainers_view, name='y_top_gainers_view'),
    path('charts/top-daily-charts/losers/', views.y_top_losers_view, name='y_top_losers_view'),
 

    path('charts/last-splits-charts/', views.last_splits_charts_view, name='last_splits_charts_view'),
    path('charts/last-splits-healthcare-sector-charts/', views.last_splits_healthcare_charts_view, name='last_splits_healthcare_charts_view'),
    path('charts/bought-excluding-healthcare-sector-charts/', views.bought_excluding_healthcare_charts_view, name='bought_excluding_healthcare_charts_view'),
    path('charts/bought-healthcare-sector-charts/', views.bought_healthcare_charts_view, name='bought_healthcare_charts_view'),
   
    # view_test_tickers_load
    path('tickers-load/', view_test_tickers_load, name='view_test_tickers_load'),

    # Update-data-page
    # All Data Save and Update
    path('update-data-page/save-stock-data/', views.save_stock_data_view, name='save_stock_data'),
    path('update-data-page/save-news-data/', views.save_and_get_multiple_news_data, name='get_multiple_news_data'),
    path('update-data-page/local-sec-data/', views.fetch_and_save_sec_symbols_list, name='fetch_and_save_sec_symbols_list'),
    path('update-data-page/update-earnings-data/', views.earnings_update_view, name='earnings_update_view'),
 
    # stock_data_update_view.py
    path('update-data-page/update-watchlist-news-all-tickers/', update_watchlist_news_all_tickers_view, name='update_watchlist_news_all_tickers_view'),
    path('update-data-page/update-watchlist-tickers-day-stock-info/', update_watchlist_all_tickers_day_stock_info_view, name='update_watchlist_all_tickers_day_stock_info_view'),
    path('update-data-page/update-watchlist-tickers-stock-info/', update_watchlist_all_tickers_stock_info_view, name='update_watchlist_all_tickers_stock_info_view'),
    path('update-data-page/update-and-merge-missing-short-volume-data/', update_and_merge_missing_short_volume_data_view, name='update_and_merge_missing_short_volume_data_view'),
    path('update-data-page/update-watchlist-tickers-stock-data/', update_watchlist_tickers_stock_data_view, name='update_watchlist_tickers_stock_data_view'),
    
    path('update-data-page/update-y-all-news/', update_y_all_news_view, name='update_y_all_news_view'),
    path('update-data-page/update-y-all-day-stock-info/', update_y_all_day_stock_info_view, name='update_y_all_day_stock_info_view'),
    path('update-data-page/update-y-all-stock-info/', update_y_all_stock_info_view, name='update_y_all_stock_info_view'),
    path('update-data-page/update-and-merge-y-all-missing-short-volume-data/', update_and_merge_y_all_missing_short_volume_data_view, name='update_and_merge_y_all_missing_short_volume_data_view'),
    path('update-data-page/update-y-all-stock-data/', update_y_all_stock_data_view, name='update_y_all_stock_data_view'),
    
    path('update-data-page/update-regsho-SV-news/', update_regsho_SV_news_view, name='update_regsho_SV_news_view'),
    path('update-data-page/update-regsho-SV-day-stock-info/', update_regsho_SV_day_stock_info_view, name='update_regsho_SV_day_stock_info_view'),
    path('update-data-page/update-regsho-SV-stock-info/', update_regsho_SV_stock_info_view, name='update_regsho_SV_stock_info_view'),
    path('update-data-page/update-and-merge-regsho-SV-missing-short-volume-data/', update_and_merge_regsho_SV_missing_short_volume_data_view, name='update_and_merge_regsho_SV_missing_short_volume_data_view'),
    path('update-data-page/update-regsho-SV-stock-data/', update_regsho_SV_stock_data_view, name='update_regsho_SV_stock_data_view'),
    
    path('update-data-page/update-all-splits-tickers-news/', update_all_splits_tickers_news_view, name='update_all_splits_tickers_news_view'),
    path('update-data-page/update-all-splits-tickers-day-stock-info/', update_all_splits_tickers_day_stock_info_view, name='update_all_splits_tickers_day_stock_info_view'),
    path('update-data-page/update-all-splits-tickers-stock-info/', update_all_splits_tickers_stock_info_view, name='update_all_splits_tickers_stock_info_view'),
    path('update-data-page/update-and-merge-all-splits-tickers-missing-short-volume-data/', update_and_merge_all_splits_tickers_missing_short_volume_data_view, name='update_and_merge_all_splits_tickers_missing_short_volume_data_view'),
    path('update-data-page/update-all-splits-tickers-stock-data/', update_all_splits_tickers_stock_data_view, name='update_all_splits_tickers_stock_data_view'),
    
    path('update-data-page/update-current-all-tickers-news/', update_current_all_tickers_news_view, name='update_current_all_tickers_news_view'),
    path('update-data-page/update-current-all-tickers-day-stock-info/', update_current_all_tickers_day_stock_info_view, name='update_current_all_tickers_day_stock_info_view'),
    path('update-data-page/update-current-all-tickers-stock-info/', update_current_all_tickers_stock_info_view, name='update_current_all_tickers_stock_info_view'),
    path('update-data-page/update-and-merge-current-all-tickers-missing-short-volume-data/', update_and_merge_current_all_tickers_missing_short_volume_data_view, name='update_and_merge_current_all_tickers_missing_short_volume_data_view'),
    path('update-data-page/update-current-all-tickers-stock-data/', update_current_all_tickers_stock_data_view, name='update_current_all_tickers_stock_data_view'),
    
    path('update-data-page/update-user-watchlist-tickers-news/', update_user_watchlist_tickers_news_view, name='update_user_watchlist_tickers_news_view'),
    path('update-data-page/update-user-current-all-tickers-day-stock-info/', update_user_current_all_tickers_day_stock_info_view, name='update_user_current_all_tickers_day_stock_info_view'),
    path('update-data-page/update-user-current-all-tickers-stock-info/', update_user_current_all_tickers_stock_info_view, name='update_user_current_all_tickers_stock_info_view'),
    path('update-data-page/update-and-merge-user-current-all-tickers-missing-short-volume-data/', update_and_merge_user_current_all_tickers_missing_short_volume_data_view, name='update_and_merge_user_current_all_tickers_missing_short_volume_data_view'),
    path('update-data-page/update-user-current-all-tickers-stock-data/', update_user_current_all_tickers_stock_data_view, name='update_user_current_all_tickers_stock_data_view'),
    
    path('update-data-page/update-custom-tickers-news/', update_custom_tickers_news_view, name='update_custom_tickers_news_view'),
    path('update-data-page/update-custom-tickers-tickers-day-stock-info/', update_custom_tickers_tickers_day_stock_info_view, name='update_custom_tickers_tickers_day_stock_info_view'),
    path('update-data-page/update-custom-tickers-tickers-stock-info/', update_custom_tickers_tickers_stock_info_view, name='update_custom_tickers_tickers_stock_info_view'),
    path('update-data-page/update-custom-tickers-tickers-stock-data/', update_custom_tickers_tickers_stock_data_view, name='update_custom_tickers_tickers_stock_data_view'),
    
    
    path('update-data-page/missing-ticker-info-in-stock-data/', missing_ticker_info_in_stock_data_view, name='missing_ticker_info_in_stock_data_view'),
    # Update SNP 500 Tickers
    path('update-data-page/update-snp-500-tickers/', update_snp_500_tickers_view, name='update_snp_500_tickers_view'),

    #For Api Usage
    path("api/user/register/", CreateUserView.as_view(), name="register"),
    path("api/token/", TokenObtainPairView.as_view(), name="get_token"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("api-auth/", include("rest_framework.urls")),
    path("api/", include("api.urls")),
    path("api/user/profile/", UserProfileView.as_view(), name="user_profile"),

]
