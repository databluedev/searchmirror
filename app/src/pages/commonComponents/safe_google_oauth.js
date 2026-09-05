import React from "react";
import { GoogleOAuthProvider } from "@react-oauth/google";

/**
 * GoogleOAuthProvider throws "Missing required parameter client_id" the moment
 * it mounts with an empty string, and it takes the whole page subtree down with
 * it -- an uncaught error, not a warning. A self-hosted instance has exactly
 * that until the operator registers their own Google app and sets
 * VITE_GSC_CLIENT_ID, so every screen that mounts the provider (Add Project,
 * the Google sign-in button, Connected Apps) crashed out of the box.
 *
 * This renders the provider only when a client id is actually present. With no
 * id the Google-connected controls simply do not appear, which is the correct
 * state for an instance that cannot talk to Google yet -- far better than a
 * blank page. `fallback` lets a caller show an explanatory note in that slot.
 */
function SafeGoogleOAuthProvider({ clientId, children, fallback = null }) {
   if (!clientId) {
      return fallback;
   }
   return <GoogleOAuthProvider clientId={clientId}>{children}</GoogleOAuthProvider>;
}

export default SafeGoogleOAuthProvider;
