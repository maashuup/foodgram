from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (Favorite, Follow, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag, User)


@admin.register(User)
class Admin(UserAdmin):
    """Настройка отображения пользователей в админке."""

    list_display = ('id', 'email', 'username', 'first_name', 'last_name',
                    'is_staff')
    list_display_links = ('email',)
    search_fields = ('email', 'username', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    ordering = ('id',)
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'avatar')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups',
                       'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Настройки админки для ингредиентов рецепта."""

    list_display = ('recipe', 'ingredient', 'amount')
    list_filter = ('recipe', 'ingredient')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Настройки админки для ингредиентов."""

    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Настройки админки для рецептов."""

    list_display = ('id', 'name', 'author',)
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('tags',)
    filter_horizontal = ('ingredients',)
    inlines = [RecipeIngredientInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'author'
        ).prefetch_related('ingredients', 'tags')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Настройки админки для тегов."""

    list_display = ('id', 'name', 'slug')
    search_fields = ('name',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Настройки админки для избранного."""

    list_display = ('id', 'user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Настройки админки для корзины покупок."""

    list_display = ('id', 'user', 'recipe')


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Настройки админки для подписок."""

    list_display = ('id', 'user', 'following')
