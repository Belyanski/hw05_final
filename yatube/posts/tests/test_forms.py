import shutil
import tempfile

from http import HTTPStatus
from posts.models import Group, Post, Comment, User
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

    def test_auth_client_create_post(self):
        """"Создается новая запись в Post"""
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Текст',
            'group': self.group.pk,
            'user': self.user.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        last_post = Post.objects.order_by('id').last()
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(form_data['text'], last_post.text)
        self.assertEqual(form_data['group'], last_post.group.pk)
        self.assertEqual(last_post.image.name, 'posts/small.gif')
        self.assertEqual(self.user.username, last_post.author.username)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, reverse(
                'posts:profile', kwargs={'username': self.user.username})
        )

    def test_guest_create_post(self):
        """"Неавторизованный клиент не может создавать посты."""
        form_data = {
            'text': 'Пост от неавторизованного клиента',
            'group': self.group.id
        }
        self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertFalse(Post.objects.filter(
            text='Пост неавторизованнного клиента').exists())

    def test_authorized_post_edit(self):
        """"Авторизованный клиент редактирует пост."""
        self.post = Post.objects.create(
            author=self.user,
            text='Великий пост',
            pub_date='Великая дата',
            group=self.group,
        )
        self.new_group = Group.objects.create(
            title='Сорока два',
            slug='test-slug_2',
            description='Сорок два описания',
        )
        post_count = Post.objects.count()
        form_data = {
            'text': 'Новый текст',
            'group': self.new_group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=False
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        post = Post.objects.get(pk=self.post.pk)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk}))
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, self.new_group.id)

    def test_comment(self):
        """Комментирование постов."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
