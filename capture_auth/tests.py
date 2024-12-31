from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import User
from unittest.mock import patch
 
class SignUpViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.signup_url = reverse('signup')
        self.signin_url = reverse('signin')
        self.user_data = {
            'username': 'testuser',
            'password': 'Test@1234',
            'email': 'testuser@example.com',
        }
 
    @patch('django.core.mail.send_mail')  # Mock the email sending to avoid actually sending emails
    def test_user_signup_success(self, mock_send_mail):
        response = self.client.post(self.signup_url, self.user_data)
        # Check if the user was created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username=self.user_data['username']).exists())
        self.assertEqual(response.data['username'], self.user_data['username'])
        mock_send_mail.assert_called_once()  # Ensure email sending was called once
 
    def test_user_signup_invalid_data(self):
        # Invalid data (missing username, invalid email)
        response = self.client.post(self.signup_url, {
            'username': '',
            'password': 'short',
            'email': 'invalid-email'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    def test_user_signin(self):
        # First, sign up the user to ensure the user exists in the database
        self.client.post(self.signup_url, self.user_data)
        
        # Now attempt to sign in with the same credentials
        response = self.client.post(self.signin_url, {
            'username': self.user_data['username'],
            'password': self.user_data['password']
        })
        
        # Check if the response status is 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_user_signin_invalid_creds(self):
        # First, sign up the user to ensure the user exists in the database
        self.client.post(self.signup_url, self.user_data)
        
        # Now attempt to sign in with the same credentials
        response = self.client.post(self.signin_url, {
            'username': 'wrong',
            'password': self.user_data['password']
        })
        
        # Check if the response status is 200 OK
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        