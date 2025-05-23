from collections import defaultdict

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

from .filters import IngredientFilter, RecipeFilter
from .models import (Favorite, Follow, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag, User)
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
        queryset = Follow.objects.filter(user=request.user)
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
        try:
            user_to_follow = User.objects.get(pk=id)
        except User.DoesNotExist:
            return Response(
                {'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND
            )

        if request.user == user_to_follow:
            return Response(
                {'error': 'Нельзя подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'POST':
            follow, created = Follow.objects.get_or_create(
                user=request.user, following=user_to_follow
            )
            if not created:
                return Response(
                    {'error': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = FollowSerializer(
                follow, context={'request': request} if request else None
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            follow_qs = Follow.objects.filter(
                user=request.user, following=user_to_follow
            )
            if not follow_qs.exists():
                return Response(
                    {'error': 'Вы не подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            follow_qs.delete()
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
                user.avatar.delete(save=False)
                user.avatar = None
                user.save(update_fields=['avatar'])
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

    @action(
        detail=False,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавление/удаление рецепта в избранное."""
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            favorite, created = Favorite.objects.get_or_create(
                user=request.user, recipe=recipe
            )
            if not created:
                return Response(
                    {'error': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
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
        elif request.method == 'DELETE':
            favorite = Favorite.objects.filter(
                user=request.user,
                recipe=recipe
            )
            if favorite.exists():
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'error': 'Рецепт не найден в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавление/удаление рецепта в список покупок."""
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            cart, created = ShoppingCart.objects.get_or_create(
                user=request.user,
                recipe=recipe
            )
            if not created:
                return Response(
                    {'error': 'Рецепт уже в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
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
        elif request.method == 'DELETE':
            cart = ShoppingCart.objects.filter(
                user=request.user,
                recipe=recipe
            )
            if cart.exists():
                cart.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'error': 'Рецепт не найден в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST
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
        carts = (
            ShoppingCart.objects
            .filter(user=request.user)
            .select_related('recipe')
        )

        if not carts.exists():
            return Response(
                {'error': 'Список покупок пуст'},
                status=status.HTTP_400_BAD_REQUEST
            )

        totals = defaultdict(lambda: {'amount': 0, 'unit': ''})
        recipes_used = set()

        # Суммирование ингредиентов по названиям и сбор списка рецептов
        for cart in carts:
            recipe = cart.recipe
            recipes_used.add(recipe.name)
            for ri in (
                RecipeIngredient.objects
                .filter(recipe=recipe)
                .select_related('ingredient')
            ):
                key = ri.ingredient.name
                totals[key]['amount'] += ri.amount
                totals[key]['unit'] = ri.ingredient.measurement_unit

        # Формирование списка для файла
        lines = ['Список покупок:']
        lines.append("\nИспользуемые рецепты:")
        for recipe_name in sorted(recipes_used):
            lines.append(f" - {recipe_name}")

        lines.append("\nИнгредиенты:")
        for name, data in totals.items():
            lines.append(f" - {name}: {data['amount']} {data['unit']}")

        content = "\n".join(lines)
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response
