import type { Metadata } from "next";
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

// Static export compatible - no server-side headers
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // For static export, nonce is not used (CSP headers set at CloudFront level)
  const styleNonce = null;

  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className="font-sans"
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
