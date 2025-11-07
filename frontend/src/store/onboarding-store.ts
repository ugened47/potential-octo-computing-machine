import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

interface OnboardingState {
  isCompleted: boolean
  currentStep: number
  completedSteps: number[]
  skipOnboarding: () => void
  completeStep: (step: number) => void
  setCurrentStep: (step: number) => void
  reset: () => void
}

const TOTAL_STEPS = 4

export const useOnboarding = create<OnboardingState>()(
  persist(
    (set) => ({
      isCompleted: false,
      currentStep: 0,
      completedSteps: [],
      skipOnboarding: () => set({ isCompleted: true }),
      completeStep: (step: number) =>
        set((state) => {
          const newCompletedSteps = state.completedSteps.includes(step)
            ? state.completedSteps
            : [...state.completedSteps, step]
          const isCompleted = newCompletedSteps.length === TOTAL_STEPS
          return {
            completedSteps: newCompletedSteps,
            isCompleted,
            currentStep: isCompleted ? state.currentStep : state.currentStep + 1,
          }
        }),
      setCurrentStep: (step: number) => set({ currentStep: step }),
      reset: () =>
        set({
          isCompleted: false,
          currentStep: 0,
          completedSteps: [],
        }),
    }),
    {
      name: 'onboarding-storage',
      storage: createJSONStorage(() => localStorage),
    }
  )
)

