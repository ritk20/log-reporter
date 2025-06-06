import type { ReactNode } from 'react';
import { Header } from './Header';
import UploadWidget from './UploadWidget';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen w-full bg-gray-50">
      <Header />
      <UploadWidget />
      <main className="w-[100%] px-4 py-8">
        {children}
      </main>
    </div>
  );
}
