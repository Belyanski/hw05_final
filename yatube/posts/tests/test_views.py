from http import HTTPStatus
from django import forms
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.models import Group, Post, Comment, Follow, User

from django.core.cache import cache


class PostPagesTests(TestCase):
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
            text='Тестовый текст',
            pub_date='Тестовая дата',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон и HTTP статус."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}): (
                'posts/group_list.html'),
            reverse('posts:profile', kwargs={'username': (
                self.user.username)}): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': (
                self.post.pk)}): 'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': (
                self.post.pk)}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_show_correct_context(self):
        """Шаблоны posts сформированы с правильным контекстом."""
        namespace_list = {
            reverse('posts:index'): 'page_obj',
            reverse('posts:group_list', args=[self.group.slug]): 'page_obj',
            reverse('posts:profile', args=[self.user.username]): 'page_obj',
            reverse('posts:post_detail', args=[self.post.pk]): 'post',
        }
        for reverse_name, context in namespace_list.items():
            first_object = self.guest_client.get(reverse_name)
            if context == 'post':
                first_object = first_object.context[context]
            else:
                first_object = first_object.context[context][0]
            posts_dict = {
                first_object.text: self.post.text,
                first_object.author: self.user,
                first_object.group: self.group,
                first_object.image: self.post.image
            }
            for post_param, test_post_param in posts_dict.items():
                with self.subTest(
                        post_param=post_param,
                        test_post_param=test_post_param):
                    self.assertEqual(post_param, test_post_param)

    def test_group_list_page_correct_context(self):
        """Списка постов отфильтрованных по группе."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        group = response.context.get('group')
        self.assertIsNotNone(group)
        self.assertIsInstance(group, Group)

    def test_profile_page_correct_context_demo(self):
        """Постов отфильтрованных по пользователю."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        author = response.context.get('author')
        self.assertIsNotNone(author)
        self.assertIsInstance(author, User)

    def test_one_post_id_correct_context(self):
        """Проверка одного поста по id."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(
            response.context.get('post').author.posts.count(), 1)
        self.assertEqual(response.context.get('post').author, self.user)

    def test_create_post_show_correct_context(self):
        """Шаблоны create и edit сформированы с правильным контекстом."""
        namespace_list = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        ]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for urls in namespace_list:
            response = self.authorized_client.get(urls)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_appears_new_post(self):
        """При создании поста он должен появляется на главной странице,
        на странице выбранной группы и в профиле пользователя."""
        pages = [
            reverse('posts:index'),
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}),
            reverse(
                'posts:profile', kwargs={'username': self.user.username})
        ]
        for urls in pages:
            with self.subTest(urls=urls):
                response = self.authorized_client.get(urls)
                self.assertIn(self.post, response.context['page_obj'])

    def test_post_another_group(self):
        """Пост не попал в другую группу."""
        response = self.authorized_client.get(
            reverse('posts:group_list', args={self.group.slug}))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        first_object = response.context.get('page_obj')[0]
        self.assertTrue(first_object.text, 'Тестовый текст')


class PostPaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        for post_number in range(13):
            cls.post = Post.objects.create(
                text='Тестовый текст',
                author=cls.user,
                group=cls.group
            )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        """Проверка: количество постов на первой странице равно 10."""
        TEN_POSTS = 10
        namespace_list = {
            'posts:index': reverse('posts:index'),
            'posts:group_list': reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}),
            'posts:profile': reverse(
                'posts:profile', kwargs={'username': self.user.username}),
        }
        for template, reverse_name in namespace_list.items():
            response = self.guest_client.get(reverse_name)
            self.assertEqual(len(response.context['page_obj']), TEN_POSTS)

    def test_second_page_contains_three_records(self):
        """Проверка: количество постов на второй странице равно 3."""
        THREE_POSTS = 3
        namespace_list = {
            'posts:index': reverse('posts:index') + '?page=2',
            'posts:group_list': reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}) + '?page=2',
            'posts:profile': reverse(
                'posts:profile',
                kwargs={'username': self.user.username}) + '?page=2',
        }
        for template, reverse_name in namespace_list.items():
            response = self.guest_client.get(reverse_name)
            self.assertEqual(len(response.context['page_obj']), THREE_POSTS)


class CommentTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
        )
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий',
            post=cls.post,
            author=cls.user
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_add_comment(self):
        """После успешной отправки комментарий появляется на странице поста."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', args=[self.post.pk]))
        count_comments = 1
        self.assertEqual(len(response.context['comments']), count_comments)
        first_object = response.context['comments'][0]
        comment_text = first_object.text
        self.assertTrue(comment_text, 'Тестовый текст')


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title="Тестовый заголовок",
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            pub_date='Тестовая дата',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()

    def test_cache_index(self):
        """Тест кэширования главной страницы."""
        response = self.authorized_client.get(reverse('posts:index'))
        post = Post.objects.get(pk=1)
        post.text = 'Измененный текст'
        post.save()
        second_response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, second_response.content)
        post.delete()
        cache.clear()
        third_response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, third_response.content)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follower = User.objects.create_user(
            username='follower',
            email='test_follower_@mail.ru',
            password='test_password')
        cls.user_following = User.objects.create_user(
            username='following',
            email='test_following_@mail.ru',
            password='test_password')
        cls.post = Post.objects.create(
            author=cls.user_following,
            text='Тестовая запись для тестирования')

    def setUp(self):
        self.client_auth_follower = Client()
        self.client_auth_following = Client()
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following.force_login(self.user_following)

    def test_profile_follow(self):
        """Авторизованный пользователь может
        подписываться на других пользователей.
        """
        self.client_auth_follower.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user_following.username}))
        count_follower = 1
        self.assertEqual(Follow.objects.all().count(), count_follower)

    def test_profile_unfollow(self):
        """Авторизованный пользователь может
        удалять других пользователей из подписок.
        """
        self.client_auth_follower.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user_following.username}))
        count_follower = 0
        self.assertEqual(Follow.objects.all().count(), count_follower)

    def test_subscription(self):
        """Новая запись появляется в ленте тех, кто на него подписан."""
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        response = self.client_auth_follower.get('/follow/')
        post_text = response.context["page_obj"][0].text
        self.assertEqual(post_text, 'Тестовая запись для тестирования')

    def test_no_subscription(self):
        """Новая запись не появляется в ленте тех, кто не подписан."""
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        response = self.client_auth_following.get('/follow/')
        self.assertNotEqual(response, 'Тестовая запись для тестирования')
