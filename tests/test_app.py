"""
Tests for the FastAPI application
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state after each test"""
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Competitive basketball team for intramural and inter-school tournaments",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["alex@mergington.edu"]
        },
        "Soccer Club": {
            "description": "Join our soccer team and develop your skills on the field",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 18,
            "participants": ["sarah@mergington.edu", "james@mergington.edu"]
        },
        "Drama Club": {
            "description": "Perform in theatrical productions and develop acting skills",
            "schedule": "Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 25,
            "participants": ["isabella@mergington.edu"]
        },
        "Digital Art Studio": {
            "description": "Create digital artwork, animations, and graphic design projects",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 16,
            "participants": ["lucas@mergington.edu", "mia@mergington.edu"]
        },
        "Debate Team": {
            "description": "Compete in debate tournaments and develop public speaking skills",
            "schedule": "Mondays, 3:30 PM - 4:30 PM",
            "max_participants": 10,
            "participants": ["david@mergington.edu"]
        },
        "Science Club": {
            "description": "Explore scientific concepts through experiments and research projects",
            "schedule": "Fridays, 4:00 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["aisha@mergington.edu", "ryan@mergington.edu"]
        }
    }
    
    yield
    
    # Reset to original state
    activities.clear()
    activities.update(original_activities)


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert len(data) == 9
    
    def test_activities_contain_required_fields(self, client):
        """Test that each activity contains required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_info in data.items():
            assert "description" in activity_info
            assert "schedule" in activity_info
            assert "max_participants" in activity_info
            assert "participants" in activity_info
            assert isinstance(activity_info["participants"], list)
    
    def test_activities_have_participants(self, client):
        """Test that activities have participants"""
        response = client.get("/activities")
        data = response.json()
        
        # Check that at least some activities have participants
        has_participants = any(
            len(activity["participants"]) > 0 
            for activity in data.values()
        )
        assert has_participants


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_for_activity_success(self, client, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball Team/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Basketball Team"]["participants"]
    
    def test_signup_nonexistent_activity(self, client):
        """Test signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_signup_duplicate_email(self, client, reset_activities):
        """Test signup with duplicate email returns 400"""
        # Try to signup with an email that's already registered
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Student is already signed up"
    
    def test_signup_new_email_same_activity_twice(self, client, reset_activities):
        """Test that same email cannot signup twice for same activity"""
        email = "test@mergington.edu"
        activity = "Soccer Club"
        
        # First signup should succeed
        response1 = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response2.status_code == 400
        assert response2.json()["detail"] == "Student is already signed up"
    
    def test_signup_response_format(self, client, reset_activities):
        """Test that signup response has correct format"""
        response = client.post(
            "/activities/Drama Club/signup?email=drama@mergington.edu"
        )
        data = response.json()
        assert "message" in data
        assert "Signed up" in data["message"]
        assert "drama@mergington.edu" in data["message"]
        assert "Drama Club" in data["message"]


class TestRootEndpoint:
    """Tests for GET / endpoint"""
    
    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestIntegration:
    """Integration tests"""
    
    def test_full_signup_workflow(self, client, reset_activities):
        """Test full signup workflow"""
        # Get activities
        activities_response = client.get("/activities")
        assert activities_response.status_code == 200
        activities_data = activities_response.json()
        initial_participants = len(activities_data["Debate Team"]["participants"])
        
        # Sign up for activity
        signup_response = client.post(
            "/activities/Debate Team/signup?email=newspeaker@mergington.edu"
        )
        assert signup_response.status_code == 200
        
        # Verify participant was added
        updated_response = client.get("/activities")
        updated_data = updated_response.json()
        assert len(updated_data["Debate Team"]["participants"]) == initial_participants + 1
        assert "newspeaker@mergington.edu" in updated_data["Debate Team"]["participants"]
