# Tailwind CSS Agent Capabilities

## Core Utility Classes

### Layout Utilities
- **Display:** `block`, `inline`, `flex`, `grid`, `table`
- **Position:** `static`, `relative`, `absolute`, `fixed`, `sticky`
- **Float & Clear:** `float-left`, `float-right`, `clear-both`
- **Visibility:** `visible`, `invisible`, `opacity-*`

### Flexbox & Grid
- **Flex Direction:** `flex-row`, `flex-col`, `flex-row-reverse`
- **Flex Wrap:** `flex-wrap`, `flex-nowrap`, `flex-wrap-reverse`
- **Align Items:** `items-start`, `items-center`, `items-end`, `items-stretch`
- **Justify Content:** `justify-start`, `justify-center`, `justify-between`
- **Grid Templates:** `grid-cols-*`, `grid-rows-*`, `col-span-*`

### Spacing & Sizing
- **Padding:** `p-*`, `px-*`, `py-*`, `pt-*`, `pr-*`, `pb-*`, `pl-*`
- **Margin:** `m-*`, `mx-*`, `my-*`, `mt-*`, `mr-*`, `mb-*`, `ml-*`
- **Width:** `w-*`, `min-w-*`, `max-w-*`
- **Height:** `h-*`, `min-h-*`, `max-h-*`

## Typography System

### Font Properties
- **Family:** `font-sans`, `font-serif`, `font-mono`
- **Size:** `text-xs`, `text-sm`, `text-base`, `text-lg`, `text-xl`, `text-2xl`+
- **Weight:** `font-thin`, `font-normal`, `font-medium`, `font-semibold`, `font-bold`
- **Style:** `italic`, `not-italic`

### Text Alignment & Decoration
- **Align:** `text-left`, `text-center`, `text-right`, `text-justify`
- **Decoration:** `underline`, `line-through`, `no-underline`
- **Transform:** `uppercase`, `lowercase`, `capitalize`, `normal-case`
- **Leading:** `leading-none`, `leading-tight`, `leading-normal`, `leading-relaxed`

## Color System

### Color Palette
- **Gray Scale:** `gray-50` through `gray-950`
- **Primary Colors:** `red-*`, `blue-*`, `green-*`, `yellow-*`, `purple-*`
- **Extended Palette:** `orange-*`, `amber-*`, `lime-*`, `emerald-*`, `teal-*`, `cyan-*`, `sky-*`, `indigo-*`, `violet-*`, `fuchsia-*`, `pink-*`, `rose-*`

### Color Applications
- **Text:** `text-gray-900`, `text-blue-600`
- **Background:** `bg-white`, `bg-gray-100`, `bg-blue-500`
- **Border:** `border-gray-300`, `border-red-500`
- **Ring:** `ring-blue-500`, `ring-opacity-50`

## Responsive Design

### Breakpoint System
```css
/* Default breakpoints */
sm: 640px   /* Small devices */
md: 768px   /* Medium devices */
lg: 1024px  /* Large devices */
xl: 1280px  /* Extra large devices */
2xl: 1536px /* 2X large devices */
```

### Responsive Utilities
- **Mobile First:** Base styles apply to all sizes
- **Breakpoint Prefixes:** `sm:`, `md:`, `lg:`, `xl:`, `2xl:`
- **State Combinations:** `md:hover:bg-blue-600`

### Container Queries
- **Container:** `@container` support for component-level responsiveness
- **Container Size:** `@sm`, `@md`, `@lg` container breakpoints

## Interactive States

### Hover & Focus
- **Hover:** `hover:bg-blue-600`, `hover:scale-105`
- **Focus:** `focus:outline-none`, `focus:ring-2`, `focus:ring-blue-500`
- **Active:** `active:bg-blue-700`, `active:scale-95`
- **Disabled:** `disabled:opacity-50`, `disabled:cursor-not-allowed`

### Group & Peer States
- **Group Hover:** `group-hover:translate-x-2`
- **Peer Focus:** `peer-focus:text-blue-600`
- **Group States:** `group-active`, `group-focus`, `group-disabled`

## Animation & Transitions

