import nextVitals from "eslint-config-next/core-web-vitals";

const config = [
  ...nextVitals,
  {
    rules: {
      "react-hooks/set-state-in-effect": "off",
      "react-hooks/static-components": "off",
      "react-hooks/purity": "off",
      "react-hooks/preserve-manual-memoization": "off",
      "react-hooks/immutability": "off",
      "react-hooks/refs": "off",
      "@next/next/no-html-link-for-pages": "off",
      "import/no-anonymous-default-export": "off",
    },
  },
  {
    ignores: [".next/**", "node_modules/**"],
  },
];

export default config;
