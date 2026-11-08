import js from "@eslint/js";
import globals from "globals";

export default [
  js.configs.recommended,
  {
    files: ["dashboard/static/**/*.js"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      globals: globals.browser,
    },
    rules: {
      curly: ["error", "all"],
      "no-ternary": "error",
      "no-nested-ternary": "error",
      "no-unused-expressions": ["error", { allowShortCircuit: false, allowTernary: false }],
      "no-else-return": "error",
      "padding-line-between-statements": ["error", { blankLine: "always", prev: "*", next: "return" }],

      eqeqeq: ["error", "always"],
      "no-var": "error",
      "prefer-const": "error",
      "object-shorthand": "error",
      "prefer-template": "error",
      "no-param-reassign": "error",
      "no-unused-vars": ["error", { argsIgnorePattern: "^_", caughtErrors: "none" }],

      complexity: ["warn", 8],
      "max-depth": ["warn", 3],
      "max-lines-per-function": ["warn", { max: 50, skipBlankLines: true, skipComments: true }],
    },
  },
];
