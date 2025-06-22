import re

from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from api.fields import Base64ImageField
from recipes.models import (Favorite, Follow, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Tag)

User = get_user_model()


class UserSerializer(DjoserUserSerializer):
    """Сериализатор пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        """Подписан ли пользователь на автора."""
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and user.following.filter(following=obj).exists()
        )

    def get_avatar(self, obj):
        """Получение URL аватара пользователя."""
        return obj.avatar.url if obj.avatar else None


class CreateUserSerializer(UserSerializer):
    """Сериализатор создания пользователя."""

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'password'
        )

    def validate_username(self, value):
        """Валидация username."""
        pattern = r'^[\w.@+-]+\Z'
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                'Недопустимые символы в username.'
                'Разрешены только буквы, цифры и @/./+/-/_'
            )
        return value


class UserSerializerForMe(UserSerializer):
    """Сериализатор для текущего пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'avatar',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        return False


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор подписок."""

    email = serializers.ReadOnlyField(source='following.email')
    id = serializers.ReadOnlyField(source='following.id')
    username = serializers.ReadOnlyField(source='following.username')
    first_name = serializers.ReadOnlyField(source='following.first_name')
    last_name = serializers.ReadOnlyField(source='following.last_name')
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Follow
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'recipes',
            'recipes_count', 'avatar',
        )

    def validate(self, data):
        """Валидация подписки (на себя, повторной)."""
        user = self.context['request'].user
        following = self.context.get('following_user')
        if not following:
            raise serializers.ValidationError(
                'Нет целевого пользователя для подписки.'
            )

        if user == following:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.'
            )

        if Follow.objects.filter(user=user, following=following).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя.'
            )

        return data

    def create(self, validated_data):
        user = self.context['request'].user
        following = self.context['following_user']
        return Follow.objects.create(user=user, following=following)

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if not user or not user.is_authenticated:
            return False
        return Follow.objects.filter(
            user=user, following=obj.following
        ).exists()

    def get_avatar(self, obj):
        user = obj.following
        request = self.context.get('request')
        if user.avatar:
            return request.build_absolute_uri(
                user.avatar.url
            ) if request else user.avatar.url
        return None

    def get_recipes(self, obj):
        try:
            request = self.context.get('request')
            limit = request.query_params.get(
                'recipes_limit'
            ) if request else None
            recipes_qs = obj.following.recipes.all()
            if limit and limit.isdigit():
                recipes_qs = recipes_qs[:int(limit)]
            return [{
                'id': r.id,
                'name': r.name,
                'image': request.build_absolute_uri(
                    r.image.url
                ) if request and r.image else None,
                'cooking_time': r.cooking_time
            } for r in recipes_qs]
        except Exception as e:
            print('[ERROR in get_recipes]:', e)
            return []


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор аватара."""

    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """"Сериализатор ингредиентов рецепта."""

    # id = serializers.IntegerField()
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов."""

    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='ingredient_amounts'
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        write_only=True
    )
    image = Base64ImageField(
        required=True,
        max_length=None,
        use_url=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time'
                  )

    def get_is_favorited(self, obj):
        return getattr(obj, 'is_favorited', False)

    def get_is_in_shopping_cart(self, obj):
        return getattr(obj, 'is_in_shopping_cart', False)

    def to_representation(self, instance):
        """Добавление тегов и картинки к рецепту."""
        data = super().to_representation(instance)
        data['tags'] = TagSerializer(instance.tags.all(), many=True).data
        request = self.context.get('request')
        data['image'] = (
            request.build_absolute_uri(instance.image.url)
            if instance.image
            else None
        )
        return data

    def validate(self, attrs):
        """Валидация данных рецепта."""
        request = self.context.get('request')
        if self.instance and self.instance.author != request.user:
            raise PermissionDenied(
                'Вы не можете редактировать чужой рецепт.'
            )
        return attrs

    def validate_ingredients(self, value):
        """Валидация ингредиентов."""
        if not value:
            raise serializers.ValidationError(
                'Необходимо добавить хотя бы один ингредиент.'
            )

        ingredient_ids = []
        for item in value:
            ingredient = item.get('ingredient')
            if not ingredient:
                raise serializers.ValidationError('Ингредиент не найден.')

            ingredient_id = ingredient.id if hasattr(
                ingredient, 'id'
            ) else ingredient
            ingredient_ids.append(ingredient_id)

            amount = item.get('amount')
            if isinstance(amount, str) and amount.isdigit():
                amount = int(amount)

            if not isinstance(amount, int):
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть числом.'
                )
            if amount < 1:
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть не менее 1.'
                )

        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты должны быть уникальны.'
            )

        return value

    def validate_tags(self, value):
        """Валидация тегов."""
        if not value:
            raise serializers.ValidationError(
                'Необходимо указать хотя бы один тег.'
            )
        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                'Теги должны быть уникальны.'
            )
        return value

    def add_ingredients(self, recipe, ingredients_data):
        objs = []
        for item in ingredients_data:
            ing = item.get('ingredient') or item.get('id')
            if isinstance(ing, int):
                ing = Ingredient.objects.get(pk=ing)
            objs.append(RecipeIngredient(
                recipe=recipe,
                ingredient=ing,
                amount=item['amount']
            ))
        RecipeIngredient.objects.bulk_create(objs)

    def create(self, validated_data):
        tags_data = validated_data.pop('tags', [])
        ingredients_data = validated_data.pop('ingredient_amounts', [])
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        self.add_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', [])
        ingredients_data = validated_data.pop('ingredient_amounts', [])
        instance = super().update(instance, validated_data)
        instance.tags.set(tags_data)
        instance.ingredient_amounts.all().delete()
        self.add_ingredients(instance, ingredients_data)
        return instance


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления рецепта в избранное."""

    class Meta:
        model = Favorite
        fields = ('recipe',)

    def create(self, validated_data):
        return Favorite.objects.create(
            user=self.context['request'].user,
            **validated_data
        )


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления рецепта в список покупок."""

    class Meta:
        model = ShoppingCart
        fields = ('recipe',)

    def create(self, validated_data):
        return ShoppingCart.objects.create(
            user=self.context['request'].user,
            **validated_data
        )
