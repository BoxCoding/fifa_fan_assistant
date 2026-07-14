import { useEffect, useState } from "react";

/**
 * Poll an async fetcher on an interval and return its latest result.
 *
 * Handles the full lifecycle once, so components don't each re-implement it:
 * immediate first load, interval refresh, in-flight guard against setting state
 * after unmount, and cleanup. Fetch errors are swallowed (the panel simply keeps
 * its last value and retries on the next tick).
 *
 * @param {() => Promise<any>} fetcher - returns the data to store
 * @param {number} intervalMs - refresh cadence
 * @param {Array} deps - re-subscribe when these change (e.g. stadium id)
 */
export function usePolling(fetcher, intervalMs, deps = []) {
  const [data, setData] = useState(null);

  useEffect(() => {
    let alive = true;
    const load = () =>
      fetcher()
        .then((d) => alive && setData(d))
        .catch(() => {});
    load();
    const id = setInterval(load, intervalMs);
    return () => {
      alive = false;
      clearInterval(id);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return data;
}
