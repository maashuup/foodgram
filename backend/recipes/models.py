from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from .constants import EMAIL_MAX_LENGTH, NAME_MAX_LENGTH, USERNAME_MAX_LENGTH


class User(AbstractUser):
    email = models.EmailField(
        unique=True,
        max_length=EMAIL_MAX_LENGTH,
        verbose_name='Email',
    )
    username = models.CharField(
        unique=True,
        max_length=USERNAME_MAX_LENGTH,
        verbose_name='Уникальный юзернейм',
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message='Разрешены только буквы, цифры и ./@/+/-/_.'
            )
        ]
    )
    first_name = models.CharField(
        max_length=NAME_MAX_LENGTH,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=NAME_MAX_LENGTH,
        verbose_name='Фамилия',
    )
    avatar = models.ImageField(
        upload_to='users/',
        blank=True,
        verbose_name='Аватар',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name', 'password')

    class Meta:
        verbose_name = 'Пользователь'
        ordering = ['id']

    def __str__(self):
        return self.username


class Tag(models.Model):
    name = models.CharField(
        max_length=32,
        unique=True,
        verbose_name='Название тега',
    )
    slug = models.SlugField(
        max_length=32,
        unique=True,
        verbose_name='Уникальный слаг тега',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=128,
        unique=True,
        verbose_name='Название ингредиента',
    )
    measurement_unit = models.CharField(max_length=64)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Список id тегов',
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        blank=True,
        default=None,
        verbose_name='Картинка, закодированная в Base64',
    )
    name = models.CharField(
        max_length=256,
        verbose_name='Название',
    )
    text = models.TextField(
        verbose_name='Описание',
        default=''
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Время приготовления',
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания',
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-created']

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_amounts',
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_usages',
        verbose_name='Ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Количество',
    )

    class Meta:
        verbose_name = 'Ингредиент для рецепта'
        verbose_name_plural = 'Ингредиенты для рецепта'

    def __str__(self):
        return f'{self.ingredient} ({self.amount}) для {self.recipe}'


class UserRecipeRelation(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe'
            )
        ]


class Favorite(UserRecipeRelation):
    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'

    def __str__(self):
        return f'{self.user} likes {self.recipe}'


class ShoppingCart(UserRecipeRelation):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart'
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        return f'Список покупок {self.user} для {self.recipe}'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Кто подписан'
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='На кого подписан'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'], name='unique_follow'
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'У {self.user.username} подписка на {self.following.username}'
