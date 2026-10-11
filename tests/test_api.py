from fastapi.testclient import TestClient
from app.server import create_app
from sample_case.fixture import request


def test_human_gate_requires_local_session_token(tmp_path):
    app=create_app(tmp_path/"cases")
    client=TestClient(app)
    case=app.state.service.register_case(request())
    plan=app.state.service.compile_evaluation_plan(case["id"])
    approval={"reviewer":"TEST SIMULATION","digest":plan["digest"],"confirmed":True}
    assert client.post(f"/api/cases/{case['id']}/plan/approve",json=approval).status_code==403
    token=client.get("/api/session").json()["token"]
    assert client.post(f"/api/cases/{case['id']}/plan/approve",json=approval,headers={"X-Workbench-Token":token,"Origin":"https://untrusted.example"}).status_code==403
    assert client.post(f"/api/cases/{case['id']}/plan/approve",json=approval,headers={"X-Workbench-Token":token}).status_code==200


def test_download_requires_approved_export(tmp_path):
    app=create_app(tmp_path/"cases")
    client=TestClient(app)
    case=app.state.service.register_case(request())
    assert client.get(f"/api/cases/{case['id']}/download").status_code==403
    assert client.get("/",headers={"Host":"evil.example"}).status_code==400
