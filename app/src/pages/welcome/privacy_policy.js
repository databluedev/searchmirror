import React from "react";
import { Link } from "react-router-dom";
import { ParaLg, Title } from "../commonComponents/parts";

const sections = [
  {
    title: "Who operates your data",
    paragraphs: [
      "SearchMirror is open-source software. If you self-host it, you or your organisation operates the deployment and controls the data stored in it. The SearchMirror maintainers do not automatically receive data from self-hosted instances.",
      "If you use an instance hosted by somebody else, that instance operator is responsible for its data handling and retention practices.",
    ],
  },
  {
    title: "Data the application stores",
    paragraphs: [
      "The application stores the account and team details you provide, including names, email addresses, roles, and authentication records.",
      "It also stores the SEO workspace data you create, such as projects, domains, keywords, rankings, competitors, notes, tags, reports, and product settings.",
      "Operational logs may contain request timing, error details, IP addresses, user-agent information, and identifiers needed to secure and troubleshoot the service.",
    ],
  },
  {
    title: "Provider keys",
    paragraphs: [
      "SearchMirror uses your own DataBlue key for search results and can use optional AI-provider keys for supported analysis features. Provider keys are encrypted at rest, masked in the interface, and sent only to the selected provider when the application performs a request for your account.",
      "SearchMirror does not collect payment details. DataBlue and optional AI providers bill you directly under their own terms; their privacy policies apply to data sent to them.",
    ],
  },
  {
    title: "Sessions and local storage",
    paragraphs: [
      "The application uses essential cookies and browser storage to keep you signed in, remember the active project, and preserve interface preferences. Blocking this storage may prevent authenticated features from working.",
    ],
  },
  {
    title: "Retention and security",
    paragraphs: [
      "The instance operator decides how long account, project, and log data is retained. Ask that operator to correct or delete your data. Self-hosters can manage retention directly in their deployment.",
      "SearchMirror includes access controls and encrypted credential storage, but no internet service can guarantee absolute security. Keep the application updated, restrict administrative access, use HTTPS, and protect the deployment encryption key.",
    ],
  },
  {
    title: "Questions and changes",
    paragraphs: [
      "Questions about a hosted instance should go to its operator. Questions about the open-source project can be raised through the contact channels listed in the repository README.",
      "This policy may change as the product changes. Material updates should be published with the application or repository.",
    ],
  },
];

function PrivacyPolicy() {
  return (
    <main className="overflow-scroll p-4" style={{ height: "100vh" }}>
      <div className="container py-4">
        <div className="mx-auto" style={{ maxWidth: "860px" }}>
          {/* Reached from the sign-up form and from the marketing
              footer, and previously a dead end from both. */}
          <Link to="/" className="lightTxtClr d-inline-block mb-4">&larr; Back to SearchMirror</Link>

          <header className="mb-5">
            <h1 className="h2-md fB">Privacy Policy</h1>
            <ParaLg class="mt-2">Last updated: August 31, 2026</ParaLg>
          </header>

          {sections.map((section) => (
            <section className="mb-5" key={section.title}>
              <Title class="fsL">{section.title}</Title>
              {section.paragraphs.map((paragraph) => (
                <ParaLg class="mt-3" key={paragraph}>{paragraph}</ParaLg>
              ))}
            </section>
          ))}
        </div>
      </div>
    </main>
  );
}

export default PrivacyPolicy;
