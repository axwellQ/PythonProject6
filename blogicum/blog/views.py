from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Count
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponseNotFound

from .models import Post, Category, Comment
from .forms import PostForm, CommentForm, UserEditForm

User = get_user_model()


def get_paginated_page(request, queryset, count=10):
    """Вспомогательная функция: разбивает список объектов на страницы."""
    # Создаем пагинатор: передаем список объектов и кол-во на одну страницу
    paginator = Paginator(queryset, count)
    # Получаем номер страницы из URL-параметра (например, ?page=2)
    page_number = request.GET.get('page')
    # Возвращаем объекты для текущей страницы
    return paginator.get_page(page_number)


def index(request):
    """Главная страница."""
    template = "blog/index.html"

    # Формируем сложный запрос к БД (QuerySet)
    post_list = (
        # select_related: Оптимизация (SQL JOIN). Загружаем связанные поля сразу,
        # чтобы в шаблоне не было лишних запросов к базе.
        Post.objects.select_related('location', 'author', 'category')
        .filter(
            # Оставляем посты, дата которых меньше или равна (lte) текущему времени
            pub_date__lte=timezone.now(),
            is_published=True,             # Только опубликованные посты
            category__is_published=True,   # Только из опубликованных категорий
        )
        # annotate: Добавляем к каждому объекту поста вычисляемое поле.
        # Count: Считаем количество связанных комментариев.
        .annotate(comment_count=Count('comment'))
        .order_by('-pub_date')  # Сортировка: новые сверху (минус перед полем)
    )

    # Применяем пагинацию к полученному списку
    page_obj = get_paginated_page(request, post_list)

    context = {"page_obj": page_obj}
    return render(request, template, context)


def post_detail(request, post_id):
    """Страница одного поста."""
    template = "blog/detail.html"

    # get_object_or_404: Ищем пост по ID. Если не найден — ошибка 404.
    post = get_object_or_404(
        Post.objects.select_related('location', 'author', 'category'),
        pk=post_id
    )

    # Проверка прав доступа:
    # Если текущий пользователь НЕ автор поста...
    if request.user != post.author:
        # ...то проверяем условия публикации.
        if (
                not post.is_published             # Пост снят с публикации
                or not post.category.is_published # Категория скрыта
                or post.pub_date > timezone.now() # Дата публикации в будущем
        ):
            # Если хотя бы одно условие верно — возвращаем 404 (скрываем пост)
            return HttpResponseNotFound()

    # Получаем все комментарии к посту.
    # ИСПРАВЛЕНО: используем .comment вместо .comment_set, так как related_name='comment'
    comments = post.comment.all().order_by('created_at')

    # Если пользователь авторизован — показываем форму добавления комментария.
    # Если нет (аноним) — передаем None (форма не отобразится).
    form = CommentForm() if request.user.is_authenticated else None

    context = {
        "post": post,
        "comments": comments,
        "form": form,
    }
    return render(request, template, context)


