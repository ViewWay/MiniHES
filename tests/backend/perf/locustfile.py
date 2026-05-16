from locust import HttpUser, between, task


class MiniHESUser(HttpUser):
    wait_time = between(1, 3)
    host = "http://localhost:8000"

    def on_start(self):
        resp = self.client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "Test123456!",
        })
        data = resp.json()
        self.token = data.get("data", {}).get("access_token", "")
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def list_meters(self):
        self.client.get("/api/v1/meters?page=1&page_size=20", headers=self.headers)

    @task(2)
    def list_tasks(self):
        self.client.get("/api/v1/tasks?page=1&page_size=20", headers=self.headers)

    @task(1)
    def dashboard_overview(self):
        self.client.get("/api/v1/screens/overview", headers=self.headers)

    @task(1)
    def health_check(self):
        self.client.get("/api/v1/health")
