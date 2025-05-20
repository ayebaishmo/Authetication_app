from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class AuthTests(APITestCase):

    def setUp(self):
        self.register_url = reverse('user-register')
        self.token_obtain_url = reverse('token_obtain_pair')
        self.token_refresh_url = reverse('token_refresh')
        self.user_list_url = reverse('user-list-create')

        # Common user data
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpassword123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        self.user_credentials = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }

    # --- User Registration Tests ---
    def test_successful_user_registration(self):
        """
        Ensure users can register successfully.
        """
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email=self.user_data['email']).exists())
        user = User.objects.get(email=self.user_data['email'])
        self.assertEqual(user.first_name, self.user_data['first_name'])

    def test_registration_missing_email(self):
        """
        Ensure registration fails if email is missing.
        """
        data = self.user_data.copy()
        del data['email']
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_registration_missing_password(self):
        """
        Ensure registration fails if password is missing.
        """
        data = self.user_data.copy()
        del data['password']
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_registration_existing_email(self):
        """
        Ensure registration fails if email already exists.
        """
        # Create a user first
        User.objects.create_user(**self.user_data)
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data) 

    # --- Token Generation (Login) Tests ---
    def test_successful_token_generation(self):
        """
        Ensure tokens are generated for valid credentials.
        """
        User.objects.create_user(**self.user_data) # Create the user
        response = self.client.post(self.token_obtain_url, self.user_credentials, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_token_generation_invalid_password(self):
        """
        Ensure token generation fails for invalid password.
        """
        User.objects.create_user(**self.user_data) # Create the user
        invalid_credentials = self.user_credentials.copy()
        invalid_credentials['password'] = 'wrongpassword'
        response = self.client.post(self.token_obtain_url, invalid_credentials, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_generation_non_existent_user(self):
        """
        Ensure token generation fails for a non-existent user.
        """
        response = self.client.post(self.token_obtain_url, self.user_credentials, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Token Refresh Tests ---
    def test_successful_token_refresh(self):
        """
        Ensure refresh token can be used to obtain a new access token.
        """
        User.objects.create_user(**self.user_data)
        login_response = self.client.post(self.token_obtain_url, self.user_credentials, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        refresh_token = login_response.data['refresh']
        
        refresh_response = self.client.post(self.token_refresh_url, {'refresh': refresh_token}, format='json')
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)
        self.assertNotIn('refresh', refresh_response.data) 

    def test_token_refresh_invalid_token(self):
        """
        Ensure refreshing with an invalid token fails.
        """
        response = self.client.post(self.token_refresh_url, {'refresh': 'invalidtoken'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Protected View Access Tests ---
    def test_access_protected_view_without_token(self):
        """
        Ensure accessing protected view without token is forbidden.
        """
        response = self.client.get(self.user_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_access_protected_view_with_valid_token(self):
        """
        Ensure accessing protected view with valid token is successful.
        """
        User.objects.create_user(**self.user_data)
        login_response = self.client.post(self.token_obtain_url, self.user_credentials, format='json')
        access_token = login_response.data['access']
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.user_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_access_protected_view_with_invalid_token(self):
        """
        Ensure accessing protected view with invalid token is forbidden.
        """
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalidtoken')
        response = self.client.get(self.user_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_access_protected_view_with_expired_token(self):
        """
        Ensure accessing protected view with an (effectively) expired token is forbidden.
        This test uses a refresh token in place of an access token, which should be rejected.
        """
        User.objects.create_user(**self.user_data)
        login_response = self.client.post(self.token_obtain_url, self.user_credentials, format='json')
        refresh_token = login_response.data['refresh'] # Using refresh token as access token

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh_token}')
        response = self.client.get(self.user_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED) 
        self.assertIn('detail', response.data) 

    def tearDown(self):
        # APITestCase handles transaction rollback, so manual cleanup is usually not needed.
        pass
