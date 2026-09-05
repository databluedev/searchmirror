import React from "react";
import { Link } from "react-router-dom";
import "../style.scss";
import LogoSymbol from "../../../assets/images/logo-dark.png";

function WelcomeLayout({ children }) {
  return (
    <div className="authShell">
      <main className="authMain">
        <div className="authFrame">
          {/* The lockup is a LINK home. It was an image and a <strong>, which
              made sign-in, sign-up, password reset, registration and the legal
              pages all dead ends: the marketing site links into them and
              nothing linked back, at any width. Clicking the logo to get out is
              the convention people already try. */}
          <Link to="/" className="authBrand" aria-label="SearchMirror home">
            <img src={LogoSymbol} alt="" width={32} height={32} />
            <div>
              {/* The same logotype the app rail and the marketing header set:
                  "Search" drops a weight and a tone so the pair reads as a
                  designed mark. Crossing login into the product is continuous
                  only if all three are the same lockup, not just the same face. */}
              <strong className="authBrand__word">
                <span className="authBrand__s">Search</span>Mirror
              </strong>
              <span>Powered by DataBlue</span>
            </div>
          </Link>

          {children}

          <p className="authFoot">
            Open source rank tracking with your own DataBlue key.
          </p>
        </div>
      </main>
    </div>
  );
}

export default WelcomeLayout;
