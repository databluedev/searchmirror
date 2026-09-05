import Cookies from 'universal-cookie';
import axios from 'axios';
import { Tooltip, Zoom } from "@mui/material";
import { FillArrow, SFRatingIcon } from "./commonComponents/icons";

export const cookiesremove = () => {
	const cookies = new Cookies();  
	cookies.remove('session_userid', { path: '/' });
	cookies.remove('session_token', { path: '/' });
	cookies.remove('ckgrp', { path: '/' });
	cookies.remove('activegrp', { path: '/' });
	cookies.remove('session_username', { path: '/' }); 
	cookies.remove('session_usermail', { path: '/' });  
	localStorage.clear();
}

export const openLiveGoogleSerp = async (keywordId) => {
   const cookies = new Cookies();
   const userid = cookies.get("session_userid");
   const grpid = cookies.get("activegrp");
   const token = cookies.get("session_token");
   if (!userid || !grpid || !token || !keywordId) {
      throw new Error("Missing SERP context");
   }

   const response = await axios.post(global.apiurl + "/gresultpage", {
      userid,
      grpid,
      kwid: keywordId,
   }, {
      headers: { Authorization: "Token " + token },
   });
   const data = response.data || {};
   if (data.status !== "true" || data.mode !== "live" || !data.url) {
      throw new Error(data.message || "Live Google results are unavailable");
   }

   const url = new URL(data.url);
   if (url.protocol !== "https:" || url.hostname !== "www.google.com") {
      throw new Error("Unexpected SERP destination");
   }
   window.open(url.toString(), "_blank", "noopener,noreferrer");
   return url.toString();
}

export const searchRegionValue = (region) => (
   region ? `${region.Rcd} ${region.RN} (${region.Rcnt})` : ""
);

export const findSearchRegion = (regions = [], value = "") => (
   regions.find((item) => searchRegionValue(item) === value) || null
);

export const normalizeSearchDefaults = (
   regions = [],
   languages = [],
   defaultRegion = "",
   preferredCode = "",
) => {
   const defaultCode = String(defaultRegion || "").split("|")[0];
   const selectedCode = preferredCode || defaultCode;
   const selectedRegion = (
      regions.find((item) => item.Rcd === selectedCode) || regions[0] || null
   );
   const selectedLanguage = (
      languages.find((item) => item.LN === "English") || languages[0] || null
   );

   return {
      region: selectedRegion ? selectedRegion.RN : "",
      isocode: selectedRegion ? selectedRegion.Rcd : "",
      countryname: selectedRegion ? selectedRegion.Rcnt : "",
      language: selectedLanguage ? selectedLanguage.LN : "",
   };
}

export const fstLtrCapitalfun = (val) => {
   return typeof(val) === "string" ? val.charAt(0).toUpperCase() + val.slice(1).toLowerCase() : val;
}

export const capitalfun = (val) => {
   return typeof(val) === "string" ? val.toUpperCase() : val;
}

export const lowercasefun = (val) => {
   return typeof(val) === "string" ? val.toLowerCase() : val;
}

export const url_to_host = (url) => {
   // const domain = (new URL(url)).hostname.replace('www.','');
   // return (new URL(url)).hostname
   try {
      var domain = (new URL(url)).hostname;
   } catch (_) {
      domain = url;
   }

   return domain
}

export const Arrow = ({ status, type, y_sts, tooltip }) => {
   if(y_sts < 0){
      status = ""
   }else if(type=== "Declined"){
      status = status > 0 ? "down" : status < 0 ? "up" : ""
   }else{
      status = status > 0 ? "up" : status < 0 ? "down" : ""
   }

   return (
      (status !== "" && tooltip === false) ?
         <span className={"d-flex arrow "+ (status === "down" ? "red" : "green")}>
            <FillArrow />
         </span>
      : status !== "" ?
         <Tooltip title={"Yesterday it was "+y_sts} TransitionComponent={Zoom} placement="top" classes={{ tooltip: "Tltpsmall" }}>
            <span className={"d-flex arrow "+ (status === "down" ? "red" : "green")}>
               <FillArrow />
            </span>
         </Tooltip>
      : null
   );
};

