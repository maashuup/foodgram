import django_filters
from django_filters.rest_framework import FilterSet

from recipes.models import Ingredient, Recipe


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

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']

    # def filter_is_favorited(self, queryset, name, value):
    #     user = self.request.user
    #     if not user.is_authenticated:
    #         return queryset.none() if value else queryset
    #     return (
    #         queryset.filter(favorited_by__user=user)
    #         if value
    #         else queryset.exclude(favorited_by__user=user)
    #     )
    def filter_is_favorited(self, queryset, name, value):
        if value:
            return queryset.filter(is_favorited=True)
        return queryset.exclude(is_favorited=True)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none() if value else queryset
        return (
            queryset.filter(shoppingcarts__user=user)
            if value
            else queryset.exclude(shoppingcarts__user=user)
        )
