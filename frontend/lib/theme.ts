import { useSyncExternalStore } from "react";

export type Theme = "light" | "dark";

const STORAGE_KEY = "theme";
const CHANGE_EVENT = "themechange";

export function getTheme(): Theme {
  return document.documentElement.classList.contains("dark") ? "dark" : "light";
}

export function setTheme(theme: Theme) {
  document.documentElement.classList.toggle("dark", theme === "dark");
  try {
    localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    // Private browsing / blocked storage — theme still applies for this load, just won't persist.
  }
  window.dispatchEvent(new Event(CHANGE_EVENT));
}

function subscribe(callback: () => void): () => void {
  window.addEventListener(CHANGE_EVENT, callback);
  return () => window.removeEventListener(CHANGE_EVENT, callback);
}

// The theme lives on the <html> class, set by the inline script in
// layout.tsx before hydration — not in any React state. useSyncExternalStore
// is the built-in way to read external mutable state like this without a
// useEffect+useState dance, and it already handles the SSR/hydration case:
// the server snapshot below matches layout.tsx's "dark" default, and React
// reconciles to the DOM's real value right after hydration.
export function useTheme(): Theme {
  return useSyncExternalStore(subscribe, getTheme, () => "dark");
}