/* Get Date */
export const getdate = (date) => {  
    const monthShortNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun","Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]; 
    var dat = new Date(date)
    var mon = dat.getMonth();
    var m = monthShortNames[mon];   
    var d = dat.getDate() < 10 ? '0' + dat.getDate() : dat.getDate(); 
    return m+' '+d;   
}

/* Get Full Date */
export const getfulldate = (date) => {  
    const monthShortNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun","Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]; 
    var dat = new Date(date)
    var mon = dat.getMonth();
    var year = dat.getFullYear();
    var m = monthShortNames[mon];   
    var d = dat.getDate() < 10 ? '0' + dat.getDate() : dat.getDate(); 
    return m+' '+d+' '+year;   
}

/*List table url in domain remove use*/
export const removeUrlAttr = (url) => {
    // url = url.replace(/^(?:https?:\/\/)?(?:www\.)?/i, "").split('/')[0]; 
    // return url.match(/[^\].]*\.[^.]*$/)[0];   
    return url.replace("www.", "");
}

/*List table url in domain remove use*/
export const convertSiteUrl = (url) => {
    var pat = /^https?:\/\//i;
    if (pat.test(url))  {
        var siteUrl = new URL(url);
        var urlPathName = siteUrl.pathname.trim();
        var urlSearchhName = siteUrl.search.trim();

        var convertUrlpath = (urlPathName === "") ? removeUrlAttr(siteUrl.host.trim()) : (siteUrl.pathname.trim() === "/" ? removeUrlAttr(siteUrl.host.trim()) : siteUrl.pathname.trim());   
        var convertUrl = urlSearchhName === "" ?  convertUrlpath : convertUrlpath + urlSearchhName
        return convertUrl;
    }  else {
        return url; 
    }
}

/// VOLUME CONVERSION
export function VolTool({value, d = 1}) { 
   if (value >= 0) {
      var volume = value;
      var suffix = "";

      if (Math.abs(Number(value)) >= 1.0e+12) {
         volume = (Number(value) / 1.0e+12)
         suffix = "T" 
      } else if (Math.abs(Number(value)) >= 1.0e+9) {
         volume = (Number(value) / 1.0e+9)
         suffix = "B"
      } else if (Math.abs(Number(value)) >= 1.0e+6) {
         volume = (Number(value) / 1.0e+6)
         suffix = "M"
      } else if (Math.abs(Number(value)) >= 1.0e+3) {
         volume = (Number(value) / 1.0e+3)
         suffix = "K"
      } else {
         volume = (Number(value))
      }

      return value !== volume ?
        (d === 1 ?
          parseFloat((Math.floor(volume * Math.pow(10, d)) / Math.pow(10, d)).toFixed(d)).toString() + suffix
        :
          (Math.floor(volume * Math.pow(10, d)) / Math.pow(10, d)).toFixed(d) + suffix
        ) 
      : 
         Math.abs(Number(value))
   } else {
      return (
         <span className="txt-color-light">
            {"NA"}
         </span>
      ); 
   } 
}; 

//
export const SFRatingClrIcon = ({value}) => {
   var color = "currentColor"
   if (parseFloat(value) >= 4){
      color="#43CF62"
   }else if (parseFloat(value) >= 2){
      color="#CFAE43"
   }else if (parseFloat(value) !== 0 && parseFloat(value) < 2){
      color="#CF4343"
   }
   return <SFRatingIcon color={color} />;
}


export const Logout = () => {
   const cookies = new Cookies(); 
   const userid = cookies.get('session_userid');

   const data = {
      'userid': userid,
   };

   axios.post(global.apiurl + '/last_logout', data, {
      headers: {'Authorization': global.token}
   }).then(response => {
      return response.data;
   }).then(res => {
      if(res.status !== "true"){
         // console.log(res.message);
      } else {
         cookiesremove();
         // history.push("/login")
         window.location.reload(); 
      }
   }).catch((error) => {
      // history.push("/")
      window.location.reload(); 
   }); 
}

export const convertToK=(number) =>{
   if (typeof number !== 'number') {
       throw new Error('Input must be a number');
   }
   
   if (number < 1000) {
       return number.toString();
   }
   
   let result = (number / 1000).toFixed(1);
   
   if (result.endsWith('.0')) {
       result = result.slice(0, -2);
   }
   
   return `${result}k`;
}
