import "./landing.css";
import { Byok } from "./components/sections/byok";
import { ContentTools } from "./components/sections/content-tools";
import { Features } from "./components/sections/features";
import { GeoCitations } from "./components/sections/geo-citations";
import { Hero } from "./components/sections/hero";
import { Hosting } from "./components/sections/hosting";
import { HowItWorks } from "./components/sections/how-it-works";
import { SiteFooter } from "./components/site-footer";
import { SiteHeader } from "./components/site-header";
function LandingPage() {
  return <div className="landing-page">
      <a
    href="#main"
    className="sr-only rounded-pill focus-visible:not-sr-only focus-visible:fixed focus-visible:left-4 focus-visible:top-4 focus-visible:z-[60] focus-visible:bg-ink focus-visible:px-5 focus-visible:py-2.5 focus-visible:text-[13.5px] focus-visible:font-semibold focus-visible:text-white"
  >
        Skip to content
      </a>

      <SiteHeader />

      <main id="main">
        <Hero />
        <Byok />
        <Features />
        <GeoCitations />
        <ContentTools />
        <HowItWorks />
        <Hosting />
      </main>

      <SiteFooter />
    </div>;
}
export {
  LandingPage as default
};
