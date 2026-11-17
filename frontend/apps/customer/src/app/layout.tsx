import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import { ServiceWorkerRegistration } from "./service-worker-registration";
import "./globals.css";

export const metadata: Metadata = {
  title: "SwarmDining",
  description: "Order from your table. Let the swarm coordinate the floor.",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "SwarmDining",
  },
  icons: {
    icon: [{ url: "/icons/icon-192.png", type: "image/png" }],
    apple: [{ url: "/icons/icon-192.png", type: "image/png" }],
  },
};

export const viewport: Viewport = {
  themeColor: "#0f172a",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="flex min-h-full flex-col">
        <ServiceWorkerRegistration />
        {children}
      </body>
    </html>
  );
}
