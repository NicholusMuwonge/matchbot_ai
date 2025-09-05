# Tailwind Designer MCP Setup Guide

## Installation Status
✅ **INSTALLED** - Tailwind Designer MCP Server is configured and ready

## Installation Command
```bash
claude mcp add tailwind-designer -- npx -y tailwind-designer-mcp
```

## Configuration
The MCP server is configured in `~/.claude.json`:
```json
{
  "mcpServers": {
    "tailwind-designer": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "tailwind-designer-mcp"],
      "env": {}
    }
  }
}
```

## Verification
Test MCP connection:
```bash
# List available MCP servers
claude mcp list

# Should show:
# tailwind-designer (stdio) - npx -y tailwind-designer-mcp
```

## Available MCP Functions

### Design Generation
- `create_component(description)` - Generate Tailwind component from text description
- `optimize_css(css_code)` - Identify and remove redundant classes
- `convert_css_to_tailwind(css)` - Convert traditional CSS to Tailwind utilities

### Visual Tools
- `generate_preview(html_with_tailwind)` - Create visual preview of components
- `validate_design_system(component)` - Check design system compatibility
- `suggest_improvements(component)` - Recommend optimizations

### Responsive Design
- `create_responsive_layout(requirements)` - Generate mobile-first layouts
- `optimize_breakpoints(component)` - Optimize responsive breakpoint usage
- `validate_accessibility(component)` - Check accessibility compliance

## Advanced Configuration

### Project-Specific Setup
Create a local configuration file for project-specific settings:

```json
// .tailwind-mcp.json
{
  "theme": {
    "extend": {
      "colors": {
        "brand": {
          "50": "#f0f9ff",
          "500": "#3b82f6",
          "900": "#1e3a8a"
        }
      }
    }
  },
  "designSystemRules": {
    "spacing": "4-based",
    "typography": "fluid-scale",
    "colors": "semantic-naming"
  }
}
```

### Environment Variables
Optional configuration for enhanced features:
```bash
# Add to environment or MCP config
TAILWIND_CONFIG_PATH=./tailwind.config.js
DESIGN_SYSTEM_TOKENS=./design-tokens.json
OUTPUT_FORMAT=html # or jsx, vue, etc.
```

## Integration with Build Tools

### Vite Integration
```javascript
// vite.config.ts
import { defineConfig } from 'vite'

export default defineConfig({
  css: {
    postcss: {
      plugins: [
        require('tailwindcss'),
        require('autoprefixer'),
      ]
    }
  }
})
```

### Tailwind Configuration
```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,jsx,ts,tsx}'],
  theme: {
    extend: {
      // Custom extensions will be detected by MCP
    },
  },
  plugins: [
    // Plugin compatibility will be analyzed
  ],
}
```

## Troubleshooting

### Common Issues
1. **MCP not responding:** Check Node.js version compatibility
2. **Design generation errors:** Verify Tailwind config is valid
3. **Preview not working:** Ensure HTML structure is valid
4. **Optimization not applying:** Check for conflicting CSS

### Debug Commands
```bash
# Check MCP server status
claude mcp status tailwind-designer

# View MCP logs for debugging
claude mcp logs tailwind-designer

# Test MCP functions directly
claude mcp test tailwind-designer create_component "blue button with rounded corners"
```

### Performance Optimization
```bash
# Monitor MCP performance
claude mcp monitor tailwind-designer

# Cache optimization
export TAILWIND_MCP_CACHE_SIZE=1000
export TAILWIND_MCP_CACHE_TTL=3600
```

## Dependencies
- **Node.js** (version 16+ recommended)
- **Tailwind CSS** (version 3+ for best compatibility)
- **PostCSS** (for CSS processing)
- **Internet connection** (for package downloads)

## Best Practices

### MCP Usage Patterns
```javascript
// Efficient component generation
const component = await createComponent({
  description: "responsive card with image, title, and description",
  constraints: {
    maxWidth: "md",
    colorScheme: "blue",
    accessibility: true
  }
});

// Batch optimization
const optimizedCSS = await optimizeCss({
  input: multipleComponents,
  removeUnused: true,
  combineClasses: true
});
```

### Error Handling
```javascript
try {
  const result = await mcpFunction(params);
  return result;
} catch (error) {
  console.error('MCP Error:', error.message);
  // Fallback to basic recommendations
  return generateBasicRecommendations(params);
}
```

## Security Considerations
- MCP server runs in sandboxed environment
- No file system access beyond configuration
- Network requests limited to CDN resources
- Input validation for all design descriptions