import { expect, test } from "@playwright/test";

test("login page renders the form", async ({ page }) => {
  await page.goto("/login");

  await expect(page.getByRole("heading", { name: "SIVIGILA" })).toBeVisible();
  await expect(page.getByLabel("Usuario")).toBeVisible();
  await expect(page.getByLabel("Contraseña")).toBeVisible();
  await expect(page.getByRole("button", { name: "Ingresar" })).toBeVisible();
});

test("login submits valid credentials and navigates away from /login", async ({
  page,
}) => {
  await page.goto("/login");

  await page.getByLabel("Usuario").fill("docente");
  await page.getByLabel("Contraseña").fill("docente123");
  await page.getByRole("button", { name: "Ingresar" }).click();

  await expect(page).not.toHaveURL(/\/login$/);

  await expect(page.getByText(/incorrectos|No se pudo iniciar sesión/i)).toHaveCount(
    0,
  );
});
