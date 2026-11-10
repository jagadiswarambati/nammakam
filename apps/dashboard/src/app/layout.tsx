/**
 * Root Layout Component.
 *
 * Intended Responsibility:
 * Defines the root HTML shell, global typography, and top-level context providers.
 *
 * TODO:
 * 1. Implement RootLayout component with HTML and body tags.
 * 2. Mount TanStack Query and theme providers.
 */
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

