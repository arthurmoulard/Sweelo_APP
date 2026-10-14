from datetime import date


def _create_activity(client, headers, activity_type="run", **overrides):
    payload = {
        "type": activity_type, "distance_km": 5, "duration_min": 30,
        "date": date.today().isoformat(),
    }
    payload.update(overrides)
    resp = client.post("/api/v1/activities/", json=payload, headers=headers)
    return resp.get_json()


class TestFeed:

    def test_feed_requires_auth(self, client):
        resp = client.get("/api/v1/feed/")

        assert resp.status_code == 401

    def test_feed_contains_own_post(self, client, auth_headers):
        _create_activity(client, auth_headers)

        resp = client.get("/api/v1/feed/", headers=auth_headers)

        assert resp.status_code == 200
        assert len(resp.get_json()["items"]) == 1

    def test_feed_excludes_non_friend_posts(self, client, auth_headers, second_user):
        other_headers, _ = second_user
        _create_activity(client, other_headers)

        resp = client.get("/api/v1/feed/", headers=auth_headers)

        assert resp.get_json()["items"] == []


class TestLikes:

    def test_like_then_unlike_toggles(self, client, auth_headers):
        post_id = _create_activity(client, auth_headers)["post_id"]

        resp = client.post(f"/api/v1/feed/{post_id}/like", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["liked"] is True

        resp = client.post(f"/api/v1/feed/{post_id}/like", headers=auth_headers)
        assert resp.get_json()["liked"] is False

    def test_like_unknown_post_returns_404(self, client, auth_headers):
        resp = client.post("/api/v1/feed/does-not-exist/like", headers=auth_headers)

        assert resp.status_code == 404


class TestComments:

    def test_cannot_comment_on_own_post(self, client, auth_headers):
        post_id = _create_activity(client, auth_headers)["post_id"]

        resp = client.post(f"/api/v1/feed/{post_id}/comments", json={
            "content": "Bravo !",
        }, headers=auth_headers)

        assert resp.status_code == 400

    def test_comment_on_others_post(self, client, auth_headers, second_user):
        other_headers, _ = second_user
        post_id = _create_activity(client, auth_headers)["post_id"]

        resp = client.post(f"/api/v1/feed/{post_id}/comments", json={
            "content": "Bravo !",
        }, headers=other_headers)

        assert resp.status_code == 201

    def test_list_comments_of_a_post(self, client, auth_headers, second_user):
        other_headers, _ = second_user
        post_id = _create_activity(client, auth_headers)["post_id"]
        client.post(f"/api/v1/feed/{post_id}/comments", json={
            "content": "Bravo !",
        }, headers=other_headers)

        resp = client.get(f"/api/v1/feed/{post_id}/comments", headers=auth_headers)

        assert resp.status_code == 200
        assert len(resp.get_json()["items"]) == 1

    def test_delete_own_comment(self, client, auth_headers, second_user):
        other_headers, _ = second_user
        post_id = _create_activity(client, auth_headers)["post_id"]
        comment_id = client.post(f"/api/v1/feed/{post_id}/comments", json={
            "content": "Bravo !",
        }, headers=other_headers).get_json()["id"]

        resp = client.delete(f"/api/v1/feed/comments/{comment_id}", headers=other_headers)

        assert resp.status_code == 204

    def test_delete_others_comment_forbidden(self, client, auth_headers, second_user):
        other_headers, _ = second_user
        post_id = _create_activity(client, auth_headers)["post_id"]
        comment_id = client.post(f"/api/v1/feed/{post_id}/comments", json={
            "content": "Bravo !",
        }, headers=other_headers).get_json()["id"]

        resp = client.delete(f"/api/v1/feed/comments/{comment_id}", headers=auth_headers)

        assert resp.status_code == 403


class TestReports:

    def test_report_post_returns_confirmation(self, client, auth_headers, second_user):
        other_headers, _ = second_user
        post_id = _create_activity(client, auth_headers)["post_id"]

        resp = client.post(f"/api/v1/feed/{post_id}/report", json={
            "reason": "spam",
        }, headers=other_headers)

        assert resp.status_code == 200

    def test_report_unknown_post_returns_404(self, client, auth_headers):
        resp = client.post("/api/v1/feed/does-not-exist/report", json={
            "reason": "spam",
        }, headers=auth_headers)

        assert resp.status_code == 404
