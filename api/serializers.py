from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Note


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        print(validated_data)
        user = User.objects.create_user(**validated_data)
        return user


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ["id", "title", "content", "created_at", "author"]
        extra_kwargs = {"author": {"read_only": True}}

from rest_framework import serializers
from analysis.models import StockSymbolInfo



class StockInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockSymbolInfo
        fields = '__all__'  # Replace '__all__' with specific fields if needed

from rest_framework import serializers
from analysis.models import WatchList, WatchListSymbol

class WatchListSymbolSerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchListSymbol
        fields = ['id', 'symbol']

class WatchListSerializer(serializers.ModelSerializer):
    symbols = WatchListSymbolSerializer(many=True, read_only=True)

    class Meta:
        model = WatchList
        fields = ['id', 'name', 'symbols']

from rest_framework import serializers
from analysis.models import BuyNSell

class BuySellSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyNSell
        fields = ['id', 'date', 'symbol', 'name', 'sector', 'quantity', 'fill_price', 'transaction_type', 'order_id']


# serializers.py
from rest_framework import serializers
from analysis.models import TickerSplit

class TickerSplitSerializer(serializers.ModelSerializer):
    class Meta:
        model = TickerSplit
        fields = ['id','date', 'symbol', 'ratio', 'name', 'sector']
        extra_kwargs = {
            'name': {'required': False, 'allow_blank': True},  # Allow blank strings
            'sector': {'required': False, 'allow_blank': True},  # Allow blank strings if needed
        }

from analysis.models import DayStockSymbolInfo
class StockDailyInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DayStockSymbolInfo
        fields = '__all__'  # Replace '__all__' with specific fields if needed
