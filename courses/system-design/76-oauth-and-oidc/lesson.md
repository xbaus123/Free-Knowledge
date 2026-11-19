# OAuth 2.0 and OpenID Connect

*Chapter 2 · The Front Door.*

## OAuth 2.0 and OpenID Connect

Suppose a photo-printing site wants to read your photos from a cloud drive. Giving it your password would hand it your whole account, forever. **OAuth 2.0** is a framework for **delegated authorization**: the user grants a third-party app limited access, and the app never sees the user's password. It defines four roles:

- **Resource owner**: the user.
- **Client**: the app that wants access (the printing site, or your own mobile app).
- **Authorization server**: authenticates the user and issues tokens (Auth0, Okta, Keycloak, Google, or your own).
- **Resource server**: the API holding the data, which accepts the tokens.

### The authorization code flow with PKCE

This is the flow to use for any app with a user:

1. The client generates a random **code verifier** and sends its hash (the **code challenge**) when redirecting the user to the authorization server: `/authorize?client_id=…&scope=photos.read&code_challenge=…&state=…`.
2. The user logs in *at the authorization server*, not at the client, and approves the requested **scopes**.
3. The authorization server redirects back to the client with a short-lived, single-use **authorization code**.
4. The client exchanges the code, plus the original code verifier, for an **access token** (and usually a refresh token) on a direct back-channel request.
5. The client calls the API with `Authorization: Bearer <access token>`.

Why the extra hop through a code? The redirect in step 3 travels through the browser, where URLs leak into history, logs, and `Referer` headers. The code is useless on its own: exchanging it needs the code verifier (**PKCE**, Proof Key for Code Exchange), which never left the client. So an intercepted code can't be redeemed. The `state` parameter ties the response to the request the client made, which stops an attacker from injecting their own code (CSRF on the login flow).

For **service-to-service** calls with no user involved, the **client credentials** flow has a service authenticate directly with its own credentials and receive a token naming the service itself.

### OpenID Connect

OAuth answers "may this app access this API?" It deliberately doesn't say *who the user is*. **OpenID Connect (OIDC)** is a thin identity layer on top. Add the `openid` scope, and the authorization server also returns an **ID token**: a JWT about the authentication itself (`sub`, `email`, when and how the user logged in), intended for the **client**. OIDC also standardizes discovery (`/.well-known/openid-configuration` lists the endpoints and the JWKS URL), so "Sign in with Google" works the same way everywhere.

Keep the two tokens straight: the **ID token** tells the client who logged in, and the **access token** is what the client presents to APIs. An API should never accept an ID token as authorization.

Next, a short check on what you just read.
