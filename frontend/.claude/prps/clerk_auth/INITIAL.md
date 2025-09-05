## FEATURE:
- Look to linear workspace matchbot_ai, create a ticket for clerk auth for clerk_auth_frontend(word it better)
- Clerk Auth UI intergation that incoporates clerk UI components for React
- Make sure the components implentation replcaes the current user auth actions like login, signup, forgot password, profile, logout and list all users from the backend for admins.
- Maintain the dashboard as is and the initial landing screen and any existing screens.
- For the adjusted screens ensure you follow the frontend style guide.
- Ensure to reference with the backend to design this feature with full context.
- write results to changelog.md for easy tracking, no cdoe should be added, just add short description and the task ID
- What you think isn't built yet in the bakcned regarding clerk but exists in the frontend, make sure you create a linear task for it, tag it as claude recommendation, either with another tag frontend or backend.

# Additions
- write tests for both unit and e2e and intergation, 70%, 20% and 10% simultaneously. Place them in the tests folder under the auth feature, make sure they all pass.
- Make sure this follows a theme for both light and dark mode. for any styles that dont't fit inline add them in styles foler under auth feature.
- Suggest any secrets that need to be included in the project.
- Use linear workspace matchbot_ai, create a ticket for clerk auth for clerk_auth_frontend(word it better), 


## EXAMPLES:

In the `examples/` folder, there is a README for you to read to understand what the example is all about and also how to structure your own README when you create documentation for the above feature.

- `frontend/.claude/examples/product_ui` - use this as the design guide on how the app should be built like
- `frontend/docs/` - read through all of the files here to understand best way to contribute to this project.
- `frontend/CLAUDE.md` - read through this for the best practices of the frontend project

Don't copy any of these examples directly, it is for a different project entirely. But use this as inspiration and for best practices.

## DOCUMENTATION:

- `https://chakra-ui.com/docs/components/` - search through for any components
- `https://tailwindcss.com/docs/styling-with-utility-classes` - read through tailwind docs where required.
- `https://clerk.com/docs/authentication/overview` - read through for more context for clerk ui
- `frontend/.claude/examples/chakra_ui_3_llm.txt` - for local llm chakra ui docs

## OTHER CONSIDERATIONS:

- place the prps for this feature under `frontend/.claude/prps/clerk_auth`.
- Add logging and debugging to debug easily in production.
- Don't commit sensitive files or secrets
- Go through the CLAUDE.md to get more direction son the code style.
- Utilize sub-agents for specialised tasks.
- Think Hard before executing, use one or two solutions as a sernior engineer and choose the best.
- Ask for more context if still lacking