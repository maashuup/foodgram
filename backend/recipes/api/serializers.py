import re

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from recipes.api.fields import Base64ImageField
from recipes.models import (Follow, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)

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
                "Недопустимые символы в username."
                "Разрешены только буквы, цифры и @/./+/-/_"
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
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count', 'avatar')

    def validate_following(self, value):
        """Валидация подписки."""
        user = self.context['request'].user
        if user == value:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.'
            )
        if Follow.objects.filter(user=user, following=value).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя.'
            )
        return value

    def get_is_subscribed(self, obj):
        """Подписан ли пользователь на автора."""
        user = (self.context.get('request').user
                if 'request' in self.context
                else None)
        if not user or not user.is_authenticated:
            return False
        return Follow.objects.filter(
            user=user,
            following=obj.following
        ).exists()

    def get_avatar(self, obj):
        """Получение URL аватара пользователя."""
        user = obj.following
        request = self.context.get('request')
        if user.avatar:
            if request:
                return request.build_absolute_uri(user.avatar.url)
            return user.avatar.url
        return None

    def get_recipes(self, obj):
        """Получение рецептов автора."""
        request = self.context.get('request')
        if not request:
            return []
        recipes_limit = None
        if request:
            limit_val = request.query_params.get('recipes_limit')
            if limit_val is not None:
                recipes_limit = None
                if isinstance(limit_val, str) and limit_val.isdigit():
                    recipes_limit = int(limit_val)

        recipes_qs = obj.following.recipes.all()
        if recipes_limit is not None:
            recipes_qs = recipes_qs[:recipes_limit]

        result = []
        for recipe in recipes_qs:
            result.append({
                "id": recipe.id,
                "name": recipe.name,
                "image": (
                    request.build_absolute_uri(recipe.image.url)
                    if request and recipe.image
                    else recipe.image.url if recipe.image
                    else None
                ),

                "cooking_time": recipe.cooking_time
            })
        return result

    def get_recipes_count(self, obj):
        """Получение количества рецептов автора."""
        return obj.following.recipes.count()


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

    id = serializers.IntegerField()
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
        source="ingredient_amounts"
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
    is_favorited = serializers.BooleanField()
    is_in_shopping_cart = serializers.BooleanField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time'
                  )

    def to_representation(self, instance):
        """Добавление тегов и картинки к рецепту."""
        data = super().to_representation(instance)
        data['tags'] = TagSerializer(instance.tags.all(), many=True).data
        request = self.context.get("request")
        data['image'] = (
            request.build_absolute_uri(instance.image.url)
            if instance.image
            else None
        )
        return data

    def get_is_favorited(self, obj):
        """Проверка, добавлен ли рецепт в избранное."""
        request = self.context.get("request")
        return (
            request.user.is_authenticated
            and obj.favorite_recipes.filter(user=request.user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        """Проверка, добавлен ли рецепт в список покупок."""
        request = self.context.get("request")
        return (
            request.user.is_authenticated
            and ShoppingCart.objects.filter(
                user=request.user, recipe=obj
            ).exists()
        )

    # def validate(self, attrs):
    #     """Валидация данных рецепта."""
    #     request = self.context.get("request")
    #     if self.instance and self.instance.author != request.user:
    #         raise PermissionDenied(
    #             "Вы не можете редактировать чужой рецепт."
    #         )
    #     return attrs

    # def validate_ingredients(self, value):
    #     """Валидация ингредиентов."""
    #     if not value:
    #         raise serializers.ValidationError(
    #             "Необходимо добавить хотя бы один ингредиент."
    #         )

    #     ingredient_ids = [item.get('id') for item in value]
    #     if len(ingredient_ids) != len(set(ingredient_ids)):
    #         raise serializers.ValidationError(
    #             "Ингредиенты должны быть уникальны."
    #         )
    #     for item in value:
    #         amount = item.get("amount")

    #         if isinstance(amount, str) and amount.isdigit():
    #             amount = int(amount)

    #         if not isinstance(amount, int):
    #             raise serializers.ValidationError(
    #                 "Количество ингредиента должно быть числом."
    #             )

    #         if amount < 1:
    #             raise serializers.ValidationError(
    #                 "Количество ингредиента должно быть не менее 1."
    #             )

    #     return value

    # def validate_tags(self, value):
    #     """Валидация тегов."""
    #     if not value:
    #         raise serializers.ValidationError(
    #             "Необходимо указать хотя бы один тег."
    #         )
    #     if len(value) != len(set(value)):
    #         raise serializers.ValidationError(
    #             "Теги должны быть уникальны."
    #         )
    #     return value

    # def validate_text(self, value):
    #     """Валидация текста рецепта."""
    #     if not value or str(value).strip() == "":
    #         raise serializers.ValidationError(
    #             "Необходимо указать описание рецепта."
    #         )
    #     return value
    def validate(self, attrs):
        """Валидация данных рецепта."""
        request = self.context.get("request")
        if self.instance and self.instance.author != request.user:
            raise PermissionDenied("Вы не можете редактировать чужой рецепт.")

        ingredients = self.initial_data.get("ingredients", [])
        if not ingredients:
            raise serializers.ValidationError({
                "ingredients": "Необходимо добавить хотя бы один ингредиент."
            })

        tags = self.initial_data.get("tags")
        if not tags or len(tags) == 0:
            raise serializers.ValidationError({
                "tags": "Необходимо указать хотя бы один тег."
            })

        if len(tags) != len(set(tags)):
            raise serializers.ValidationError({
                "tags": "Теги должны быть уникальны."
            })

        seen_ids = set()
        for item in ingredients:
            ingr_id = item.get('id')
            amount = item.get('amount')
            if ingr_id in seen_ids:
                raise serializers.ValidationError({
                    "ingredients": "Ингредиенты должны быть уникальны."
                })
            seen_ids.add(ingr_id)
            # if not isinstance(amount, int) or amount < 1:
            #     raise serializers.ValidationError({
            #         "ingredients": (
            #             "Количество ингредиента должно быть не менее 1."
            #         )
            #     })
            try:
                amount = int(amount)
                if amount < 1:
                    raise ValueError
            except (ValueError, TypeError):
                raise serializers.ValidationError({
                    "ingredients":
                    "Количество ингредиента должно быть не менее 1."
                })

            if (
                not self.initial_data.get("text")
                or str(self.initial_data.get("text")).strip() == ""
            ):
                raise serializers.ValidationError({
                    "text": "Необходимо указать описание рецепта."
                })
        return attrs

    def validate_cooking_time(self, value):
        """Валидация времени приготовления."""
        if value < 1:
            raise serializers.ValidationError(
                "Время приготовления должно быть не меньше 1 минуты."
            )
        return value

    # def add_ingredients(self, recipe, ingredients_data):
    #     """Добавляет ингредиенты к рецепту."""
    #     RecipeIngredient.objects.bulk_create([
    #         RecipeIngredient(
    #             recipe=recipe,
    #             ingredient_id=ingredient['id'],
    #             amount=ingredient['amount']
    #         )
    #         for ingredient in ingredients_data
    #     ])

    # def create(self, validated_data):
    #     tags_data = validated_data.pop('tags', [])
    #     ingredients_data = validated_data.pop('ingredient_amounts', [])
    #     recipe = Recipe.objects.create(**validated_data)
    #     recipe.tags.set(tags_data)
    #     self.add_ingredients(recipe, ingredients_data)
    #     return recipe

    # def update(self, instance, validated_data):
    #     tags_data = validated_data.pop('tags', [])
    #     ingredients_data = validated_data.pop('ingredient_amounts', [])
    #     instance = super().update(instance, validated_data)
    #     instance.tags.set(tags_data)
    #     instance.ingredients.clear()
    #     self.add_ingredients(instance, ingredients_data)
    #     return instance
    def create(self, validated_data):
        tags_data = validated_data.pop('tags', [])
        ingredients_data = validated_data.pop('ingredient_amounts', [])
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        for ingredient_data in ingredients_data:
            ingredient = get_object_or_404(
                Ingredient, id=ingredient_data['id']
            )
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=ingredient_data['amount']
            )
        return recipe

    def update(self, instance, validated_data):
        if 'ingredient_amounts' in validated_data:
            ingredients_data = validated_data.pop('ingredient_amounts', [])
            instance.ingredient_amounts.all().delete()
            for ingredient_data in ingredients_data:
                ingredient = get_object_or_404(
                    Ingredient, id=ingredient_data['id']
                )
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient=ingredient,
                    amount=ingredient_data['amount']
                )
        if 'tags' in validated_data:
            instance.tags.set(validated_data.pop('tags', []))
        return super().update(instance, validated_data)
