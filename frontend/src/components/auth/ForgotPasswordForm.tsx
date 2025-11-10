"use client";

import { useState, FormEvent } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { forgotPassword } from "@/lib/auth-api";
import { validateEmail } from "@/lib/validation";
import { Loader2, CheckCircle2 } from "lucide-react";

export function ForgotPasswordForm() {
  const [email, setEmail] = useState("");
  const [emailError, setEmailError] = useState("");
  const [generalError, setGeneralError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const handleEmailBlur = () => {
    if (!email) {
      setEmailError("Email is required");
    } else if (!validateEmail(email)) {
      setEmailError("Please enter a valid email address");
    } else {
      setEmailError("");
    }
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setGeneralError("");

    // Validate
    if (!email) {
      setEmailError("Email is required");
      return;
    }
    if (!validateEmail(email)) {
      setEmailError("Please enter a valid email address");
      return;
    }

    setIsLoading(true);
    try {
      await forgotPassword(email);
      setIsSuccess(true);
    } catch (error: any) {
      if (error.response?.data?.detail) {
        setGeneralError(error.response.data.detail);
      } else {
        setGeneralError("Failed to send reset email. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (isSuccess) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-2 rounded-md bg-green-50 p-4 text-green-800 dark:bg-green-900/20 dark:text-green-400">
          <CheckCircle2 className="h-5 w-5" />
          <div>
            <p className="font-medium">Email sent!</p>
            <p className="text-sm">
              If an account exists with this email, you'll receive password
              reset instructions.
            </p>
          </div>
        </div>
        <Link href="/login">
          <Button variant="outline" className="w-full">
            Back to login
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {generalError && (
        <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
          {generalError}
        </div>
      )}

      <div className="space-y-2">
        <label htmlFor="email" className="text-sm font-medium">
          Email
        </label>
        <Input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          onBlur={handleEmailBlur}
          placeholder="you@example.com"
          disabled={isLoading}
          className={emailError ? "border-destructive" : ""}
        />
        {emailError && <p className="text-sm text-destructive">{emailError}</p>}
        <p className="text-xs text-muted-foreground">
          Enter your email address and we'll send you a link to reset your
          password.
        </p>
      </div>

      <Button type="submit" className="w-full" disabled={isLoading}>
        {isLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Sending...
          </>
        ) : (
          "Send reset link"
        )}
      </Button>

      <div className="text-center text-sm">
        <Link href="/login" className="text-primary hover:underline">
          Back to login
        </Link>
      </div>
    </form>
  );
}
