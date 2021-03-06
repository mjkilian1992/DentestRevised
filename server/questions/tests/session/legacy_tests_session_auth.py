import json
from django.test import TestCase
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient
from rest_framework import status
from questions.models import *

#  Create your test_sessions here.

class QuestionAPITestCase(TestCase):
    def setUp(self):
        #  Create groups with name matching Privileged Groups
        self.bronze = Group(name='Bronze')
        self.bronze.save()
        self.silver = Group(name='Silver')
        self.silver.save()

        #  Create one bronze, one silver and one staff user
        self.bronze_user = User.objects.create_user('test_session_bronze',
                                                    'bronze@fake.com',
                                                    'password1',
                                                    )
        self.bronze_user.groups.add(self.bronze)
        self.bronze_user.save()

        self.silver_user = User.objects.create_user('test_session_silver',
                                                    'silver@fake.com',
                                                    'password2',
                                                    )
        self.silver_user.groups.add(self.silver)
        self.silver_user.save()

        self.staff_user = User.objects.create_user('test_session_staff',
                                                   'staff@fake.com',
                                                   'password3',
                                                   )
        self.staff_user.is_staff = True
        self.staff_user.save()

        #  Create APIFactory and Client
        self.client = APIClient()

        #  Populate database
        #  Mixed
        t1 = Topic.objects.create(name='Topic 1', description='The first topic.')
        # Only restricted questions
        t2 = Topic.objects.create(name='Topic 2', description='The second topic.')
        # Empty
        t3 = Topic.objects.create(name='Topic 3', description='The third topic.')

        #  Mixed
        s1 = Subtopic.objects.create(name='Subtopic 1',
                                     topic=t1,
                                     description='The first subtopic of topic 1.')
        #  All restricted
        s2 = Subtopic.objects.create(name='Subtopic 2',
                                     topic=t1,
                                     description='The second subtopic of topic 1.')
        s3 = Subtopic.objects.create(name='Subtopic 3',
                                     topic=t2,
                                     description='The first subtopic of topic 2.')
        #  Empty
        s4 = Subtopic.objects.create(name='Subtopic 4',
                                     topic=t2,
                                     description='The second subtopic of topic 2.')

        q1 = Question.objects.create(id=1,
                                     question='What is my name?',
                                     answer='Test',
                                     subtopic=s1,
                                     restricted=False)
        q2 = Question.objects.create(id=2,
                                     question='What app is this?',
                                     answer='Dentest_session',
                                     subtopic=s1,
                                     restricted=True)
        q3 = Question.objects.create(id=3,
                                     question='Have I run out of questions?',
                                     answer='Nope',
                                     subtopic=s2,
                                     restricted=True)
        q4 = Question.objects.create(id=4,
                                     question='What about now?',
                                     answer="Yeah, I've ran out...",
                                     subtopic=s3,
                                     restricted=True)

    def tearDown(self):
        #  Destroy all database entities
        User.objects.all().delete()
        Group.objects.all().delete()
        Question.objects.all().delete()
        Subtopic.objects.all().delete()
        Topic.objects.all().delete()
        self.client = None


    def test_session_topic_retrieval_unauthenticated(self):
        """Check an unauthenticated user cant access Topics"""
        response = self.client.get('/topics/', format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_session_topic_retrieval_authenticated(self):
        """Check any authenticated user can access all topics"""
        self.client.login(username='test_session_bronze', password='password1')
        response = self.client.get('/topics/', format='json')
        data = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue({'name': 'Topic 1', 'description': 'The first topic.'} in data)
        self.assertTrue({'name': 'Topic 2', 'description': 'The second topic.'} in data)
        self.client.logout()


    def test_session_topic_submission_unauthenticated(self):
        """Test that an attempt to add a topic by an unauthenticated user fails"""
        topic_data = {'name': 'PostedTopic'}
        #  Try with unauthenticated user (should fail)
        response = self.client.post('/topics/', topic_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_session_topic_submission_non_staff(self):
        """Test that an attempt to add a topic by a non-staff user fails"""
        topic_data = {'name': 'PostedTopic'}
        #  Try with bronze authenticated
        self.client.login(username='test_session_bronze', password='password1')
        response = self.client.post('/topics/', topic_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.logout()

        # Try with silver authenticated
        self.client.login(email='silver@fake.com', password='password2')
        response = self.client.post('/topics/', topic_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.logout()

    def test_session_topic_submission_staff(self):
        """Check that staff can POST new topics"""
        topic_data = {'name': 'PostedTopic'}
        #  Try with staff user
        self.client.login(username='test_session_staff', password='password3')
        response = self.client.post('/topics/', topic_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Topic.objects.get(name='PostedTopic'))
        self.client.logout()

    def test_session_subtopic_retrieval_unauthenticated(self):
        """Check an unauthenticated user cant access Subtopics"""
        response = self.client.get('/subtopics/', format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_session_subtopic_retrieval_authenticated(self):
        """Check any authenticated user can access all Subtopics"""
        self.client.login(username='test_session_bronze', password='password1')
        response = self.client.get('/subtopics/', format='json')
        data = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        #  Ordering should be by Topic name, then Subtopic name
        #  Returned value will be in unicode
        self.assertEqual(str(data[0]['name']), 'Subtopic 1')
        self.assertEqual(str(data[1]['name']), 'Subtopic 2')
        self.assertEqual(str(data[2]['name']), 'Subtopic 3')
        self.client.logout()

    def test_session_subtopic_submission_unauthenticated(self):
        """Test that an attempt to add a subtopic by an unauthenticated user fails"""
        subtopic_data = {'name': 'PostedSubtopic',
                         'topic': 'Topic 1',
                         'description': 'A user posted subtopic.'}
        #  Try with unauthenticated user (should fail)
        response = self.client.post('/subtopics/', subtopic_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_session_subtopic_submission_non_staff(self):
        """Test that an attempt to add a subtopic by a non-staff user fails"""
        subtopic_data = {'name': 'PostedSubtopic',
                         'topic': 'Topic 1',
                         'description': 'A user posted subtopic.'}
        #  Try with bronze authenticated
        self.client.login(username='test_session_bronze', password='password1')
        response = self.client.post('/subtopics/', subtopic_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.logout()

        # Try with silver authenticated
        self.client.login(email='silver@fake.com', password='password2')
        response = self.client.post('/topics/', subtopic_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.logout()

    def test_session_subtopic_submission_staff(self):
        """Check that staff can POST new subtopics"""
        subtopic_data = {'name': 'PostedSubtopic',
                         'topic': 'Topic 1',
                         'description': 'A user posted subtopic.'}
        #  Try with staff user
        self.client.login(username='test_session_staff', password='password3')
        response = self.client.post('/subtopics/', subtopic_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Subtopic.objects.get(name='PostedSubtopic'))
        self.client.logout()

    def test_session_all_question_retrieval_unauthenticated(self):
        """Check an unauthenticated user can't access questions"""
        response = self.client.get('/questions/', format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_session_all_questions_retrieval_unprivileged(self):
        """Check a basic user can only access non-restricted questions"""
        self.client.login(username='test_session_bronze', password='password1')
        response = self.client.get('/questions/', format='json')
        data = json.loads(response.content)

        self.assertFalse(data[0]['restricted'])
        self.assertEqual(str(data[0]['question']), 'What is my name?')
        self.assertEqual(str(data[0]['subtopic']['topic']), 'Topic 1')
        self.assertEqual(len(data), 1)
        self.client.logout()

    def test_session_all_question_retrieval_privileged(self):
        """Check a privileged user can access all questions"""
        self.client.login(username='test_session_silver', password='password2')
        response = self.client.get('/questions/', format='json')
        data = json.loads(response.content)
        self.assertEqual(len(data), 4)
        self.client.logout()

    def test_session_all_question_retrieval_staff(self):
        """Check a staff member can access all questions"""
        self.client.login(username='test_session_staff', password='password3')
        response = self.client.get('/questions/', format='json')
        data = json.loads(response.content)
        self.assertEqual(len(data), 4)
        self.client.logout()


    def test_session_fetch_question_by_id_unauthenticated(self):
        """Check an unauthenticated user cant access individual questions"""
        response = self.client.get('/questions/', {'question': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_session_fetch_question_by_id_unprivileged(self):
        """An unprivileged user should only be able to access non-restricted questions"""
        self.client.login(username='test_session_bronze', password='password1')
        #  Try on non-restricted question. Make sure only one is returned
        response = self.client.get('/questions/', {'question': 1}, format='json')
        data = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data[0]['id'], 1)
        self.assertEqual(len(data), 1)

        #  Now try a restricted question. Should fail
        response = self.client.get('/questions/', {'question': 2}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_session_fetch_question_by_id_privileged(self):
        """A privileged user can access any question"""
        self.client.login(username='test_session_silver', password='password2')
        response = self.client.get('/questions/', {'question': 2}, format='json')
        data = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data[0]['id'], 2)
        self.assertEqual(len(data), 1)
        self.client.logout()

    def test_session_fetch_question_by_id_staff(self):
        """A staff user can also access privileged questions"""
        self.client.login(username='test_session_staff', password='password3')
        response = self.client.get('/questions/', {'question': 2}, format='json')
        data = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data[0]['id'], 2)
        self.assertEqual(len(data), 1)
        self.client.logout()

    def test_session_fetch_by_topic_unauthenticated(self):
        """An unauthenticated user cant access anything"""
        response = self.client.get('/questions/', {'topic': 'Topic 1'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_session_fetch_by_topic_unprivileged(self):
        """Basic user should only see the unrestricted questions in the topic"""
        self.client.login(username='test_session_bronze', password='password1')
        response = self.client.get('/questions/', {'topic': 'Topic 1'}, format='json')
        data = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['subtopic']['topic'], 'Topic 1')
        self.assertEqual(data[0]['id'], 1)
        self.client.logout()

    def test_session_fetch_by_topic_unprivileged_all_restricted(self):
        """If a topic exists, the user is restricted from viewing all its questions, 403 should be returned"""
        self.client.login(username='test_session_bronze', password='password1')
        response = self.client.get('/questions/', {'topic': 'Topic 2'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.logout()

    def test_session_fetch_by_topic_privileged(self):
        """Privileged user can view all questions in any topic"""
        self.client.login(username='test_session_silver', password='password2')
        response = self.client.get('/questions/', {'topic': 'Topic 1'}, format='json')
        data = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 3)

        #  Questions should always be ordered by Subtopic then ID
        self.assertEqual(data[0]['subtopic']['topic'], 'Topic 1')
        self.assertEqual(data[0]['id'], 1)
        self.assertEqual(data[1]['subtopic']['topic'], 'Topic 1')
        self.assertEqual(data[1]['id'], 2)
        self.client.logout()

    def test_session_fetch_unknown_topic(self):
        """Filtering on a non existent topic should return a 404 error"""
        self.client.login(username='test_session_bronze', password='password1')
        response = self.client.get('/questions/', {'topic': 'NonExistentTopic'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.client.logout()

    def test_session_fetch_empty_topic(self):
        """Filtering on an empty topic should also return 404 (no QUESTIONS could be found)"""
        self.client.login(username='test_session_bronze', password='password1')
        response = self.client.get('/questions/', {'topic': 'Topic 3'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.client.logout()

    def test_session_fetch_by_subtopic_unprivleged(self):
        """Basic users should only be able to see unrestricted questions"""
        self.client.login(username='test_session_bronze', password='password1')
        response = self.client.get('/questions/', {'topic': 'Topic 1', 'subtopic': 'Subtopic 1'}, format='json')
        data = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['subtopic']['topic'], 'Topic 1')
        self.assertEqual(data[0]['subtopic']['name'], 'Subtopic 1')
        self.assertEqual(data[0]['id'], 1)

    def test_session_fetch_by_subtopic_privilieged(self):
        """Privileged user can see all the questions in a subtopic"""
        self.client.login(username='test_session_silver', password='password2')
        response = self.client.get('/questions/', {'topic': 'Topic 1', 'subtopic': 'Subtopic 1'}, format='json')
        data = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['subtopic']['topic'], 'Topic 1')
        self.assertEqual(data[0]['subtopic']['name'], 'Subtopic 1')
        self.assertEqual(data[0]['id'], 1)
        self.assertEqual(data[1]['subtopic']['topic'], 'Topic 1')
        self.assertEqual(data[1]['subtopic']['name'], 'Subtopic 1')
        self.assertEqual(data[1]['id'], 2)

    def test_session_fetch_by_subtopic_unprivileged_all_restricted(self):
        """If all questions in the subtopic are restricted, 403 should be returned"""
        self.client.login(username='test_session_bronze', password='password1')
        response = self.client.get('/questions/', {'topic': 'Topic 1', 'subtopic': 'Subtopic 2'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_session_fetch_by_subtopic_unknown_subtopic(self):
        """If no such subtopic exists, should return 404"""
        self.client.login(username='test_session_bronze', password='password1')
        response = self.client.get('/questions/', {'topic': 'Topic 1', 'subtopic': 'NonExistantSubtopic'},
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_session_fetch_by_subtopic_empty_subtopic(self):
        """If the subtopic is empty then 404 should be returned (no QUESTIONS found)"""
        self.client.login(username='test_session_bronze', password='password1')
        response = self.client.get('/questions/', {'topic': 'Topic 2', 'subtopic': 'Subtopic 4'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)