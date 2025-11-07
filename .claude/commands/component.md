---
description: Create a new React component with Shadcn UI
argument-hint: [component-name]
---

Create a new React component named "$1" following Next.js 14 best practices:

1. **Read existing patterns** - Check frontend/src/components/ for similar components
2. **Determine component type**:
   - Server Component (default) - for static content, data fetching
   - Client Component ('use client') - for interactivity, hooks, browser APIs

3. **Create component** - Add to appropriate directory:
   - UI primitives: frontend/src/components/ui/
   - Video features: frontend/src/components/video/
   - Timeline: frontend/src/components/timeline/
   - Other: frontend/src/components/

4. **Component structure**:
   ```typescript
   import { type ComponentProps } from 'react'

   interface $1Props {
     // Define props with TypeScript
   }

   export function $1({ ...props }: $1Props) {
     // Implementation
     return (
       <div>
         {/* Use Shadcn UI components */}
       </div>
     )
   }
   ```

5. **Add types** - Define TypeScript interfaces in frontend/src/types/ if needed
6. **Write tests** - Create component test with Vitest
7. **Verify**:
   - Type check: `cd frontend && tsc --noEmit`
   - Lint: `cd frontend && npm run lint`
   - Test: `cd frontend && npm test`

Use Shadcn UI components from @/components/ui/ for consistency.
