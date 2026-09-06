import React from "react";
import { Link } from "react-router-dom";

/* A feature the account cannot use yet.

   docs/DESIGN.md, "Empty state": micro-label, one sentence, one action, no art.
   This reuses the house `emptyState` block rather than inventing a second one --
   `widget/components/dash_states.js` renders the same classes for the dashboard's
   own three states.

   There are THREE reasons a screen is not ready, and the product used to answer
   all of them the same way: with whatever the API said, in a red toast. They are
   different facts and each needs a different next step:

     no project     -- the account is empty; create one
     no credential  -- the feature needs a provider key; add it in Settings
     no measurement -- a project exists but nothing has been ranked yet

   The caller decides which one applies, because the caller already knows: the
   project list length, or `useCapability()` for a credential. Nothing is guessed
   here. This component only renders the answer.

   `action` is optional on purpose. A team member without permission to add a
   project should be told why the screen is empty without being offered a button
   that would fail -- the same reasoning `NoProjects` already applies. */
function NotReady({ label, children, actionLabel, actionTo, onAction, note }) {
   const hasAction = Boolean(actionLabel && (actionTo || onAction));

   return (
      <div className="emptyState">
         <p className="emptyState__label">{label}</p>
         <p className="emptyState__body">{children}</p>

         {hasAction ? (
            <div className="emptyState__action">
               {actionTo ? (
                  <Link className="btn btn-primary" to={actionTo}>
                     {actionLabel}
                  </Link>
               ) : (
                  <button type="button" className="btn btn-primary" onClick={onAction}>
                     {actionLabel}
                  </button>
               )}
            </div>
         ) : null}

         {note ? <p className="emptyState__body">{note}</p> : null}
      </div>
   );
}

/* The no-project case, which is the one every project-scoped screen shares.
   `feature` names what the screen would have shown, so the sentence says why
   THIS page is empty rather than repeating a generic line on all of them. */
export function NoProjectYet({ feature, canAddProject = true }) {
   return (
      <NotReady
         label="No projects"
         actionLabel={canAddProject ? "Add project" : null}
         actionTo={canAddProject ? "/addproject" : null}
      >
         {feature} needs a project to report on. Add the site you want to track
         and this page fills in from there.
      </NotReady>
   );
}

export default NotReady;
