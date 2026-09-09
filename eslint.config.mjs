import next from "eslint-config-next";

/**
 * Flat config. `eslint-config-next` ships the core-web-vitals and TypeScript
 * rule sets together, so no compatibility shim is needed.
 */
const config = [
  { ignores: [".next/**", "node_modules/**", "out/**", "next-env.d.ts"] },
  ...next,
];

export default config;
