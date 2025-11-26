"""
Simple test for signup APIs using Django's test framework
Run with: pipenv run python manage.py test scheduling.tests_signup
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from scheduling.models import UserProfile, Agent, Client as ClientModel, AgentSettings
import json


class SignupAPITestCase(TestCase):
    """Test cases for agent and client signup APIs"""
    
    def setUp(self):
        """Set up test client"""
        self.client = Client()
    
    def test_agent_signup_success(self):
        """Test successful agent registration"""
        data = {
            "username": "dr_smith",
            "email": "dr.smith@hospital.com",
            "password": "securepass123",
            "first_name": "John",
            "last_name": "Smith",
            "phone": "555-0101"
        }
        
        response = self.client.post(
            '/api/signup/agent/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        
        # Verify User was created
        user = User.objects.get(username="dr_smith")
        self.assertEqual(user.email, "dr.smith@hospital.com")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Smith")
        
        # Verify UserProfile was created
        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.user_type, "agent")
        self.assertEqual(profile.phone, "555-0101")
        
        # Verify Agent was created
        agent = Agent.objects.get(user=user)
        self.assertEqual(agent.email, "dr.smith@hospital.com")
        self.assertTrue(agent.active)
        
        # Verify AgentSettings was created
        settings = AgentSettings.objects.get(agent_id=agent.id)
        self.assertEqual(settings.daily_caps, 10)
        self.assertEqual(settings.weekly_caps, 50)
    
    def test_client_signup_success(self):
        """Test successful client registration"""
        data = {
            "username": "jane_doe",
            "email": "jane.doe@email.com",
            "password": "clientpass123",
            "first_name": "Jane",
            "last_name": "Doe",
            "phone": "555-0202",
            "date_of_birth": "1990-05-15",
            "address": "123 Main St"
        }
        
        response = self.client.post(
            '/api/signup/client/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        
        # Verify User was created
        user = User.objects.get(username="jane_doe")
        self.assertEqual(user.email, "jane.doe@email.com")
        
        # Verify UserProfile was created
        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.user_type, "client")
        
        # Verify Client was created
        client = ClientModel.objects.get(user=user)
        self.assertEqual(client.address, "123 Main St")
    
    def test_duplicate_username(self):
        """Test that duplicate usernames are rejected"""
        # Create first user
        User.objects.create_user(username="existing_user", email="first@email.com", password="pass123")
        
        # Try to create another user with same username
        data = {
            "username": "existing_user",
            "email": "different@email.com",
            "password": "password123",
            "first_name": "Another",
            "last_name": "User",
            "phone": "555-9999"
        }
        
        response = self.client.post(
            '/api/signup/agent/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("Username already exists", response.json()['error'])
    
    def test_duplicate_email(self):
        """Test that duplicate emails are rejected"""
        # Create first user
        User.objects.create_user(username="user1", email="same@email.com", password="pass123")
        
        # Try to create another user with same email
        data = {
            "username": "user2",
            "email": "same@email.com",
            "password": "password123",
            "first_name": "Another",
            "last_name": "User",
            "phone": "555-9999"
        }
        
        response = self.client.post(
            '/api/signup/client/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("Email already exists", response.json()['error'])
    
    def test_missing_required_fields(self):
        """Test that missing required fields are caught"""
        data = {
            "username": "incomplete_user",
            "email": "incomplete@email.com",
            # Missing password, first_name, last_name
        }
        
        response = self.client.post(
            '/api/signup/agent/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing required fields", response.json()['error'])
    
    def test_invalid_date_format(self):
        """Test that invalid date formats are rejected"""
        data = {
            "username": "test_user",
            "email": "test@email.com",
            "password": "pass123",
            "first_name": "Test",
            "last_name": "User",
            "phone": "555-0000",
            "date_of_birth": "invalid-date"
        }
        
        response = self.client.post(
            '/api/signup/client/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid date_of_birth format", response.json()['error'])
