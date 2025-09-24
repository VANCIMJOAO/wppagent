'use client';

import React from 'react';
import { useRouter } from 'next/navigation';

interface SafeLinkProps {
  href: string;
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

export function SafeLink({ href, children, className, onClick }: SafeLinkProps) {
  const router = useRouter();

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    if (onClick) {
      onClick();
    }
    router.push(href);
  };

  return (
    <a
      href={href}
      onClick={handleClick}
      className={className}
      style={{ cursor: 'pointer' }}
    >
      {children}
    </a>
  );
}
