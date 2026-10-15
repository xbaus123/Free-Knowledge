import { test } from "node:test";
import assert from "node:assert/strict";
import { sum } from "./solution.js";

test("sums a few numbers", () => {
  assert.equal(sum([1, 2, 3]), 6);
});

test("an empty array sums to 0", () => {
  assert.equal(sum([]), 0);
});

test("handles negative numbers", () => {
  assert.equal(sum([5, -2, -3]), 0);
});
