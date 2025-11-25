"""
Tests for authentication endpoints.
"""
import pytest
from fastapi import status


class TestLogin:
    """Test login endpoint."""
    
    def test_login_success(self, client, sample_student):
        """Test successful login."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "teststudent@umd.edu",
                "password": "password123"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "token" in data
        assert data["user"]["email"] == "teststudent@umd.edu"
        assert data["user"]["role"] == "student"
    
    def test_login_invalid_credentials(self, client, sample_student):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "teststudent@umd.edu",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["success"] is False
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@umd.edu",
                "password": "password123"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestRegister:
    """Test registration endpoint."""
    
    def test_register_success(self, client):
        """Test successful registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newstudent@umd.edu",
                "password": "password123",
                "name": "New Student",
                "role": "student"
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        assert "token" in data
        assert data["user"]["email"] == "newstudent@umd.edu"
    
    def test_register_duplicate_email(self, client, sample_student):
        """Test registration with duplicate email."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "teststudent@umd.edu",
                "password": "password123",
                "name": "Duplicate Student",
                "role": "student"
            }
        )
        
        assert response.status_code == status.HTTP_409_CONFLICT
    
    def test_register_invalid_email(self, client):
        """Test registration with non-UMD email."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "student@gmail.com",
                "password": "password123",
                "name": "Invalid Student",
                "role": "student"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestTokenValidation:
    """Test token validation endpoint."""
    
    def test_validate_valid_token(self, client, sample_student):
        """Test validation with valid token."""
        # Login first
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "teststudent@umd.edu",
                "password": "password123"
            }
        )
        token = login_response.json()["token"]
        
        # Validate token
        response = client.get(
            "/api/auth/validate",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["valid"] is True
        assert data["user"]["email"] == "teststudent@umd.edu"
    
    def test_validate_invalid_token(self, client):
        """Test validation with invalid token."""
        response = client.get(
            "/api/auth/validate",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetCurrentUser:
    """Test get current user endpoint."""
    
    def test_get_current_user_success(self, client, sample_student):
        """Test getting current user info."""
        # Login first
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "teststudent@umd.edu",
                "password": "password123"
            }
        )
        token = login_response.json()["token"]
        
        # Get user info
        response = client.get(
            "/api/auth/user",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "teststudent@umd.edu"
        assert data["name"] == "Test Student"


class TestLogout:
    """Test logout endpoint."""
    
    def test_logout_success(self, client, sample_student):
        """Test successful logout."""
        # Login first
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "teststudent@umd.edu",
                "password": "password123"
            }
        )
        token = login_response.json()["token"]
        
        # Logout
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
