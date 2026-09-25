import { expect, test } from "@playwright/test";

test("backend /health returns 200 {status:ok}", async ({ request }) => {
  const response = await request.get("http://localhost:8000/health");
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body).toEqual({ status: "ok" });
});
