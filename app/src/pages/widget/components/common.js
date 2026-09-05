// The last survivor of the widget grid this directory used to hold. It stays
// because pages/reports/index.js imports GetDomain from here; nothing on the
// dashboard uses it any more. It belongs in utils/domain.js, which is outside
// this lane.
export function GetDomain({url}) {
   if (typeof url !== 'undefined') { 
      try { 
         var urll = url.trim();
         // Stored domains are inconsistent: some carry a scheme ("https://ahrefs.com"),
         // some do not ("semrush.com"). new URL() throws on the second form, which
         // is why bare domains rendered as "Domain not available".
         if (!/^[a-zA-Z][a-zA-Z0-9+.-]*:\/\//.test(urll)) {
            urll = "https://" + urll;
         }
         const { hostname } = new URL(urll);
         return hostname.replace('www.','');
      } catch(err) {
         return "Domain not available"; 
      }
   }
   return "";
};