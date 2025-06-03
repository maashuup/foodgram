import django_filters
from django_filters.rest_framework import FilterSet

from .models import Ingredient, Recipe


class IngredientFilter(FilterSet):
    """Фильтр для ингредиентов – поиск по началу названия."""

    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ['name']


class RecipeFilter(FilterSet):
    author = django_filters.NumberFilter(field_name='author__id')
    tags = django_filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = django_filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = django_filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none() if value else queryset
        return (
            queryset.filter(favorite_recipes__user=user)
            if value
            else queryset.exclude(favorite_recipes__user=user)
        )

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none() if value else queryset
        return (
            queryset.filter(shopping_cart__user=user)
            if value
            else queryset.exclude(shopping_cart__user=user)
        )

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']
