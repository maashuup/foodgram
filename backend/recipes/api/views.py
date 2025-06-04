from collections import defaultdict

from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from recipes.models import (Favorite, Follow, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Tag, User)

from .filters import IngredientFilter, RecipeFilter
from .serializers import (AvatarSerializer, FollowSerializer,
                          IngredientSerializer, RecipeSerializer,
                          TagSerializer, UserSerializer, UserSerializerForMe)


class PageLimitPagination(PageNumberPagination):
    """Пагинация с лимитом количества объектов на странице."""
    page_size = 6
    page_size_query_param = 'limit'


class UserViewSet(DjoserUserViewSet):
    """Вьюсет для управления пользователями."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageLimitPagination

    def get_serializer_class(self):
        """Для эндпоинта /me используется другой сериализатор."""
        if self.action == "me":
            return UserSerializerForMe
        return super().get_serializer_class()

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request, *args, **kwargs):
        """Возвращает данные текущего пользователя (профиль)."""
        return super().me(request, *args, **kwargs)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Список подписок текущего пользователя (с пагинацией)."""
        queryset = Follow.objects.filter(user=request.user).annotate(
            recipes_count=Count('following__recipes')
        )
        page = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            page or queryset, many=True, context={'request': request}
        )
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='subscribe'
    )
    def subscribe(self, request, id=None):
        """Подписка или отписка от пользователя."""
        user_to_follow = get_object_or_404(User, pk=id)

        if request.method == 'POST':
            data = {'following': user_to_follow.id}
            serializer = FollowSerializer(
                data=data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            follow_obj = Follow.objects.get(
                user=request.user, following=user_to_follow
            )
            return Response(
                FollowSerializer(
                    follow_obj,
                    context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )

        if request.method == 'DELETE':
            follow_qs = Follow.objects.filter(
                user=request.user, following=user_to_follow
            )

            deleted, _ = follow_qs.delete()
            if deleted == 0:
                return Response(
                    {'error': 'Вы не подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar'
    )
    def avatar(self, request):
        """Добавить/удалить аватар пользователя."""
        user = request.user
        if request.method == 'PUT':
            if 'avatar' not in request.data:
                return Response(
                    {"avatar": ["Обязательное поле."]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = AvatarSerializer(
                instance=user, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {'avatar': user.avatar.url if user.avatar else None},
                status=status.HTTP_200_OK
            )
        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Просмотр тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Просмотр ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """Управление рецептами (создание, получение, редактирование, удаление)."""
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    pagination_class = PageLimitPagination
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        """Создаёт рецепт, устанавливая текущего пользователя автором."""
        serializer.save(author=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """Удаляет рецепт, если текущий пользователь является его автором."""
        recipe = self.get_object()
        if recipe.author != request.user:
            return Response(
                {'detail': 'Недостаточно прав.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Recipe.objects.all().select_related(
            'author'
        ).prefetch_related(
            'tags', 'ingredient_amounts__ingredient'
        )

        return queryset

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавление/удаление рецепта в избранное."""
        recipe = get_object_or_404(Recipe, pk=pk)
        return handle_add_remove(
            request,
            recipe,
            model=Favorite,
            error_exists='Рецепт уже в избранном',
            error_not_found='Рецепт не найден в избранном'
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def favorites(self, request):
        """Список рецептов, добавленных в избранное текущим пользователем."""
        recipes = Recipe.objects.filter(favorite_recipes__user=request.user)
        serializer = self.get_serializer(
            recipes, many=True, context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавление/удаление рецепта в список покупок."""
        recipe = get_object_or_404(Recipe, pk=pk)
        return handle_add_remove(
            request,
            recipe,
            model=ShoppingCart,
            error_exists='Рецепт уже в списке покупок',
            error_not_found='Рецепт не найден в списке покупок'
        )

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
        permission_classes=[AllowAny]
    )
    def get_link(self, request, pk=None):
        """Возврат короткой ссылки на рецепт."""
        recipe = self.get_object()
        relative_url = reverse('recipe-detail', kwargs={'pk': recipe.pk})
        absolute_url = request.build_absolute_uri(relative_url)
        return Response(
            {"short-link": absolute_url},
            status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Выгрузка списка покупок в файл с указанием рецептов и суммированием
        одинаковых ингредиентов."""
        user = request.user

        # Получаем все ингредиенты через промежуточную модель
        ingredients_qs = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=user
        ).select_related('ingredient')

        totals = defaultdict(lambda: {'amount': 0, 'unit': ''})
        recipes_used = set()

        for ri in ingredients_qs:
            name = ri.ingredient.name
            totals[name]['amount'] += ri.amount
            totals[name]['unit'] = ri.ingredient.measurement_unit
            recipes_used.add(ri.recipe.name)

        return render_ingredients_txt(totals, recipes_used)


def render_ingredients_txt(ingredients_totals, recipes_used):
    lines = ['Список покупок:']
    lines.append('\nИспользуемые рецепты:')
    for name in sorted(recipes_used):
        lines.append(f'– {name}')
    lines.append('\nИнгредиенты:')
    for name, data in ingredients_totals.items():
        lines.append(f'– {name}: {data["amount"]} {data["unit"]}')

    content = '\n'.join(lines)
    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = (
        'attachment; filename="shopping_list.txt"'
    )
    return response


def handle_add_remove(request, recipe, model, error_exists, error_not_found):
    if request.method == 'POST':
        obj, created = model.objects.get_or_create(
            user=request.user, recipe=recipe
        )
        if not created:
            return Response(
                {'error': error_exists}, status=status.HTTP_400_BAD_REQUEST
            )
        data = {
            'id': recipe.id,
            'name': recipe.name,
            'image': (
                request.build_absolute_uri(recipe.image.url)
                if recipe.image else None
            ),
            'cooking_time': recipe.cooking_time
        }
        return Response(data, status=status.HTTP_201_CREATED)

    if request.method == 'DELETE':
        qs = model.objects.filter(user=request.user, recipe=recipe)
        deleted, _ = qs.delete()
        if deleted == 0:
            return Response(
                {'error': error_not_found},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
