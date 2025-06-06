import type { ReactNode } from 'react';
import { Header } from './Header';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen w-full bg-gray-50">
      <Header />
      <main className="w-[100%] px-4 py-8">
        {children}
      </main>
    </div>
  );
}
