"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    from src.app import activities
    
    # Store original state
    original_activities = {
        name: {
            "description": activity["description"],
            "schedule": activity["schedule"],
            "max_participants": activity["max_participants"],
            "participants": activity["participants"].copy()
        }
        for name, activity in activities.items()
    }
    
    yield
    
    # Restore original state
    activities.clear()
    for name, original in original_activities.items():
        activities[name] = {
            "description": original["description"],
            "schedule": original["schedule"],
            "max_participants": original["max_participants"],
            "participants": original["participants"].copy(),
        }


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_success(self, client, reset_activities):
        """Test successfully retrieving all activities"""
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify it's a dictionary with activities
        assert isinstance(data, dict)
        assert len(data) > 0
        
        # Verify activity structure
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)

    def test_get_activities_contains_expected_activities(self, client, reset_activities):
        """Test that the response contains expected activities"""
        response = client.get("/activities")
        data = response.json()
        
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]
        for activity in expected_activities:
            assert activity in data


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client, reset_activities):
        """Test successfully signing up for an activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_signup_duplicate_email(self, client, reset_activities):
        """Test that a student cannot sign up twice for the same activity"""
        # First signup
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        assert response1.status_code == 400
        
        # Verify error message
        data = response1.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test signing up for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_signup_updates_participant_list(self, client, reset_activities):
        """Test that signup actually adds the participant to the activity"""
        # Get initial state
        initial_response = client.get("/activities")
        initial_data = initial_response.json()
        initial_count = len(initial_data["Programming Class"]["participants"])
        
        # Sign up new student
        client.post(
            "/activities/Programming Class/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        # Get updated state
        updated_response = client.get("/activities")
        updated_data = updated_response.json()
        updated_count = len(updated_data["Programming Class"]["participants"])
        
        # Verify participant was added
        assert updated_count == initial_count + 1
        assert "newstudent@mergington.edu" in updated_data["Programming Class"]["participants"]


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/signup endpoint"""

    def test_unregister_success(self, client, reset_activities):
        """Test successfully unregistering from an activity"""
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]

    def test_unregister_not_registered(self, client, reset_activities):
        """Test unregistering a student who is not registered"""
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": "notregistered@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not registered" in data["detail"].lower()

    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Test unregistering from an activity that doesn't exist"""
        response = client.delete(
            "/activities/Nonexistent Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister actually removes the participant"""
        # Get initial state
        initial_response = client.get("/activities")
        initial_data = initial_response.json()
        initial_count = len(initial_data["Chess Club"]["participants"])
        
        # Unregister student
        client.delete(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        
        # Get updated state
        updated_response = client.get("/activities")
        updated_data = updated_response.json()
        updated_count = len(updated_data["Chess Club"]["participants"])
        
        # Verify participant was removed
        assert updated_count == initial_count - 1
        assert "michael@mergington.edu" not in updated_data["Chess Club"]["participants"]
