// Shared request ownership and allocation identity rules; no DOM dependencies.
export const canonicalSymbol = (value) => {
  const name = String(value).trim().toUpperCase();
  return name && !name.endsWith(".NS") ? `${name}.NS` : name;
};

export function mergeAllocation(existing, imported, target) {
  const other = target === "current" ? "alternative" : "current";
  const old = new Map();
  for (const row of existing) {
    const name = canonicalSymbol(row.symbol);
    if (!name && !Number(row[other])) continue;
    if (old.has(name))
      throw new Error(
        `Duplicate stock ${name}; remove the duplicate before importing.`,
      );
    old.set(name, row);
  }
  const incoming = new Map(
    imported.map((row) => [canonicalSymbol(row.symbol), row.weight]),
  );
  const symbols = new Set([...old.keys(), ...incoming.keys()]);
  if (symbols.size > 10)
    throw new Error(
      "Combined allocations exceed ten stocks. Remove unused rows first.",
    );
  return [...symbols].map((symbol) => ({
    symbol,
    [target]: incoming.get(symbol) ?? 0,
    [other]: old.get(symbol)?.[other] ?? 0,
  }));
}

export function allocationHint(rows, alternative) {
  const symbols = rows.map((row) => canonicalSymbol(row.symbol));
  const problems = [];
  if (
    !rows.length ||
    symbols.some((s) => !/^[A-Z0-9][A-Z0-9&-]{0,24}\.NS$/.test(s))
  )
    problems.push("Complete each NSE stock symbol.");
  if (new Set(symbols).size !== symbols.length)
    problems.push("Remove duplicate stocks (aliases count as the same stock).");
  const totals = {};
  for (const key of alternative ? ["current", "alternative"] : ["current"]) {
    const valid = rows.every(
      (row) =>
        String(row[key]).trim() !== "" &&
        Number.isFinite(Number(row[key])) &&
        Number(row[key]) >= 0 &&
        Number(row[key]) <= 100.01,
    );
    totals[key] = rows.reduce((sum, row) => sum + (Number(row[key]) || 0), 0);
    if (
      !valid ||
      totals[key] <= 0 ||
      Math.abs(totals[key] - 100) > 0.0100000001
    )
      problems.push(
        `${key === "current" ? "Current" : "Alternative"} weights must total 100% (±0.01 rounding tolerance).`,
      );
  }
  return { totals, problems };
}

export function requestCoordinator() {
  let revision = 0,
    analysisId = null;
  const pending = new Map();
  const current = (kind, token) =>
    pending.get(kind) === token &&
    token.revision === revision &&
    (kind !== "commentary" || token.analysisId === analysisId);
  return {
    busy: (kind) => pending.has(kind),
    setAnalysis: (id) => {
      analysisId = id;
    },
    invalidate() {
      revision++;
      analysisId = null;
      for (const token of pending.values()) token.controller.abort();
      pending.clear();
    },
    async run(kind, task, callbacks) {
      if (pending.has(kind)) return false;
      const token = { revision, analysisId, controller: new AbortController() };
      pending.set(kind, token);
      callbacks.started?.();
      try {
        const value = await task(token.controller.signal);
        if (current(kind, token)) callbacks.success(value);
      } catch (error) {
        if (current(kind, token) && error.name !== "AbortError")
          callbacks.error(error);
      } finally {
        if (pending.get(kind) === token) {
          pending.delete(kind);
          callbacks.settled?.();
        }
      }
      return true;
    },
  };
}
