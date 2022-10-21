from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        help_text='Введите название группы',
        verbose_name='Название группы'
    )
    slug = models.SlugField(
        unique=True,
        help_text='Придумайте название ссылки',
        verbose_name='URL'
    )
    description = models.TextField(
        help_text='Напишите описание к группе',
        verbose_name='Описаине'
    )

    def __str__(self):
        return self.title


class Post(models.Model):
    LENGHT_STR_TEXT = 15
    text = models.TextField(
        help_text='Что вы хотите рассказать?',
        verbose_name='Текст'
    )
    pub_date = models.DateTimeField(auto_now_add=True)
    group = models.ForeignKey(
        Group(),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts'
    )
    author = models.ForeignKey(
        User,
        null=True,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    image = models.ImageField(
        upload_to='posts/',
        blank=True,
        null=True)

    class Meta:
        ordering = ('-pub_date',)

    def __str__(self):
        return self.text[:self.LENGHT_STR_TEXT]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    text = models.TextField(
        verbose_name='Комментарий',
        help_text='Комментарий'
    )

    created = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name='unique_follow',
                fields=['user', 'author'],
            ),
            models.CheckConstraint(
                name='prevent_self_follow',
                check=~models.Q(user=models.F('author'))
            ),
        ]
