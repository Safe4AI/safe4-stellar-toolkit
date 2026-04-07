const { test, expect } = require("@playwright/test");
const fs = require("node:fs");
const path = require("node:path");

const outputDir = path.join(process.cwd(), "docs", "assets");

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

async function renderJson(page, title, payload) {
  await page.setContent(`
    <html>
      <head>
        <style>
          body { font-family: Georgia, serif; margin: 0; background: #f4f7fb; color: #12213b; }
          main { max-width: 1000px; margin: 0 auto; padding: 32px; }
          h1 { margin: 0 0 16px; font-size: 28px; }
          p { margin: 0 0 18px; color: #5a6782; }
          pre { background: #101828; color: #e8eef8; padding: 20px; border-radius: 16px; overflow: auto; font-size: 14px; line-height: 1.5; }
        </style>
      </head>
      <body>
        <main>
          <h1>${escapeHtml(title)}</h1>
          <p>Live public proof artifact captured from the deployed Safe4 Stellar Toolkit surface.</p>
          <pre>${escapeHtml(JSON.stringify(payload, null, 2))}</pre>
        </main>
      </body>
    </html>
  `);
}

test("capture live public proof surfaces", async ({ page, request }) => {
  fs.mkdirSync(outputDir, { recursive: true });

  await page.goto("https://toolkit-api-production-a04c.up.railway.app/demo", { waitUntil: "networkidle" });
  await expect(page.getByRole("heading", { name: "Safe4 Stellar Toolkit" })).toBeVisible();
  await page.screenshot({ path: path.join(outputDir, "public-demo-home.png"), fullPage: true });

  const x402Status = await request.get("https://toolkit-api-production-a04c.up.railway.app/protocols/x402/facilitator");
  await renderJson(page, "Public x402 Facilitator Status", await x402Status.json());
  await page.screenshot({ path: path.join(outputDir, "public-x402-status.png"), fullPage: true });

  const x402Supported = await request.get("https://x402-facilitator-demo-production.up.railway.app/supported");
  await renderJson(page, "Public x402 Facilitator Sidecar", await x402Supported.json());
  await page.screenshot({ path: path.join(outputDir, "public-x402-sidecar.png"), fullPage: true });

  const mppStatus = await request.get("https://toolkit-api-production-a04c.up.railway.app/protocols/mpp/charge");
  await renderJson(page, "Public MPP Charge Status", await mppStatus.json());
  await page.screenshot({ path: path.join(outputDir, "public-mpp-status.png"), fullPage: true });

  const mppChallenge = await request.get("https://mpp-charge-demo-production.up.railway.app/mpp/service");
  const challengeBody = await mppChallenge.text();
  await renderJson(page, "Public MPP Charge Sidecar 402", {
    status: mppChallenge.status(),
    headers: {
      "www-authenticate": mppChallenge.headers()["www-authenticate"],
      "content-type": mppChallenge.headers()["content-type"],
    },
    body: (() => {
      try {
        return JSON.parse(challengeBody);
      } catch {
        return challengeBody;
      }
    })(),
  });
  await page.screenshot({ path: path.join(outputDir, "public-mpp-sidecar-402.png"), fullPage: true });
});
