# Chakra UI MCP Setup Guide

## Installation Status
✅ **INSTALLED** - Chakra UI MCP Server is configured and ready

## Installation Command
```bash
claude mcp add chakra-ui -- npx -y @chakra-ui/react-mcp
```

## Configuration
The MCP server is configured in `~/.claude.json`:
```json
{
  "mcpServers": {
    "chakra-ui": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@chakra-ui/react-mcp"],
      "env": {}
    }
  }
}
```

## Optional: Chakra UI Pro Integration
For access to premium templates and advanced features:

1. **Get API Key:** Visit [Chakra UI Pro](https://pro.chakra-ui.com) and generate an API key
2. **Update Configuration:**
   ```bash
   claude mcp add chakra-ui --env CHAKRA_PRO_API_KEY=your_api_key_here -- npx -y @chakra-ui/react-mcp
   ```

## Verification
Test MCP connection:
```bash
# List available MCP servers
claude mcp list

# Should show:
# chakra-ui (stdio) - npx -y @chakra-ui/react-mcp
```

## Available MCP Functions

### Component Functions
- `list_components()` - List all available components
- `get_component_props(component_name)` - Get detailed props information
- `get_component_example(component_name)` - Get usage examples

### Theme Functions  
- `get_theme()` - Get design tokens and theme configuration
- `theme_customization()` - Custom theme guidance

### Pro Functions (requires API key)
- `list_component_templates()` - List premium templates
- `get_component_templates(template_name)` - Get premium templates

### Migration Functions
- `v2_to_v3_code_review(code)` - Migration assistance

## Troubleshooting

### Common Issues
1. **MCP not found:** Ensure Claude Code is restarted after installation
2. **Permission errors:** Run with appropriate permissions
3. **Pro features unavailable:** Verify API key is correctly configured

### Debug Commands
```bash
# Check MCP server status
claude mcp status chakra-ui

# View MCP logs
claude mcp logs chakra-ui
```

## Dependencies
- Node.js (for npx execution)
- Active internet connection (for package installation)
- Optional: Chakra UI Pro license for premium features