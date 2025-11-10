"use client";

import { useEffect } from "react";
import { useAuth } from "@/store/auth-store";

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const { initialize } = useAuth();

  useEffect(() => {
    // Initialize auth state on app load
    initialize();
  }, [initialize]);

  return <>{children}</>;
}
