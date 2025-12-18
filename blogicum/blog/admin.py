"""Admin registrations for blog app."""

from django.contrib import admin
# Не забудьте импортировать Comment, если он есть в models.py
from .models import Category, Post, Location, Comment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    # Тут все выглядит верно
    list_display = (
        "title",
        "is_published",
        "created_at",
        "slug",
    )
    list_filter = ("is_published", "created_at", "slug" )
    search_fields = ("title",)
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    # У Локации обычно поле name, а не title.
    # Убраны поля pub_date и category - они относятся к Посту, а не к Локации.
    list_display = (
        "name",  # Скорее всего в модели это field name="name"
        "is_published",
        "created_at",
    )
    list_filter = ("is_published",)
    search_fields = ("name",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    # У Поста поле называется title.
    # Добавил вывод категории, автора и даты публикации.
    list_display = (
        "title",
        "author",
        "category",
        "location",
        "is_published",
        "pub_date",
    )
    # Расширенные фильтры
    list_filter = (
        "is_published",
        "category",
        "location",
        "pub_date",
        "author",
    )
    # Поиск по заголовку и тексту поста
    search_fields = ("title", "text")
    # Возможность быстро менять статус публикации из списка
    list_editable = ("is_published",)


# Добавьте админку для комментариев, чтобы ими можно было управлять
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "text",
        "post",
        "author",
        "created_at",
    )
    list_filter = ("author", "created_at")
    search_fields = ("text",)