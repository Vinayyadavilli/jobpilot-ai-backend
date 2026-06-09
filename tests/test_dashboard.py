import sys
import httpx
from datetime import datetime, timedelta, timezone
from app.database.session import SessionLocal
from app.repositories.user_repository import UserRepository
from app.repositories.job_repository import JobRepository
from app.repositories.interview_repository import InterviewRepository
from app.models.job import Job, JobStatus
from app.models.interview import Interview


def test_dashboard_flow():
    base_url = "http://localhost:8000/api/v1"
    test_email = "dashboard_test@example.com"
    test_password = "Password123!"

    print("--- Starting Dashboard Integration Tests ---")

    # 1. Clean up existing test data
    db = SessionLocal()
    try:
        user_repo = UserRepository(db)
        existing_user = user_repo.get_by_email(test_email)
        if existing_user:
            db.delete(existing_user)
            db.commit()
            print("Cleaned up existing test user.")
    except Exception as e:
        print(f"Error during cleanup: {e}")
    finally:
        db.close()

    # 2. Register
    print("Registering test user...")
    r = httpx.post(
        f"{base_url}/auth/register",
        json={"name": "Dashboard Tester", "email": test_email, "password": test_password}
    )
    assert r.status_code == 201, r.text
    
    # 3. Retrieve token and verify email
    db = SessionLocal()
    user_repo = UserRepository(db)
    user = user_repo.get_by_email(test_email)
    token = user.email_verification_token
    db.close()

    print(f"Verifying email with token: {token[:10]}...")
    r = httpx.get(f"{base_url}/auth/verify-email?token={token}")
    assert r.status_code == 200, r.text

    # 4. Login to get tokens
    print("Logging in...")
    r = httpx.post(
        f"{base_url}/auth/login",
        json={"email": test_email, "password": test_password}
    )
    assert r.status_code == 200, r.text
    tokens = r.json()
    access_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # 5. Check empty dashboard
    print("Checking empty dashboard...")
    r = httpx.get(f"{base_url}/dashboard/summary", headers=headers)
    assert r.status_code == 200, r.text
    summary = r.json()
    assert summary["total_applications"] == 0
    assert summary["success_rate"] == 0.0
    assert summary["interview_rate"] == 0.0
    assert summary["active_this_week"] == 0
    assert len(summary["top_companies"]) == 0
    for status in ["applied", "interviewing", "offered", "rejected", "withdrawn"]:
        assert summary["status_breakdown"][status] == 0

    # 6. Add multiple job applications with varied dates and statuses
    print("Adding test jobs...")
    today_str = datetime.utcnow().date().isoformat()
    old_date_str = (datetime.utcnow().date() - timedelta(days=10)).isoformat()

    jobs_to_create = [
        # Job A: Google, SWE, offered, today
        {"company": "Google", "role": "SWE", "status": "offered", "applied_date": today_str},
        # Job B: Google, SWE 2, applied, today
        {"company": "Google", "role": "SWE 2", "status": "applied", "applied_date": today_str},
        # Job C: Apple, SRE, interviewing, today
        {"company": "Apple", "role": "SRE", "status": "interviewing", "applied_date": today_str},
        # Job D: Facebook, PE, rejected, 10 days ago
        {"company": "Facebook", "role": "PE", "status": "rejected", "applied_date": old_date_str},
    ]

    created_jobs = []
    for job_data in jobs_to_create:
        r = httpx.post(f"{base_url}/jobs", json=job_data, headers=headers)
        assert r.status_code == 201, r.text
        created_jobs.append(r.json())

    # 7. Check populated dashboard summary
    print("Verifying populated dashboard summary...")
    r = httpx.get(f"{base_url}/dashboard/summary", headers=headers)
    assert r.status_code == 200, r.text
    summary = r.json()
    
    assert summary["total_applications"] == 4
    # Success rate: 1 offered / 4 total = 25.0%
    assert summary["success_rate"] == 25.0
    # Interview rate: 1 interviewing (Apple) / 4 total = 25.0%
    assert summary["interview_rate"] == 25.0
    # Active this week: Google (2) + Apple (1) = 3 jobs
    assert summary["active_this_week"] == 3
    
    # Status breakdown check
    assert summary["status_breakdown"]["offered"] == 1
    assert summary["status_breakdown"]["applied"] == 1
    assert summary["status_breakdown"]["interviewing"] == 1
    assert summary["status_breakdown"]["rejected"] == 1
    assert summary["status_breakdown"]["withdrawn"] == 0

    # Top companies check: Google has 2, Apple 1, Facebook 1
    top_cos = summary["top_companies"]
    assert len(top_cos) == 3
    assert top_cos[0]["company"] == "Google"
    assert top_cos[0]["count"] == 2
    
    # 8. Check application timeline
    print("Verifying timeline endpoint...")
    r = httpx.get(f"{base_url}/dashboard/timeline", headers=headers)
    assert r.status_code == 200, r.text
    timeline = r.json()["timeline"]
    # Should have data points for both today and 10 days ago
    assert len(timeline) == 2
    assert timeline[0]["date"] == old_date_str
    assert timeline[0]["count"] == 1
    assert timeline[1]["date"] == today_str
    assert timeline[1]["count"] == 3

    # 9. Verify by-status endpoint
    print("Verifying by-status endpoint...")
    r = httpx.get(f"{base_url}/dashboard/by-status", headers=headers)
    assert r.status_code == 200, r.text
    by_status = r.json()
    assert by_status["offered"] == 1
    assert by_status["applied"] == 1
    assert by_status["interviewing"] == 1
    assert by_status["rejected"] == 1
    assert by_status["withdrawn"] == 0

    # 10. Test interview count logic in interview_rate (Job B has interview scheduled)
    print("Adding an interview to a job to verify interview rate logic...")
    # Find Google SWE 2 job
    job_b_id = [j["id"] for j in created_jobs if j["company"] == "Google" and j["role"] == "SWE 2"][0]
    
    interview_data = {
        "round": "Technical Phone Screen",
        "interview_type": "phone",
        "scheduled_at": (datetime.utcnow() + timedelta(days=2)).isoformat() + "Z",
        "status": "scheduled",
        "feedback": "Looking forward to it",
        "interviewer_name": "John Doe"
    }
    r = httpx.post(f"{base_url}/jobs/{job_b_id}/interviews", json=interview_data, headers=headers)
    assert r.status_code == 201, r.text

    # Re-fetch dashboard summary
    r = httpx.get(f"{base_url}/dashboard/summary", headers=headers)
    assert r.status_code == 200, r.text
    summary = r.json()
    # Now both Google SWE 2 (has interview scheduled) and Apple SRE (has status interviewing) should count towards interview rate
    # So 2 / 4 = 50.0%
    assert summary["interview_rate"] == 50.0

    # 11. Cleanup test user
    db = SessionLocal()
    try:
        user_repo = UserRepository(db)
        user = user_repo.get_by_email(test_email)
        if user:
            db.delete(user)
            db.commit()
            print("Cleaned up test user successfully.")
    finally:
        db.close()

    print("✅ All dashboard integration tests PASSED successfully!")


if __name__ == "__main__":
    test_dashboard_flow()
