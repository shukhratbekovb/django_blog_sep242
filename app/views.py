from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from app.models import Post, DisLike, Like, Report
from app.forms import PostForm, CustomUserCreationForm, CommentForm, ReportForm, UserChangeForm, MediaFormSet


# TODO: Сделать Страницу Главную Index
class IndexView(ListView):
    """
    Представления для Главной Страницы
    """
    # Для подключения Модели
    model = Post
    # Устанавливаем Шаблон HTML
    template_name = "app/index.html"
    # Имя переменной в Шаблоне
    context_object_name = "posts"
    # Сортировка по какому то полю либо несколько полей
    ordering = ["-created_at"]  # по убыванию
    # Для реализации пагинации
    paginate_by = 30


# TODO: Авторизацию
# TODO: Регистрацию
# TODO: Сделать Страницу Создание Поста
class PostCreateView(LoginRequiredMixin, CreateView):
    """
    Представления для Создания Поста
    Но Посты могут создавать только авторизованные пользователи
    """
    # Для Подключения Модельки чтоб знать обьект какой модельки он должен создать
    model = Post
    # Для Создания Поста нужно указывать форму
    form_class = PostForm
    # Шаблон HTML
    template_name = "app/post_form.html"
    # Куда перенаправлять после создания
    success_url = reverse_lazy("index")

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["media_formset"] = kwargs.get("media_formset") or MediaFormSet()
        return context

    # Так как используем FormSet нам придется вручную сохранять
    def post(self, request, *args, **kwargs):
        form = self.get_form()  # Получаем заполненую Форму поста
        media_formset = MediaFormSet(request.POST, request.FILES)  # Получаем заполненый медиа

        # Проверяем Правильно ли заполненые формы
        if form.is_valid() and media_formset.is_valid():
            post = form.save(commit=False)
            post.author = self.request.user  # Добавляем автора созданного поста
            post.save()

            media_formset.instance = post  # вставляем пост для которого медиа заполнели
            media_formset.save()  # Сохраняем медиа

            return redirect("index")  # После успеха отправляем на главную страницу
        return self.render_to_response(
            self.get_context_data(form=form, media_formset=media_formset)
        )


# TODO: Сделать Страницу Списка Постов
class PostListView(ListView):
    """
    Представления для Списка Постов
    """
    # Для подключения Модели
    model = Post
    # Устанавливаем Шаблон HTML
    template_name = "app/post_list.html"
    # Имя переменной в Шаблоне
    context_object_name = "posts"
    # Сортировка по какому то полю либо несколько полей
    ordering = ["-created_at"]  # по убыванию
    # Для реализации пагинации
    paginate_by = 50


# TODO: Сделать Страницу Просмотра Поста
class PostDetailView(DetailView):
    """
    Представления для Получения Одного Конкретного Поста
    """
    # Моделька
    model = Post
    # Шаблон HTML
    template_name = "app/post_detail.html"
    # Имя Переменной в Шаблон
    context_object_name = "post"

    def get_context_data(self, **kwargs):
        """
        Помогает засунуть доп переменные
        """
        context = super().get_context_data(**kwargs)
        context["comment_form"] = CommentForm()  # Мы добавили переменную comment_form
        context["post_test"] = "Тестовое"
        return context


# TODO: Сделать Страницу Изменение Поста
class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    template_name = "app/post_form.html"
    form_class = PostForm

    # success_url = reverse_lazy("post-detail", pk=pk)
    def get_success_url(self):  # /posts/3
        return reverse_lazy("post-detail", pk=self.object.pk)

    def test_func(self):
        """
        Проверка того что пользователь является автором изменяемого поста
        :return:
        """
        post = self.get_object()
        return self.request.user == post.author


# TODO: Сделать Страницу Подтверждение Удаления
class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = "app/post_delete.html"
    success_url = reverse_lazy("post-list")

    def test_func(self):
        """
        Проверка того что пользователь является автором удаляемого поста
        :return:
        """
        post = self.get_object()
        return self.request.user == post.author


# TODO: Сделать Страницу Создание Жалоб

# TODO: Сделать Страницу Список жалоб Пользователя

# TODO: Сделать Авторизацию и Регистрацию
# Регистрацию
def register(request):
    if request.method == "POST":  # Пользователь уже зашел на страницу и заполнил форму
        form = CustomUserCreationForm(request.POST)  # Тут вставили в форму данные которые дал пользователь
        if form.is_valid():  # Мы проверили что он правильно заполнил форму
            user = form.save()  # Сохранили Пользователя
            return redirect("login")
    else:  # Пользователь только зашел на страницу
        form = CustomUserCreationForm()  # Отправили пустую пользователю чтобы он ее заполнил
    return render(
        request,  # запрос пользователя
        "app/register.html",  # шаблон который должна показать пользователю
        {
            "form": form
        }  # Контекст (Данные) которые должны показаться пользователю
    )


# Логин
class CustomLoginView(LoginView):
    template_name = "app/login.html"
    success_url = reverse_lazy("index")


@login_required
def like_post(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(Post, pk=post_id)

        # Удаление Дизлайка
        DisLike.objects.filter(post=post, user=request.user).delete()

        like, created = Like.objects.get_or_create(user=request.user, post=post)

        if not created:
            like.delete()

        return redirect("post-detail", post_id)


@login_required
def dislike_post(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(Post, pk=post_id)

        # Удаление Лайк
        Like.objects.filter(post=post, user=request.user).delete()

        dislike, created = DisLike.objects.get_or_create(user=request.user, post=post)

        if not created:
            dislike.delete()

        return redirect("post-detail", post_id)


@login_required
def create_comment(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(Post, pk=post_id)
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user  # Вручную указали ПОльзователя который создал коммент
            comment.post = post  # Вручную указали Пост к которому создан коммент
            comment.save()  # Сохранили Коммент
            return redirect("post-detail", post_id)
        else:
            # Нужно доработать и сделать Ошибку
            return redirect("post-detail", post_id)
    else:  # GET
        return redirect("post-detail", post_id)


# ДЗ вам сделать эту страницу
def about_us(request):
    pass


# TODO: Создание Жалоб
@login_required
def create_report(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    # Когда человек заполнил форму
    if request.method == "POST":
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.user = request.user
            report.post = post
            report.save()
            return redirect("post-detail", post_id)
        else:
            form = ReportForm()
            return render(
                request,
                "app/report_form.html",
                {
                    "form": form,
                    "post_id": post_id
                }
            )
    # Когда человек впревые зашел на страницу заполнения
    else:
        form = ReportForm()
        return render(
            request,
            "app/report_form.html",
            {
                "form": form,
                "post_id": post_id
            }
        )


# TODO: Получение Списка Жалоб
class ReportListView(LoginRequiredMixin, ListView):
    model = Report
    template_name = "app/report_list.html"
    context_object_name = "reports"

    def get_queryset(self):  # Фильтруем данные
        # Мы сделали так чтобы пользователь видел только свои Жалобы
        return Report.objects.filter(user=self.request.user)


# Профиль
@login_required
def profile_view(request):
    return render(
        request,
        "app/profile.html",

    )


# Изменение Пароля
# Изменение Информация Пользователя
class UserUpdateView(UpdateView):
    form_class = UserChangeForm
    template_name = "app/user_form.html"
    success_url = reverse_lazy("index")
    model = User


class UserPostListView(PostListView):
    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)
