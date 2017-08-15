import unittest
import json

from playhouse.test_utils import test_database
from peewee import *

from app import app
from models import User, Todo

USER_DATA = {
    'username': 'tester',
    'email': 'testemail@email.com',
    'password': 'password 1',
    'verify_password': 'password 1'
}

TODO_LIST = ['Pay Bills', 'Study', 'Work out']


class TodoModelTestCase(unittest.TestCase):
    def test_todo_model(self):
        with test_database(TEST_DB, (Todo, )):
            Todo.create(name='Test todo entry')
            self.assertEqual(Todo.select().count(), 1)


class ViewModelTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = True
        self.app = app.test_client()

    def create_todos(self):
        for todo in TODO_LIST:
            Todo.create(name=todo)

    def create_user(self):
        return User.create_user(**USER_DATA)




class TodoResourceTestCase(ViewModelTestCase):

    def test_get_todos(self):
        with test_database(TEST_DB, (Todo,)):
            self.create_todos()
            rv = self.app.get('/api/v1/todos')
            self.assertEqual(rv.status_code, 200)
            self.assertEqual(Todo.select().count(), 3)
            self.assertIn('Study', rv.get_data(as_text=True))

    def test_single_todo(self):
        with test_database(TEST_DB, (Todo,)):
            self.create_todos()
            rv = self.app.get('/api/v1/todos/2')
            self.assertEqual(rv.status_code, 200)
            self.assertIn('Study', rv.get_data(as_text=True))

    def test_post_todo(self):
        with test_database(TEST_DB, (Todo,)):
            rv = self.app.post('api/v1/todos', data={'name': 'Todo'})
            self.assertEqual(rv.status_code, 201)
            self.assertIn('Todo', rv.get_data(as_text=True))

    def test_update_todo(self):
        with test_database(TEST_DB, (Todo,)):
            self.create_todos()
            rv = self.app.put('api/v1/todos/1', data={'name': 'Todo Updated'})
            self.assertEqual(rv.status_code, 200)
            self.assertIn('Todo Updated', rv.get_data(as_text=True))

    def test_delete_todo(self):
        with test_database(TEST_DB, (Todo,)):
            user = User.get(User.id == 1)
            token = user.generate_auth_token().decode('ascii')
            headers = {'Authorization': 'Token'.format(token)}
            self.create_todos()
            resp = self.app.delete('api/v1/todos/2', headers=headers)
            #resp_data = json.loads(resp.data.decode())
            self.assertEqual(resp.status_code, 204)
            self.assertNotIn('Study', resp.get_data(as_text=True))

    def test_authorized_add_todo(self):
        with test_database(TEST_DB, (Todo,)):
            user = User.get(User.id==1)
            token = user.generate_auth_token().decode('ascii')
            headers = {'Authorization': 'Token'.format(token)}
            resp = self.app.post('api/v1/todos', data={'name': 'Wash car'}, headers=headers)
            resp_data = json.loads(resp.data.decode())
            self.assertEqual(resp.status_code, 201)
            self.assertIn( 'Wash car', resp_data['name'])


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSF_ENABLED'] = False
        self.app = app
        self.client = app.test_client()

    @staticmethod
    def create_users(count=2):
        for i in range(count):
            User.create_user(
                username='test{}'.format(i),
                email='test{}@email.com'.format(i),
                password='password {}'.format(i)
            )

    def test_database(self):
        with test_database(TEST_DB, (User,)):
            self.create_users()
            self.assertEqual(User.select().count(), 2)
            self.assertNotEqual(
                User.select().get().password,
                'password 1'
            )


if __name__ == '__main__':
    TEST_DB = SqliteDatabase(':memory:')
    TEST_DB.connect()
    TEST_DB.create_tables([User, Todo], safe=True)
    unittest.main()
