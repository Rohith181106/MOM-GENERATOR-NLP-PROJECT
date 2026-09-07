import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.app.core.database import init_db

@pytest.mark.asyncio
async def test_full_application_flow():
    await init_db()
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Health Check
        health_resp = await ac.get("/api/health")
        assert health_resp.status_code == 200
        assert health_resp.json()["status"] == "healthy"

        # 2. Benchmark Endpoint
        bm_resp = await ac.get("/api/benchmark")
        assert bm_resp.status_code == 200
        assert "asr_wer" in bm_resp.json()
        assert "action_decision_f1" in bm_resp.json()

        # 3. Register User A
        reg_user_a = {
            "name": "Rohith Team Lead",
            "email": "rohith@example.com",
            "password": "SecurePassword123!"
        }
        res_a = await ac.post("/api/auth/register", json=reg_user_a)
        assert res_a.status_code in [200, 400] # 200 or already registered
        
        # Login User A
        login_res_a = await ac.post("/api/auth/login", json={
            "email": "rohith@example.com",
            "password": "SecurePassword123!"
        })
        assert login_res_a.status_code == 200
        token_a = login_res_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # 4. User A Info
        me_resp = await ac.get("/api/auth/me", headers=headers_a)
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == "rohith@example.com"

        # 5. Create Meeting for User A
        meeting_data = {
            "title": "Backend Architecture & Sprint Planning",
            "date": "2026-09-08",
            "meeting_type": "LIVE",
            "participants": ["Rohith", "Dharun", "Priya"]
        }
        m_resp = await ac.post("/api/meetings", json=meeting_data, headers=headers_a)
        assert m_resp.status_code == 200
        meeting_id = m_resp.json()["id"]

        # 6. Execute Full Pipeline for Meeting
        process_resp = await ac.post(f"/api/meetings/{meeting_id}/process", headers=headers_a)
        assert process_resp.status_code == 200
        m_detail = process_resp.json()
        assert m_detail["status"] == "COMPLETED"
        assert len(m_detail["transcript_segments"]) > 0
        assert len(m_detail["action_items"]) > 0
        assert len(m_detail["decisions"]) > 0
        assert len(m_detail["topics"]) > 0
        assert m_detail["mom_document"] is not None

        # 7. Edit MoM Document (Requirement 37: Editable MoM)
        updated_summary = "Updated Executive Summary: Architecture finalized and sprint items delegated."
        mom_put_resp = await ac.put(
            f"/api/meetings/{meeting_id}/mom",
            json={"summary": updated_summary},
            headers=headers_a
        )
        assert mom_put_resp.status_code == 200
        assert mom_put_resp.json()["summary"] == updated_summary

        # 8. Test Isolated Semantic Search
        search_resp = await ac.get("/api/meetings/search?q=PostgreSQL", headers=headers_a)
        assert search_resp.status_code == 200
        assert search_resp.json()["total_results"] > 0

        # 9. Register User B and verify USER ISOLATION (Security Requirement)
        reg_user_b = {
            "name": "Unauthorized User B",
            "email": "userb@example.com",
            "password": "Password123!"
        }
        await ac.post("/api/auth/register", json=reg_user_b)
        login_res_b = await ac.post("/api/auth/login", json={
            "email": "userb@example.com",
            "password": "Password123!"
        })
        token_b = login_res_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # User B attempts to access User A's meeting -> MUST BE 403 FORBIDDEN
        sec_resp = await ac.get(f"/api/meetings/{meeting_id}", headers=headers_b)
        assert sec_resp.status_code == 403

        # User B searches -> must NOT see User A's meeting
        sec_search = await ac.get("/api/meetings/search?q=PostgreSQL", headers=headers_b)
        assert sec_search.status_code == 200
        assert sec_search.json()["total_results"] == 0

        # 10. Export to DOCX & PDF
        docx_resp = await ac.post(f"/api/meetings/{meeting_id}/export/docx", headers=headers_a)
        assert docx_resp.status_code == 200
        assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in docx_resp.headers["content-type"]

        pdf_resp = await ac.post(f"/api/meetings/{meeting_id}/export/pdf", headers=headers_a)
        assert pdf_resp.status_code == 200
        assert "application/pdf" in pdf_resp.headers["content-type"]

        print("\nAll Backend API & User Isolation Tests PASSED successfully!")
