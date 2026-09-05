// import content from './pages/contentComponents/content.json';
import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './tailwind.css';
import reportWebVitals from './reportWebVitals';

import moment from 'moment';
moment.suppressDeprecationWarnings = true;

global.PageTopLoader = null;
global.keywordsecret = 51739;
global.cookiesexpire = 2592000;

// Empty, not a hardcoded host: with no VITE_API_URL every request is made
// against the app's own origin, which is what a single-origin self-host wants.
// The old default was https://api.tracker.example -- a domain that does not
// resolve, so an unconfigured build failed against someone else's name rather
// than its own. docker-compose.yml sets VITE_API_URL for both the dev server
// and the image build.
global.iconurl = import.meta.env.VITE_API_URL || '';
global.apiurl = import.meta.env.VITE_API_URL || '';

// Shipped to every browser -- a shared bearer in frontend code is public by
// definition. Plumbed from the build env so no token sits in the repo; the
// real fix is a per-user token issued at login.
global.token = import.meta.env.VITE_ENGINE_TOKEN || ''

global.clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';   // social login; blank => the Google button is hidden

global.designations = ['Founder', 'Chief Executive Officer', 'Chief Marketing Officer', 'Head of Marketing', 'Marketing Analyst', 'SEO Analyst', 'Marketing Consultant', 'Marketing Manager', 'Marketing Agency'];

// Outbound links.
//
// These were twelve hardcoded addresses on tracker.example, a domain that does
// not resolve, so every one of them was a dead link -- and they carried the old
// vendor's shape with them: a hosted feedback board, an affiliate programme, a
// rate-us page. Seven of them (Rate us, Feature request, Roadmap, Affiliate,
// Terms, Report a bug, and the app's own siteurl) are read by nothing at all
// any more and are gone.
//
// The five that survive are read by "know more" links beside SERP features and
// cannibalisation, and by Contact us on the account page. There is no
// SearchMirror marketing site to point them at, so they default to empty and
// the link is not rendered at all -- see utils/external_link.js. A self-hosted
// operator who does have somewhere to send people sets the env vars.
global.brndcnqsturl = import.meta.env.VITE_DOC_BRAND_CONQUEST_URL || '';
global.cannbltnurl = import.meta.env.VITE_DOC_CANNIBALIZATION_URL || '';
global.featursnipt = import.meta.env.VITE_DOC_FEATURED_SNIPPET_URL || '';
global.contactUs = import.meta.env.VITE_CONTACT_URL || '';
global.blogUrl = import.meta.env.VITE_BLOG_URL || '';

// Content Audit 
global.gscClientId = import.meta.env.VITE_GSC_CLIENT_ID || '';
// NOTE: an OAuth client secret in browser code is public to every visitor by
// definition. This is plumbed from the build env only so no key sits in the
// repo -- the token exchange still belongs on the server before GSC ships.
global.gscSecret = import.meta.env.VITE_GSC_SECRET || '';
// Google rejects the exchange unless this is byte-identical to the address the
// browser is on and to the entry in the OAuth client. It was pinned to
// app.tracker.example with no override, which is a guaranteed redirect_uri
// mismatch on every self-hosted install. The app's own origin is the only value
// that can be right by construction.
global.gscRedirectURL = import.meta.env.VITE_GSC_REDIRECT_URL || window.location.origin;
// ga analytics
global.gaClientId = import.meta.env.VITE_GSC_CLIENT_ID || ''
global.gaSecretId = import.meta.env.VITE_GSC_SECRET || ''
// React 18 root API.
const root = createRoot(document.getElementById('root'));
root.render(<App />);

reportWebVitals();
