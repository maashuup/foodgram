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
    is_in_shopping_cart = django_filters.Filter(
        method='filter_is_in_shopping_cart'
    )
    is_favorited = django_filters.Filter(method='filter_is_favorited')

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']

    def filter_is_favorited(self, queryset, name, value):
        print('🔥 filter_is_favorited вызван! value =', value)
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none() if value else queryset
        favorite_ids = Favorite.objects.filter(
            user=user
        ).values_list('recipe_id', flat=True)
        if value:
            return queryset.filter(id__in=favorite_ids)
        return queryset.exclude(id__in=favorite_ids)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        print('🔥 filter_is_in_shopping_cart вызван! value =', value)
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none() if value else queryset
        cart_ids = ShoppingCart.objects.filter(
            user=user
        ).values_list('recipe_id', flat=True)
        if value:
            return queryset.filter(id__in=cart_ids)
        return queryset.exclude(id__in=cart_ids)
