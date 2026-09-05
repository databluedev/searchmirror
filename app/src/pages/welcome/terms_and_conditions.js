import React from "react";
import { Link } from "react-router-dom";
import { ParaLg, Title } from "../commonComponents/parts";

const sections = [
  {
    title: "Open-source software",
    paragraphs: [
      "SearchMirror is provided under the GNU Affero General Public License version 3. Your rights to use, study, modify, and redistribute the software are governed by that license.",
      "These terms describe use of the application and do not replace the licence included in the repository.",
    ],
  },
  {
    title: "Your account and deployment",
    paragraphs: [
      "You are responsible for the accuracy of account information, the security of your credentials, and activity performed through your account. Instance operators are responsible for configuring authentication, HTTPS, backups, access controls, and retention for their deployment.",
      "Team owners must grant only the permissions each member needs. Members must not attempt to access projects, settings, credentials, or data outside their assigned role.",
    ],
  },
  {
    title: "Bring your own provider keys",
    paragraphs: [
      "Search ranking checks use a DataBlue key supplied by the account owner. Optional AI features use provider keys supplied by the account owner. SearchMirror does not resell provider credits or add a usage markup.",
      "You are responsible for provider charges, quotas, acceptable-use rules, and the legality of data submitted to each provider. Provider availability and results are outside SearchMirror's control.",
    ],
  },
  {
    title: "Acceptable use",
    paragraphs: [
      "Do not use SearchMirror to break applicable law, violate third-party rights, access accounts or systems without permission, distribute malicious code, evade provider controls, or interfere with other users or the deployment.",
      "Instance operators may suspend access that threatens security, reliability, other users, or compliance obligations.",
    ],
  },
  {
    title: "Your data",
    paragraphs: [
      "You retain responsibility for the domains, keywords, notes, reports, credentials, and other content you enter. You must have the rights and permissions needed to process that data.",
      "The instance operator controls backups, export, retention, and deletion. Export important data and maintain appropriate backups for your deployment.",
    ],
  },
  {
    title: "Service limitations",
    paragraphs: [
      "The software is provided without warranties, as described in the AGPL-3.0 licence. Rankings and generated analysis can be incomplete, delayed, or inaccurate and should be independently reviewed before important decisions.",
      "Features that depend on provider credentials, OAuth configuration, or external services are available only when those capabilities are configured. A visible feature does not guarantee that an external provider is available.",
    ],
  },
  {
    title: "Changes and contact",
    paragraphs: [
      "The project may update these terms when the product or its operating model changes. Questions about a hosted instance should go to its operator; project questions can be raised through the contact channels in the repository README.",
    ],
  },
];

function TermsAndConditions() {
  return (
    <main className="overflow-scroll p-4" style={{ height: "100vh" }}>
      <div className="container py-4">
        <div className="mx-auto" style={{ maxWidth: "860px" }}>
          {/* Reached from the sign-up form and from the marketing
              footer, and previously a dead end from both. */}
          <Link to="/" className="lightTxtClr d-inline-block mb-4">&larr; Back to SearchMirror</Link>

          <header className="mb-5">
            <h1 className="h2-md fB">Terms of Use</h1>
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

export default TermsAndConditions;
