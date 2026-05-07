import type { Metadata } from "next";
import { Syne, Manrope, Playfair_Display } from "next/font/google";
import "./globals.css";
import { ToastProvider } from "./components/ui/ToastProvider";
import { AuthProvider } from "./context/AuthContext";

const syne = Syne({ subsets: ["latin"], variable: "--font-syne" });
const manrope = Manrope({ subsets: ["latin"], variable: "--font-manrope" });
const playfair = Playfair_Display({ subsets: ["latin"], style: "italic", variable: "--font-playfair" });

export const metadata: Metadata = {
  title: "FireHox Connect — AI Meeting Assistant",
  description:
    "Real-time AI meeting assistant that detects actionable tasks from live conversations.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${syne.variable} ${manrope.variable} ${playfair.variable}`}>
      <body>
        <AuthProvider>
          <ToastProvider>{children}</ToastProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
