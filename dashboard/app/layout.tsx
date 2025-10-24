import type { Metadata } from "next";
import { headers } from "next/headers";
// Font import temporarily disabled due to network restrictions
// import { Inter } from "next/font/google";
import { ThemeProvider } from "next-themes";
import "../src/styles/globals.css";
import { StyleNonceProvider } from "../src/lib/nonce-context";

// Using system font fallback
// const inter = Inter({ subsets: ["latin"] });

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

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const incomingHeaders = await headers();
  const styleNonce = incomingHeaders.get("x-style-nonce");

  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className="font-sans"
        data-style-nonce={styleNonce ?? undefined}
      >
        <StyleNonceProvider nonce={styleNonce}>
          <ThemeProvider
            attribute="class"
            defaultTheme="dark"
            enableSystem={false}
            disableTransitionOnChange
          >
            {children}
          </ThemeProvider>
        </StyleNonceProvider>
      </body>
    </html>
  );
}
