from http import HTTPStatus
from django.test import TestCase, Client
from django.core.cache import cache

from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            pub_date='Тестовая дата',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.author_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client.force_login(self.post.author)
        cache.clear()

    def test_templates_urls(self):
        """Проверка соответствия шаблонов."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_urls_for_all(self):
        """Страницы, доступные всем."""
        urls = {
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.id}/',
        }
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_author_access_only(self):
        """Страницы, доступные лишь автору."""
        urls = {
            f'/posts/{self.post.id}/edit/': 'posts/post_create.html',
            '/create/': 'posts/post_create.html',
        }
        for url in urls:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_auth_access_only(self):
        """Страницы, доступные авторизованному клиенту."""
        urls = {
            f'/posts/{self.post.id}/edit/': 'posts/post_create.html',
            '/create/': 'posts/post_create.html',
        }
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_page_not_found(self):
        """Ошибка запроса несуществующей страницы."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
