import test from "node:test";
import assert from "node:assert/strict";
import {
  requestCoordinator,
  mergeAllocation,
  allocationHint,
} from "../static/dashboard_state.js";
const deferred = () => {
  let resolve;
  const promise = new Promise((r) => {
    resolve = r;
  });
  return { promise, resolve };
};

test("late old commentary cannot overwrite a new analysis; duplicate and stale completion states are ignored", async () => {
  const gate = requestCoordinator(),
    old = deferred(),
    next = deferred();
  let commentary = "",
    settled = 0;
  gate.setAnalysis("old");
  const first = gate.run("commentary", () => old.promise, {
    success: (x) => {
      commentary = x;
    },
    error: () => {},
    settled: () => settled++,
  });
  assert.equal(
    await gate.run("commentary", () => Promise.resolve("duplicate"), {}),
    false,
  );
  gate.invalidate(); // edit inputs, then finish a new calculation
  await gate.run("calculation", () => Promise.resolve({ id: "new" }), {
    success: (r) => gate.setAnalysis(r.id),
    error: () => {},
  });
  const second = gate.run("commentary", () => next.promise, {
    success: (x) => {
      commentary = x;
    },
    error: () => {},
    settled: () => settled++,
  });
  old.resolve("obsolete commentary");
  await first;
  assert.equal(commentary, "");
  assert.equal(gate.busy("commentary"), true);
  assert.equal(settled, 0);
  next.resolve("new commentary");
  await second;
  assert.equal(commentary, "new commentary");
  assert.equal(settled, 1);
  assert.equal(gate.busy("commentary"), false);
});
test("late calculation and CSV imports are discarded after edits", async () => {
  for (const kind of ["calculation", "import"]) {
    const gate = requestCoordinator(),
      d = deferred();
    let rendered = false;
    const task = gate.run(kind, () => d.promise, {
      success: () => {
        rendered = true;
      },
      error: () => {},
    });
    gate.invalidate();
    d.resolve({});
    await task;
    assert.equal(rendered, false);
    assert.equal(gate.busy(kind), false);
  }
});
test("errors restore request state", async () => {
  const gate = requestCoordinator();
  let failed = false,
    settled = false;
  await gate.run("calculation", () => Promise.reject(new Error("failure")), {
    success: () => {},
    error: () => (failed = true),
    settled: () => (settled = true),
  });
  assert.ok(failed && settled);
  assert.equal(gate.busy("calculation"), false);
});
test("CSV aliases merge into a single stock and preserve other weights", () => {
  const r = mergeAllocation(
    [
      { symbol: " tcs ", current: 40, alternative: 60 },
      { symbol: "INFY.NS", current: 60, alternative: 40 },
    ],
    [{ symbol: "TCS.NS", weight: 100 }],
    "current",
  );
  assert.equal(r.length, 2);
  assert.deepEqual(r[0], { symbol: "TCS.NS", current: 100, alternative: 60 });
  assert.equal(r[1].alternative, 40);
  assert.equal(r[1].current, 0);
});
test("incomplete weights and aliases are identified; disabled alternative is ignored", () => {
  assert.equal(
    allocationHint([{ symbol: "TCS", current: 100, alternative: "" }], false)
      .problems.length,
    0,
  );
  assert.ok(
    allocationHint([{ symbol: "TCS", current: 100, alternative: "" }], true)
      .problems.length,
  );
  assert.ok(
    allocationHint(
      [
        { symbol: "TCS", current: 50 },
        { symbol: "TCS.NS", current: 50 },
      ],
      false,
    ).problems.length,
  );
});
