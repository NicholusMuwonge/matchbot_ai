# Frontend Guidelines Enforcement Rules

## Critical Violations (Score: 0/20)

### TypeScript Violations
- **Any Type Usage**: Any occurrence of `any` type
- **Missing Type Definitions**: Functions/variables without explicit types
- **Improper Interface Design**: Interfaces that don't follow naming conventions
- **Generic Constraints Missing**: Unconstrained generic types

### React Anti-Patterns
- **Excessive useEffect**: More than 2 useEffects per component without justification
- **Improper Hook Usage**: Hooks called conditionally or in loops
- **Direct DOM Manipulation**: Using refs to manipulate DOM instead of React patterns
- **Component Mutation**: Mutating props or state directly

## Major Violations (Score: 5/20)

### File Structure Issues
- **Oversized Files**: Files exceeding 150 lines
- **Poor Organization**: Mixed concerns within single file
- **Missing Modularization**: Large implementations not broken into modules
- **Circular Dependencies**: Import cycles between modules

### Code Quality Issues
- **Large Functions**: Functions exceeding 50 lines
- **Multiple Responsibilities**: Functions handling multiple concerns
- **Poor Naming**: Non-descriptive function/variable names
- **Unnecessary Complexity**: Overly complex solutions to simple problems

## Minor Violations (Score: 10/20)

### Documentation Issues
- **Unnecessary Comments**: Code that should be self-documenting
- **Missing JSDoc**: Complex functions without proper documentation
- **Outdated Comments**: Comments that don't match current implementation

### Style Inconsistencies
- **Inconsistent Patterns**: Mixed architectural approaches
- **Import Organization**: Poorly organized import statements
- **Export Patterns**: Inconsistent export styles

## UI/UX Standards Enforcement

### Critical UI Violations (Score: 0/20)
- **Inline Styles Present**: Any use of style prop instead of Chakra system
- **Custom Components First**: Building custom before checking Chakra UI
- **Missing Theme Support**: Components without light/dark variants
- **Color Scheme Violations**: Wrong background (#f4f8fe) or accent (#2463eb) colors

### Major UI Violations (Score: 5/20)
- **Poor Chakra Usage**: Misusing Chakra components or props
- **Accessibility Ignored**: Missing a11y features that Chakra provides
- **Documentation Skipped**: Not consulting Chakra docs for implementation
- **Responsive Neglect**: No consideration for different screen sizes

### Minor UI Violations (Score: 10/20)
- **Theme Configuration Unused**: Not leveraging Chakra's theme system
- **Component Library Patterns**: Not following established Chakra patterns
- **Performance Impact**: Inefficient Chakra component usage

## Responsive Design Requirements

### Critical Responsive Violations (Score: 0/15)
- **No Mobile Consideration**: Design only works on desktop
- **Fixed Dimensions**: Hard-coded sizes that break responsiveness
- **Overflow Issues**: Content that breaks layout on smaller screens

### Major Responsive Violations (Score: 5/15)
- **Limited Breakpoint Usage**: Only considering one or two screen sizes
- **Component Reuse Ignored**: Creating duplicate components instead of using shared
- **Touch Target Issues**: Interactive elements too small for mobile

### Minor Responsive Violations (Score: 10/15)
- **Suboptimal Breakpoints**: Using breakpoints that don't match design needs
- **Performance on Mobile**: Heavy components that impact mobile performance

## Architecture Pattern Enforcement

### Critical Architecture Violations (Score: 0/20)
- **No MVC Separation**: Mixed Model/View/Controller concerns
- **Missing Feature Structure**: Not following feature folder pattern
- **State Management Chaos**: Inconsistent state management approaches

### Major Architecture Violations (Score: 5/20)
- **Poor Separation of Concerns**: Logic mixed with presentation
- **Inconsistent Patterns**: Different architectural approaches in same project
- **Missing Business Logic Layer**: No clear controller layer

### Minor Architecture Violations (Score: 10/20)
- **Suboptimal State Management**: Using less efficient state management patterns
- **Component Hierarchy Issues**: Poor component composition

## Testing & Quality Standards

### Critical Testing Violations (Score: 0/25)
- **No Unit Tests**: Missing tests for new implementations
- **Linting Failures**: Code that doesn't pass linting
- **Build Breaking**: Changes that break the build process

### Major Testing Violations (Score: 5/25)
- **Insufficient Test Coverage**: Tests don't cover main functionality
- **Poor Test Quality**: Tests that don't validate behavior properly
- **Integration Issues**: Components that don't integrate properly

### Minor Testing Violations (Score: 10/25)
- **Test Organization**: Poorly organized test files
- **Mock Usage**: Inappropriate or missing mocks

## Auto-Remediation Suggestions

### TypeScript Fixes
```typescript
// ❌ Violation
function processData(data: any): any {
  return data.map((item: any) => item.value);
}

// ✅ Compliant
interface DataItem {
  value: string;
}

function processData(data: DataItem[]): string[] {
  return data.map(item => item.value);
}
```

### React Pattern Fixes
```tsx
// ❌ Violation - Multiple useEffects
useEffect(() => { fetchUserData(); }, [userId]);
useEffect(() => { fetchUserPosts(); }, [userId]);
useEffect(() => { updateTitle(); }, [userName]);

// ✅ Compliant - Combined with clear purpose
useEffect(() => {
  async function loadUserData() {
    const userData = await fetchUserData(userId);
    const userPosts = await fetchUserPosts(userId);
    updateTitle(userData.name);
  }
  loadUserData();
}, [userId]);
```

### Chakra UI Fixes
```tsx
// ❌ Violation - Inline styles
<div style={{ backgroundColor: '#f4f8fe', padding: '20px' }}>
  <button style={{ color: '#2463eb' }}>Click me</button>
</div>

// ✅ Compliant - Chakra system
<Box bg="#f4f8fe" p={5}>
  <Button colorScheme="blue">Click me</Button>
</Box>
```

## Scoring Algorithm

### Overall Score Calculation
```
Total Score = (
  TypeScript Score (20) +
  Code Quality Score (25) +
  Architecture Score (20) +
  UI/UX Score (20) +
  Responsive Score (15)
) / 100
```

### Grade Thresholds
- **A (90-100)**: Excellent compliance, minimal issues
- **B (80-89)**: Good compliance, minor improvements needed
- **C (70-79)**: Adequate compliance, several issues to address
- **D (60-69)**: Poor compliance, major refactoring required
- **F (0-59)**: Critical violations, significant rework needed

## Enforcement Actions

### Score-Based Actions
- **90-100**: Approve with minor suggestions
- **80-89**: Request minor revisions
- **70-79**: Require moderate refactoring
- **60-69**: Major refactoring required before approval
- **0-59**: Reject and request complete redesign

### Violation-Specific Actions
- **Critical Violations**: Immediate blocking of progress
- **Major Violations**: Required fixes before proceeding
- **Minor Violations**: Recommended improvements

## Continuous Improvement

### Pattern Recognition
- Track common violation patterns
- Update enforcement rules based on team feedback
- Refine scoring algorithm for accuracy
- Add new rules as project evolves

### Team Education
- Provide examples of compliant vs non-compliant code
- Share best practices based on common violations
- Update team training based on enforcement findings
- Create quick reference guides for common fixes