# Fix this

- We could reuse this as a skeleton loader component, under components, with props like; isloaded, type(tabel, line, circle, box), size, with props for expanding the size, light or dark. Think hard and do better than this. This way we can reusing it whereever there's a loader. 

Typescript```
<VStack height="100vh" justify="center" align="center" gap={4}>
          <Spinner
            size="lg"
            colorPalette="blue"
            color={{ base: "blue.500", _dark: "blue.400" }}
          />
          <Text color={{ base: "gray.600", _dark: "gray.300" }}>
            Loading...
          </Text>
        </VStack>
```
- This would best be placed in one place in the router so it can check for with isloaded, isSignedIn and do as expected
```
if (isLoaded && isSignedIn) {
    return null
  }

```

- since these dont change often but might change and be used everywhere else, lets make sure we use them as contants in a constants file in the root of the frontend 

```
const {
    fallbackRedirectUrl = "/",
    signInFallbackRedirectUrl = "/signin",
    signUpFallbackRedirectUrl = "/signup",
  } = options
```

- We need to delete this frontend/src/features/auth/styles/auth-theme.ts.backup, frontend/tests/reset-password.spec.ts.disabled
- Remove all unnecessary comments from the affected files
- Fix all failing tests