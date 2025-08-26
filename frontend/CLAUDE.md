# Frontend Development Guidelines

## Branching Strategy
For each change you make, you must create a new branch. After implementing changes, push them up and create a merge request (MR) to the develop branch.

## Development Workflow
1. Create a new branch for your changes
2. Implement the required modifications
3. Push the branch to remote
4. Create a merge request targeting the develop branch

## TypeScript & React Standards
- Always follow TypeScript and React best practices
- Consult React and latest TypeScript documentation
- **NEVER use `any` type in TypeScript** - always provide proper typing
- Limit the use of `useEffect` - only when absolutely required
- No file should exceed 150 lines - utilize modules for larger implementations

## Feature Development Architecture
- Create a feature folder in the frontend for each new feature
- Each feature should be self-contained with MVC pattern:
  - **Model**: State management (Zustand, Redux, or best fit for project)
  - **View**: UI components (dummy/presentational)
  - **Controller**: Business logic and data handling

## Pre-Implementation Planning
- Before each feature execution, document three possible approaches
- Place approach analysis in `.claude/prps/[feature_name]/` folder
- Choose and justify the best approach
- Always consider backend implementations (changelog) before planning

## Code Quality Standards
- Remove unnecessary comments (code should be self-documenting)
- Break down large functions into smaller, focused functions
- Single responsibility principle: each function does one thing well
- Use descriptive function and variable names
- Keep functions under 50 lines when possible

## Testing & Quality Assurance
- Write unit tests for each implementation
- Run linting before push
- Ensure all tests pass before submitting MR
- Follow test-driven development practices where applicable

## Backend Integration
- Always review backend changelog and implementations
- Plan frontend features considering existing backend capabilities
- Ensure proper API integration and error handling

## UI/UX Standards with Chakra UI
- **Always check Chakra UI first** - Before building custom components, verify if functionality exists in Chakra UI
- **No inline styles** - Use Chakra UI's styling system and theme configuration
- **Dual theme support** - Each component must have light and dark mode variants
- **Color scheme**:
  - Screen backgrounds: `#f4f8fe`
  - Primary accent color: `#2463eb`
- **Documentation first** - Read Chakra UI documentation when unsure, don't assume functionality
- **Accessibility** - Follow accessibility best practices and leverage Chakra UI's built-in accessibility features

## Responsive Design & Component Management
- **Responsive thinking** - Always consider how components fit on large, mid-sized, and mobile screens
- **Shared components** - Keep reusable components in the `shared` folder to prevent duplication
- **Component reuse** - Before creating new components, check the shared folder for existing solutions
- **Simplicity first** - Code should be simple and straightforward, not hard to understand
- **Clear intent** - Write code that clearly expresses its purpose without complexity