def category_posts(request, category_slug):
    """Страница постов выбранной категории."""
    template = "blog/category.html"

    # Ищем категорию по слагу. Если она скрыта — 404.
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True,
    )

    # Фильтруем посты: они должны принадлежать этой категории
    post_list = (
        Post.objects.filter(
            category=category,
            is_published=True,
            pub_date__lte=timezone.now(),
        )
        .select_related('author', 'location')
        # ИСПРАВЛЕНО: Count('comment') вместо Count('comment_set')
        .annotate(comment_count=Count('comment'))
        .order_by('-pub_date')
    )

    page_obj = get_paginated_page(request, post_list)

    context = {
        "category": category,
        "page_obj": page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    """Страница профиля пользователя."""
    template = "blog/profile.html"

    # Находим пользователя, чей профиль просматриваем
    profile_user = get_object_or_404(User, username=username)

    # Базовый список всех постов этого автора
    posts_qs = Post.objects.filter(author=profile_user).select_related('location', 'category')

    # ЛОГИКА: Если страницу смотрит КТО-ТО ДРУГОЙ (не владелец профиля)
    if request.user != profile_user:
        # То скрываем черновики и отложенные посты
        posts_qs = posts_qs.filter(
            is_published=True,
            pub_date__lte=timezone.now()
        )

    # Считаем комменты и сортируем
    # ИСПРАВЛЕНО: Count('comment') вместо Count('comment_set')
    posts_qs = posts_qs.annotate(comment_count=Count('comment')).order_by("-pub_date")

    page_obj = get_paginated_page(request, posts_qs)

    context = {
        "profile": profile_user,
        "page_obj": page_obj
    }
    return render(request, template, context)


def register(request):
    """Регистрация нового пользователя."""
    template = "registration/registration_form.html"

    if request.method == "POST":
        # Заполняем стандартную форму регистрации данными из запроса
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # Сохраняем пользователя в БД
            user = form.save()
            # login(): Сразу авторизуем пользователя после успешной регистрации
            login(request, user)
            # Перенаправляем на страницу его нового профиля
            return redirect('blog:profile', username=user.username)
    else:
        # GET запрос: пустая форма
        form = UserCreationForm()

    return render(request, template, {"form": form})


@login_required  # Декоратор: доступ только для авторизованных
def edit_profile(request, username):
    """Редактирование профиля."""
    template = "blog/user.html"

    user = get_object_or_404(User, username=username)

    # Защита: Пользователь может редактировать ТОЛЬКО свой профиль
    if request.user != user:
        return redirect('blog:profile', username=username)

    if request.method == "POST":
        # instance=user: Указываем, какого именно пользователя обновляем
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile', username=user.username)
    else:
        # GET: Заполняем форму текущими данными пользователя
        form = UserEditForm(instance=user)

    return render(request, template, {"form": form})


@login_required
def create_post(request):
    """Создание нового поста."""
    template = "blog/create.html"

    if request.method == "POST":
        # request.FILES: Обязательно для загрузки файлов (картинок)
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            # commit=False: Создаем объект, но НЕ сохраняем в БД сразу.
            # Нам нужно вручную добавить автора.
            post = form.save(commit=False)
            post.author = request.user  # Присваиваем автора (текущий юзер)
            post.save()                 # Теперь сохраняем окончательно
            return redirect('blog:profile', username=request.user.username)
    else:
        form = PostForm()

    return render(request, template, {"form": form})


@login_required
def post_edit(request, post_id):
    """Редактирование существующего поста."""
    template = "blog/create.html"

    post = get_object_or_404(Post, pk=post_id)

    # Защита: редактировать пост может только его автор
    if request.user != post.author:
        # Если чужой — перенаправляем на просмотр поста
        return redirect('blog:post_detail', post_id=post.pk)

    if request.method == "POST":
        # instance=post: Форма знает, что мы меняем ЭТОТ конкретный пост
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post.pk)
    else:
        # GET: Показываем форму с уже заполненными данными
        form = PostForm(instance=post)

    return render(request, template, {"form": form})


@login_required
def post_delete(request, post_id):
    """Удаление поста."""
    template = "blog/create.html"

    post = get_object_or_404(Post, pk=post_id)

    # Защита: удалять пост может только его автор
    if request.user != post.author:
        return redirect('blog:post_detail', post_id=post.pk)

    if request.method == "POST":
        # Реальное удаление происходит только при POST-запросе (нажатие кнопки)
        post.delete()
        return redirect('blog:profile', username=request.user.username)

    # GET: Отображение формы (обычно readonly) для подтверждения
    form = PostForm(instance=post)
    context = {"form": form, "instance": post}
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    """Добавление комментария к посту."""
    post = get_object_or_404(Post, pk=post_id)

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            # commit=False: Останавливаем сохранение, чтобы добавить данные,
            # которых нет в форме (автор и пост)
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()

    return redirect('blog:post_detail', post_id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    """Редактирование комментария."""
    template = "blog/comment.html"

    # Ищем комментарий и проверяем, что он относится к нужному посту
    comment = get_object_or_404(Comment, pk=comment_id, post_id=post_id)

    # Защита: редактирует только автор комментария
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == "POST":
        # instance=comment: Обновляем существующий комментарий
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = CommentForm(instance=comment)

    return render(request, template, {"form": form, "comment": comment})


@login_required
def delete_comment(request, post_id, comment_id):
    """Удаление комментария."""
    template = "blog/comment.html"

    comment = get_object_or_404(Comment, pk=comment_id, post_id=post_id)

    # Защита: удаляет только автор комментария
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == "POST":
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)

    return render(request, template, {"comment": comment})