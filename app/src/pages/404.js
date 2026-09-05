import React from "react";
import { Link } from "react-router-dom";

// Type-led, monochrome: micro-label, headline, one sentence, one pill back into
// the app. It replaces a colourful stock illustration (assets/images/
// not-found.svg) that belonged to no other screen in the system -- docs/
// DESIGN.md, "Empty state" and "Non-negotiable" #7.
//
// Two modes, as before: `pagetype="apiError"` is rendered when a request fails
// (App.js, welcome/authenticate.js); everything else is a genuine 404.
function Notfound(props) {
  const apiError = props.pagetype === "apiError";

  return (
    <section className="notFound w-100">
      <div className="emptyState">
        <p className="emptyState__label">{apiError ? "Error" : "404"}</p>
        <h1 className="emptyState__title">
          {apiError ? "Something went wrong" : "Page not found"}
        </h1>
        <p className="emptyState__body">
          {apiError
            ? "SearchMirror could not reach the server, so this page has nothing to show; wait a moment and try again."
            : "The address you followed does not match anything in SearchMirror, so it has either moved or never existed."}
        </p>
        <Link className="btn btn-primary emptyState__action" to="/">
          Go to dashboard
        </Link>
      </div>
    </section>
  );
}
export default Notfound;
