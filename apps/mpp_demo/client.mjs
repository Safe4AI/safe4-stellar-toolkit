import { Keypair } from "@stellar/stellar-sdk";
import { Mppx } from "mppx/client";
import { stellar } from "@stellar/mpp/charge/client";
import { readFileSync, existsSync } from "node:fs";

function loadEnvFile(path) {
  if (!existsSync(path)) {
    return {};
  }
  return Object.fromEntries(
    readFileSync(path, "utf-8")
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line && !line.startsWith("#") && line.includes("="))
      .map((line) => {
        const separator = line.indexOf("=");
        return [line.slice(0, separator), line.slice(separator + 1)];
      }),
  );
}

const fileEnv = loadEnvFile(".env.mpp");
const STELLAR_SECRET = (process.env.STELLAR_SECRET || fileEnv.STELLAR_SECRET || "").trim();
const SERVICE_URL = (process.env.MPP_SERVICE_URL || fileEnv.MPP_SERVICE_URL || "http://localhost:3001/mpp/service").trim();
const MODE = (process.env.MPP_MODE || fileEnv.MPP_MODE || "pull").trim();

if (!STELLAR_SECRET) {
  console.error("Add STELLAR_SECRET=S... to .env.mpp or the environment.");
  process.exit(1);
}

const keypair = Keypair.fromSecret(STELLAR_SECRET);
console.log(`Using Stellar account: ${keypair.publicKey()}`);
console.log(`Calling MPP service: ${SERVICE_URL}`);

Mppx.create({
  methods: [
    stellar.charge({
      keypair,
      mode: MODE,
      onProgress(event) {
        console.log(`[${event.type}]`, event);
      },
    }),
  ],
});

const response = await fetch(SERVICE_URL);
const text = await response.text();

console.log(`Response (${response.status}):`);
console.log(text);
