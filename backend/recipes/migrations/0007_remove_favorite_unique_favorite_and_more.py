# Generated by Django 4.2.19 on 2025-06-10 18:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0006_alter_user_options_alter_favorite_recipe_and_more'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='favorite',
            name='unique_favorite',
        ),
        migrations.RemoveConstraint(
            model_name='shoppingcart',
            name='unique_shopping_cart',
        ),
    ]
