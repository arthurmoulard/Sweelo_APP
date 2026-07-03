from datetime import date, timedelta


def _create_activity(client, headers, **overrides):
    payload = {
        "type": "run", "distance_km": 5, "duration_min": 30,
        "date": date.today().isoformat(),
    }
    payload.update(overrides)
    return client.post("/api/v1/activities/", json=payload, headers=headers)


class TestActivityCreation:

    def test_create_activity_requires_auth(self, client):
        resp = _create_activity(client, headers={})

        assert resp.status_code == 401

    def test_create_activity_success(self, client, auth_headers):
        resp = _create_activity(client, auth_headers, distance_km=5.2, notes="Séance easy")

        assert resp.status_code == 201
        data = resp.get_json()
        assert data["type"] == "run"
        assert data["distance_km"] == 5.2

    def test_create_activity_requires_distance_for_distance_sport(self, client, auth_headers):
        resp = client.post("/api/v1/activities/", json={
            "type": "run", "duration_min": 30, "date": date.today().isoformat(),
        }, headers=auth_headers)

        assert resp.status_code == 400

    def test_create_activity_allows_no_distance_sport(self, client, auth_headers):
        resp = client.post("/api/v1/activities/", json={
            "type": "muscu", "duration_min": 45, "date": date.today().isoformat(),
        }, headers=auth_headers)

        assert resp.status_code == 201
        assert resp.get_json()["distance_km"] is None

    def test_create_activity_rejects_future_date(self, client, auth_headers):
        future = (date.today() + timedelta(days=1)).isoformat()

        resp = _create_activity(client, auth_headers, date=future)

        assert resp.status_code == 400


class TestActivityDetail:

    def test_get_activity_returns_owner_activity(self, client, auth_headers):
        activity_id = _create_activity(client, auth_headers).get_json()["id"]

        resp = client.get(f"/api/v1/activities/{activity_id}", headers=auth_headers)

        assert resp.status_code == 200

    def test_get_activity_unknown_returns_404(self, client, auth_headers):
        resp = client.get("/api/v1/activities/does-not-exist", headers=auth_headers)

        assert resp.status_code == 404

    def test_get_activity_forbidden_for_other_user(self, client, auth_headers, second_user):
        activity_id = _create_activity(client, auth_headers).get_json()["id"]
        other_headers, _ = second_user

        resp = client.get(f"/api/v1/activities/{activity_id}", headers=other_headers)

        assert resp.status_code == 403

    def test_update_activity_changes_fields(self, client, auth_headers):
        activity_id = _create_activity(client, auth_headers).get_json()["id"]

        resp = client.put(f"/api/v1/activities/{activity_id}", json={
            "duration_min": 50,
        }, headers=auth_headers)

        assert resp.status_code == 200
        assert resp.get_json()["duration_min"] == 50

    def test_update_activity_forbidden_for_other_user(self, client, auth_headers, second_user):
        activity_id = _create_activity(client, auth_headers).get_json()["id"]
        other_headers, _ = second_user

        resp = client.put(f"/api/v1/activities/{activity_id}", json={
            "duration_min": 50,
        }, headers=other_headers)

        assert resp.status_code == 403

    def test_delete_activity_removes_it(self, client, auth_headers):
        activity_id = _create_activity(client, auth_headers).get_json()["id"]

        resp = client.delete(f"/api/v1/activities/{activity_id}", headers=auth_headers)
        assert resp.status_code == 204

        resp = client.get(f"/api/v1/activities/{activity_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_list_activities_paginated(self, client, auth_headers):
        _create_activity(client, auth_headers)

        resp = client.get("/api/v1/activities/", headers=auth_headers)

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["page"] == 1
        assert len(data["items"]) == 1
