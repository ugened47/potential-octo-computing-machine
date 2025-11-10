"use client";

import { useState, FormEvent, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { updateUser, getCurrentUser } from "@/lib/auth-api";
import { useAuth } from "@/store/auth-store";
import { Loader2, CheckCircle2 } from "lucide-react";

function ProfileContent() {
  const { user, setUser, isLoading: authLoading } = useAuth();
  const [fullName, setFullName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      setFullName(user.full_name || "");
    } else if (!authLoading) {
      // Fetch user if not in store
      getCurrentUser()
        .then((fetchedUser) => {
          setUser(fetchedUser);
          setFullName(fetchedUser.full_name || "");
        })
        .catch((err) => {
          console.error("Failed to fetch user:", err);
        });
    }
  }, [user, authLoading, setUser]);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setIsSuccess(false);

    if (!fullName.trim()) {
      setError("Full name is required");
      return;
    }

    setIsLoading(true);
    try {
      const updatedUser = await updateUser(fullName.trim());
      setUser(updatedUser);
      setIsSuccess(true);
      setTimeout(() => setIsSuccess(false), 3000);
    } catch (err: any) {
      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError("Failed to update profile. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">Loading...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-2xl py-8">
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Profile</h1>
          <p className="text-muted-foreground">
            Manage your account information
          </p>
        </div>

        <div className="rounded-lg border bg-card p-6 shadow-sm">
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-muted-foreground">
                Email
              </label>
              <p className="mt-1 text-sm">{user?.email || "Loading..."}</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
                  {error}
                </div>
              )}

              {isSuccess && (
                <div className="flex items-center gap-2 rounded-md bg-green-50 p-3 text-green-800 dark:bg-green-900/20 dark:text-green-400">
                  <CheckCircle2 className="h-4 w-4" />
                  <span className="text-sm">Profile updated successfully!</span>
                </div>
              )}

              <div className="space-y-2">
                <label htmlFor="fullName" className="text-sm font-medium">
                  Full Name
                </label>
                <Input
                  id="fullName"
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="John Doe"
                  disabled={isLoading}
                />
              </div>

              <Button type="submit" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Updating...
                  </>
                ) : (
                  "Update Profile"
                )}
              </Button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ProfilePage() {
  return (
    <ProtectedRoute>
      <ProfileContent />
    </ProtectedRoute>
  );
}
