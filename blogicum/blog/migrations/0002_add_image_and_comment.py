"""Add image field to Post and create Comment model

Generated for tests.
"""

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="image",
            field=models.ImageField(upload_to="posts/", null=True, blank=True, verbose_name="Изображение"),
        ),
        migrations.CreateModel(
            name="Comment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text", models.TextField(verbose_name="Текст комментария")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Добавлено")),
                ("post", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="blog.post", verbose_name="Пост")),
                ("author", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name="Автор комментария")),
            ],
        ),
    ]
