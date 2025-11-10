"use client";

import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/store/auth-store";
import { LogOut, User, Video, Home } from "lucide-react";

export function Header() {
  const router = useRouter();
  const pathname = usePathname();
  const { user, logout, isAuthenticated } = useAuth();

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  // Don't show header on auth pages
  if (
    !isAuthenticated ||
    pathname?.startsWith("/login") ||
    pathname?.startsWith("/register")
  ) {
    return null;
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        <div className="flex items-center gap-6">
          <Link
            href="/dashboard"
            className="flex items-center gap-2 font-bold text-xl"
          >
            <Video className="h-6 w-6" />
            <span>AI Video Editor</span>
          </Link>
          <nav className="hidden md:flex items-center gap-4">
            <Link
              href="/dashboard"
              className={`text-sm font-medium transition-colors hover:text-primary ${
                pathname === "/dashboard"
                  ? "text-primary"
                  : "text-muted-foreground"
              }`}
            >
              <Home className="h-4 w-4 inline mr-1" />
              Dashboard
            </Link>
            <Link
              href="/upload"
              className={`text-sm font-medium transition-colors hover:text-primary ${
                pathname === "/upload"
                  ? "text-primary"
                  : "text-muted-foreground"
              }`}
            >
              Upload
            </Link>
            <Link
              href="/help"
              className={`text-sm font-medium transition-colors hover:text-primary ${
                pathname?.startsWith("/help")
                  ? "text-primary"
                  : "text-muted-foreground"
              }`}
            >
              Help
            </Link>
          </nav>
        </div>
        <div className="flex items-center gap-4">
          {user && (
            <div className="hidden sm:flex items-center gap-2 text-sm text-muted-foreground">
              <User className="h-4 w-4" />
              <span>{user.full_name || user.email}</span>
            </div>
          )}
          <Button variant="ghost" size="sm" onClick={handleLogout}>
            <LogOut className="h-4 w-4 mr-2" />
            <span className="hidden sm:inline">Logout</span>
          </Button>
        </div>
      </div>
    </header>
  );
}
