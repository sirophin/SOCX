import { useCallback, useEffect, useRef, useState } from 'react'
import { getErrorMessage } from '../api/client'

/**
 * Polls `fetchFn` every `intervalMs`.
 *
 * Deliberately distinguishes two kinds of loading:
 *   - `loading`: true only until the FIRST successful (or failed) fetch —
 *     this is what should show a skeleton.
 *   - `refreshing`: true while a background poll is in flight after that —
 *     existing `data` stays on screen the whole time, nothing blanks out.
 *
 * A background poll that fails does NOT clear `data` — the widget keeps
 * showing the last good snapshot with `error` set alongside it, rather
 * than flashing empty/broken every time one poll cycle hiccups.
 *
 * Polling pauses while the tab is hidden (visibilitychange) and does an
 * immediate refresh when it becomes visible again, rather than burning
 * requests against a tab nobody's looking at.
 */
export function useAutoRefresh(fetchFn, { intervalMs = 10000, enabled = true } = {}) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')
  const [lastUpdated, setLastUpdated] = useState(null)

  const fetchFnRef = useRef(fetchFn)
  fetchFnRef.current = fetchFn

  const hasLoadedOnce = useRef(false)

  const load = useCallback(async () => {
    if (hasLoadedOnce.current) {
      setRefreshing(true)
    }
    try {
      const result = await fetchFnRef.current()
      setData(result)
      setError('')
      setLastUpdated(new Date())
    } catch (err) {
      setError(getErrorMessage(err, 'Could not load this widget.'))
    } finally {
      hasLoadedOnce.current = true
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    if (!enabled) return undefined

    load()

    let intervalId = setInterval(load, intervalMs)

    function handleVisibilityChange() {
      if (document.hidden) {
        clearInterval(intervalId)
      } else {
        load()
        intervalId = setInterval(load, intervalMs)
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => {
      clearInterval(intervalId)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [enabled, intervalMs, load])

  return { data, loading, refreshing, error, lastUpdated, reload: load }
}
