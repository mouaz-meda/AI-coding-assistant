import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AI Coding Assistant",
  description: "Ingest, review, and fix code with an LLM-backed coding assistant",
};

// Runs before hydration (plain <script>, not a React effect) so the right
// theme class is already on <html> for the very first paint — otherwise the
// page would flash dark-then-light (or vice versa) on every load.
const THEME_INIT_SCRIPT = `
(function () {
  try {
    var theme = localStorage.getItem("theme");
    document.documentElement.classList.toggle("dark", theme !== "light");
  } catch (e) {}
})();
`;

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
