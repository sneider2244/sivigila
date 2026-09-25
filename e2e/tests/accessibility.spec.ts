import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import fs from "node:fs";

interface AxeViolation {
  id: string;
  impact: string | null;
  description: string;
  help: string;
  helpUrl: string;
  nodes: { target: string[]; html: string }[];
}

const OUTPUT_FILE = "/tmp/opencode/axe-violations.json";

function writeViolations(pageName: string, violations: AxeViolation[]): void {
  const payload = { page: pageName, scannedAt: new Date().toISOString(), violations };
  try {
    const existing = fs.existsSync(OUTPUT_FILE)
      ? JSON.parse(fs.readFileSync(OUTPUT_FILE, "utf8"))
      : [];
    const list = Array.isArray(existing) ? existing : [];
    list.push(payload);
    fs.writeFileSync(OUTPUT_FILE, JSON.stringify(list, null, 2));
  } catch (err) {
    console.error("Failed to write axe results:", err);
  }
}

test("accessibility audit: /login", async ({ page }) => {
  await page.goto("/login");
  await expect(page.getByRole("heading", { name: "SIVIGILA" })).toBeVisible();

  const results = await new AxeBuilder({ page }).analyze();
  writeViolations("/login", results.violations as AxeViolation[]);

  console.log(
    `[axe /login] ${results.violations.length} violation(s), ` +
      `${results.passes.length} pass(es), ${results.incomplete.length} incomplete`,
  );
});

test("accessibility audit: /caracterizacion", async ({ page }) => {
  await page.goto("/caracterizacion");
  await expect(page.getByRole("heading", { name: "Caracterización UPGD" })).toBeVisible();

  const results = await new AxeBuilder({ page }).analyze();
  writeViolations("/caracterizacion", results.violations as AxeViolation[]);

  console.log(
    `[axe /caracterizacion] ${results.violations.length} violation(s), ` +
      `${results.passes.length} pass(es), ${results.incomplete.length} incomplete`,
  );
});
