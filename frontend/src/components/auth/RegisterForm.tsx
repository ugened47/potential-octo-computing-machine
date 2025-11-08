"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { GoogleOAuthButton } from "./GoogleOAuthButton";
import { register } from "@/lib/auth-api";
import { useAuth } from "@/store/auth-store";
import { validateEmail, validatePassword } from "@/lib/validation";
import { Loader2 } from "lucide-react";

export function RegisterForm() {
  const router = useRouter();
  const { setUser } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [fullNameError, setFullNameError] = useState("");
  const [generalError, setGeneralError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleEmailBlur = () => {
    if (!email) {
      setEmailError("Email is required");
    } else if (!validateEmail(email)) {
      setEmailError("Please enter a valid email address");
    } else {
      setEmailError("");
    }
  };

  const handlePasswordBlur = () => {
    if (!password) {
      setPasswordError("Password is required");
    } else {
      const validation = validatePassword(password);
      if (!validation.valid) {
        setPasswordError(validation.errors[0]);
      } else {
        setPasswordError("");
      }
    }
  };

  const handleFullNameBlur = () => {
    if (!fullName.trim()) {
      setFullNameError("Full name is required");
    } else {
      setFullNameError("");
    }
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setGeneralError("");

    // Validate
    let isValid = true;
    if (!email) {
      setEmailError("Email is required");
      isValid = false;
    } else if (!validateEmail(email)) {
      setEmailError("Please enter a valid email address");
      isValid = false;
    }

    if (!password) {
      setPasswordError("Password is required");
      isValid = false;
    } else {
      const validation = validatePassword(password);
      if (!validation.valid) {
        setPasswordError(validation.errors[0]);
        isValid = false;
      }
    }

    if (!fullName.trim()) {
      setFullNameError("Full name is required");
      isValid = false;
    }

    if (!isValid) return;

    setIsLoading(true);
    try {
      const response = await register(email, password, fullName);
      setUser(response.user);
      router.push("/onboarding");
    } catch (error: any) {
      if (error.response?.data?.detail) {
        setGeneralError(error.response.data.detail);
      } else {
        setGeneralError("Registration failed. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {generalError && (
        <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
          {generalError}
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
          onBlur={handleFullNameBlur}
          placeholder="John Doe"
          disabled={isLoading}
          className={fullNameError ? "border-destructive" : ""}
        />
        {fullNameError && (
          <p className="text-sm text-destructive">{fullNameError}</p>
        )}
      </div>

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
      </div>

      <div className="space-y-2">
        <label htmlFor="password" className="text-sm font-medium">
          Password
        </label>
        <Input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onBlur={handlePasswordBlur}
          placeholder="Enter your password"
          disabled={isLoading}
          className={passwordError ? "border-destructive" : ""}
        />
        {passwordError && (
          <p className="text-sm text-destructive">{passwordError}</p>
        )}
        <p className="text-xs text-muted-foreground">
          Must be at least 8 characters with uppercase, lowercase, and a digit
        </p>
      </div>

      <Button type="submit" className="w-full" disabled={isLoading}>
        {isLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Creating account...
          </>
        ) : (
          "Create account"
        )}
      </Button>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-background px-2 text-muted-foreground">
            Or continue with
          </span>
        </div>
      </div>

      <GoogleOAuthButton className="w-full" />

      <div className="text-center text-sm">
        Already have an account?{" "}
        <Link href="/login" className="text-primary hover:underline">
          Log in
        </Link>
      </div>
    </form>
  );
}
