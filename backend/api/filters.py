import django_filters
from django_filters.rest_framework import FilterSet

from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart


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

    def filter_is_favorited(self, queryset, name, value):
        print('🔥 Фильтр is_favorited сработал! Значение:', value)
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none() if value else queryset

        favorites = Favorite.objects.filter(
            user=user
        ).values_list('recipe_id', flat=True)
        if value:
            return queryset.filter(id__in=favorites)
        return queryset.exclude(id__in=favorites)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none() if value else queryset

        cart_items = ShoppingCart.objects.filter(
            user=user
        ).values_list('recipe_id', flat=True)
        if value:
            return queryset.filter(id__in=cart_items)
        return queryset.exclude(id__in=cart_items)
