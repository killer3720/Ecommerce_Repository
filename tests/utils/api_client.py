class APIClient:

    def __init__(self, client):
        self.client = client

    def get(self, endpoint, headers=None):
        return self.client.get(endpoint, headers=headers)

    def post(self, endpoint, payload, headers=None):
        return self.client.post(
            endpoint,
            json=payload,
            headers=headers
        )

    def put(self, endpoint, payload, headers=None):
        return self.client.put(
            endpoint,
            json=payload,
            headers=headers
        )

    def patch(self, endpoint, payload, headers=None):
        return self.client.patch(
            endpoint,
            json=payload,
            headers=headers
        )

    def delete(self, endpoint, headers=None):
        return self.client.delete(endpoint, headers=headers)