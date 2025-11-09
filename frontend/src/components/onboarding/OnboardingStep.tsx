import { ReactNode } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { X, ChevronLeft, ChevronRight } from "lucide-react";

interface OnboardingStepProps {
  title: string;
  description: string;
  children: ReactNode;
  step: number;
  totalSteps: number;
  onNext: () => void;
  onPrevious: () => void;
  onSkip: () => void;
  isFirst: boolean;
  isLast: boolean;
}

export function OnboardingStep({
  title,
  description,
  children,
  step,
  totalSteps,
  onNext,
  onPrevious,
  onSkip,
  isFirst,
  isLast,
}: OnboardingStepProps) {
  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>{title}</CardTitle>
            <CardDescription className="mt-2">{description}</CardDescription>
          </div>
          <Button variant="ghost" size="icon" onClick={onSkip}>
            <X className="h-4 w-4" />
          </Button>
        </div>
        <div className="mt-4">
          <div className="flex items-center gap-2">
            {Array.from({ length: totalSteps }).map((_, i) => (
              <div
                key={i}
                className={`h-2 flex-1 rounded-full transition-colors ${
                  i <= step ? "bg-primary" : "bg-muted"
                }`}
              />
            ))}
          </div>
          <p className="text-xs text-muted-foreground mt-2 text-center">
            Step {step + 1} of {totalSteps}
          </p>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {children}
        <div className="flex items-center justify-between pt-4">
          <Button variant="outline" onClick={onPrevious} disabled={isFirst}>
            <ChevronLeft className="h-4 w-4 mr-2" />
            Previous
          </Button>
          <Button onClick={onNext}>
            {isLast ? "Get Started" : "Next"}
            {!isLast && <ChevronRight className="h-4 w-4 ml-2" />}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