### Transitions
- **Property:** `transition-colors`, `transition-transform`, `transition-all`
- **Duration:** `duration-75`, `duration-150`, `duration-300`, `duration-500`
- **Timing:** `ease-linear`, `ease-in`, `ease-out`, `ease-in-out`
- **Delay:** `delay-75`, `delay-150`, `delay-300`

### Transforms
- **Scale:** `scale-50`, `scale-100`, `scale-125`
- **Rotate:** `rotate-45`, `rotate-90`, `rotate-180`
- **Translate:** `translate-x-4`, `translate-y-2`
- **Skew:** `skew-x-12`, `skew-y-6`

### Animations
- **Predefined:** `animate-spin`, `animate-ping`, `animate-pulse`, `animate-bounce`
- **Custom Keyframes:** Support for custom animation definitions

## Borders & Effects

### Border Properties
- **Width:** `border`, `border-2`, `border-4`, `border-8`
- **Style:** `border-solid`, `border-dashed`, `border-dotted`
- **Radius:** `rounded`, `rounded-lg`, `rounded-full`
- **Individual Corners:** `rounded-tl-lg`, `rounded-br-md`

### Shadow Effects
- **Box Shadow:** `shadow-sm`, `shadow`, `shadow-lg`, `shadow-xl`
- **Colored Shadows:** `shadow-blue-500/50`
- **Inner Shadow:** `shadow-inner`
- **Drop Shadow:** `drop-shadow-lg`

## Advanced Features

### CSS Grid Advanced
- **Grid Areas:** `col-start-2`, `col-end-4`, `row-start-1`
- **Grid Flow:** `grid-flow-row`, `grid-flow-col`
- **Auto Fit/Fill:** `grid-cols-[repeat(auto-fit,minmax(200px,1fr))]`

### Custom Properties
- **CSS Variables:** `[--custom-property:value]`
- **Dynamic Values:** `bg-[color:var(--custom-bg)]`
- **Arbitrary Values:** `w-[32rem]`, `text-[#1da1f2]`

### Dark Mode
- **Dark Variant:** `dark:bg-gray-900`, `dark:text-white`
- **System Preference:** Automatic dark mode detection
- **Manual Toggle:** Class-based dark mode switching

## Performance Optimization

### JIT Compilation
- **Just-in-Time:** Generate styles on-demand
- **Reduced Bundle Size:** Only include used utilities
- **Dynamic Values:** Support for arbitrary values

### PurgeCSS Integration
- **Unused Style Removal:** Automatic dead code elimination
- **Content Detection:** Scan templates for class usage
- **Safelist Configuration:** Protect dynamic classes

## Accessibility Features

### Screen Reader Support
- **Screen Reader Only:** `sr-only`
- **Focus Visible:** `focus-visible:ring-2`
- **ARIA Integration:** Complementary to ARIA attributes

### Color Contrast
- **WCAG Compliance:** Built-in contrast ratios
- **Color Blindness:** Accessible color combinations
- **High Contrast:** Enhanced contrast options

## Design System Integration

### Design Tokens
- **Consistent Spacing:** 4px base spacing scale
- **Typography Scale:** Modular scale ratios
- **Color Semantics:** Semantic color naming

### Component Patterns
- **Composition:** Utility-based component building
- **Variants:** Responsive and state-based variants
- **Themes:** Customizable design system themes

## Browser Support

### Modern Browsers
- **Chrome/Edge:** Full support (latest versions)
- **Firefox:** Full support (latest versions)
- **Safari:** Full support (latest versions)

### Progressive Enhancement
- **Graceful Degradation:** Fallbacks for older browsers
- **Feature Detection:** CSS feature queries support
- **Polyfills:** Optional polyfill integration

## Limitations & Trade-offs

### Bundle Size Considerations
- **Development:** Large CSS file during development
- **Production:** Optimized with PurgeCSS
- **Critical CSS:** Extract above-fold styles

### Learning Curve
- **Utility Memorization:** Learning utility class names
- **Design Thinking:** Shift from component to utility mindset
- **Team Adoption:** Consistent usage patterns

### Customization Complexity
- **Deep Customization:** Some designs require custom CSS
- **Component Libraries:** Integration with existing libraries
- **Legacy Code:** Migration from existing CSS approaches