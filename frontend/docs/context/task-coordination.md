# Task Coordination

*Main agent coordination for sub-agent system*

## Current Task
**Sample Test Task**: Create a responsive user dashboard component that displays user stats, recent activity, and quick actions. The component should support both light and dark themes, be fully accessible, and work seamlessly across mobile, tablet, and desktop devices.

**Requirements**:
- User profile section with avatar and basic info
- Statistics cards showing metrics (followers, posts, etc.)
- Recent activity list with timestamps
- Quick action buttons (edit profile, settings, logout)
- Loading states for async data
- Error handling for failed requests

## Sub-Agents Consulted
- [x] Chakra UI Sub-Agent - For component recommendations
- [x] Tailwind Sub-Agent - For responsive design strategy
- [x] Guidelines Compliance Agent - For code quality validation

## Execution Plan
*Synthesized from Chakra UI, Tailwind, and Guidelines Compliance agent recommendations*

### 1. Architectural Foundation (MVC Pattern)
Based on **Guidelines Compliance Agent** recommendations:
- Create `frontend/src/features/user-dashboard/` with MVC structure
- Split into 5 components (<50 lines each): DashboardContainer, ProfileSection, StatsCards, ActivityFeed, QuickActions
- Implement Zustand stores for state management
- Use custom hooks for data fetching controllers

### 2. Component Implementation Strategy
**Prioritized by Chakra UI Agent + Guidelines compliance:**
1. **DashboardContainer.tsx** - Main orchestrator using Chakra UI Grid
2. **ProfileSection.tsx** - Avatar (size="xl", bg="ui.main") + Badge + Heading
3. **StatsCards.tsx** - SimpleGrid with Stat components and StatArrow trends
4. **ActivityFeed.tsx** - VStack with Divider + Avatar (size="sm") + timestamp formatting  
5. **QuickActions.tsx** - VStack with Button variants (solid/outline/ghost)

### 3. Responsive Design Implementation
**Combined Chakra UI + Tailwind approach:**
- **Primary**: Chakra UI breakpoints `{ base: 1, sm: 2, lg: 4 }` for components
- **Enhancement**: Tailwind utilities for complex grid layouts and positioning
- **Container**: `maxW="container.xl"` with responsive padding
- **Grid**: `SimpleGrid columns={{ base: 1, lg: 3 }}` for main/sidebar layout

### 4. Theme Integration
**Chakra UI first approach:**
- Use `useColorMode()` and `useColorModeValue()` hooks
- Implement dual theme with existing color tokens (ui.main: #2463eb, bg: #f4f8fe)
- Apply `color="fg"` and `color="fg.muted"` for theme-aware text
- Avoid inline styles completely

### 5. Loading & Error States
**Chakra UI Skeleton + Tailwind animations:**
- Use `<Skeleton>`, `<SkeletonCircle>` for loading states
- Implement staggered loading with Tailwind `stagger-load` classes
- Error boundaries with `<Alert status="error" variant="left-accent">`
- Success states with proper ARIA attributes

### 6. Performance Optimizations
**Combined approach:**
- Chakra UI: Built-in performance with proper component usage
- Tailwind: `transform-gpu` and `will-change-transform` for animations
- React.memo for pure components (ProfileSection, StatsCards)
- Single useEffect for data loading per Guidelines requirements

### 7. TypeScript Implementation
**Strict compliance:**
- Define interfaces for User, Stats, Activity, ApiResponse
- No `any` types allowed
- Proper generic constraints for data fetching hooks
- Type-safe store implementations with Zustand

## Implementation Status
- ✅ Task analysis complete
- ✅ Sub-agent consultations complete
- ✅ Execution plan synthesis complete
- ⏳ Architecture setup pending
- ⏳ Component implementation pending
- ⏳ Testing and validation pending

## Next Steps
1. **Create MVC directory structure** in `frontend/src/features/user-dashboard/`
2. **Define TypeScript interfaces** in `models/types.ts`
3. **Implement Zustand stores** for user data and activity
4. **Build controller hooks** for data fetching logic
5. **Create view components** following Chakra UI + compliance guidelines
6. **Add loading/error states** with proper accessibility
7. **Write unit tests** for each component
8. **Validate responsive design** across all breakpoints
9. **Test accessibility** with screen readers
10. **Run compliance validation** against Guidelines agent checklist

### Conflict Resolution Applied:
- **Chakra UI vs Tailwind**: Chakra UI components prioritized, Tailwind for layout/animations only
- **Performance vs Guidelines**: Component decomposition maintains both performance and <50 line rule
- **Responsive Strategy**: Combined approach using both Chakra breakpoints and Tailwind utilities where beneficial

### Success Metrics:
- Guidelines Compliance Score: Target 95/100
- All components under 50 lines
- Zero TypeScript `any` types
- Full responsive design coverage
- Accessibility compliance (WCAG 2.1)
- Performance budget maintained

---
*Last updated: 2025-08-27*
*Task ID: dashboard-component-test-001*