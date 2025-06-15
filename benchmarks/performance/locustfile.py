from locust import HttpUser, between, task


class LTMUser(HttpUser):
    wait_time = between(0.01, 0.05)

    @task
    def consolidate_and_retrieve(self):
        record = {
            "task_context": {"query": "perf"},
            "execution_trace": {},
            "outcome": {"success": True},
        }
        self.client.post("/consolidate", json={"record": record})
        self.client.get("/retrieve?limit=1", json={"query": {"query": "perf"}})
