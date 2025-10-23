import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ThemeProvider } from "next-themes";
import "../src/styles/globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "SwarmAI - Autonomous Incident Commander",
  description: "Revolutionary AI-Powered Multi-Agent Incident Response System",
  keywords: [
    "SwarmAI",
    "incident management",
    "AI",
    "automation",
    "DevOps",
    "SRE",
    "multi-agent",
  ],
  authors: [{ name: "SwarmAI Team" }],
};

export const viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem={false}
          disableTransitionOnChange
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
