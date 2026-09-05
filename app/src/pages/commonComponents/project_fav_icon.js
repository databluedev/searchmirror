import React, { useState, useEffect,  } from "react";
import Cookies from 'universal-cookie';

import SiteMark from "./site_mark";

function ProjectFavIcon(props) {

   	const [basedata, setbasedata] = useState({});

   	useEffect (() => {
   	   const cookies = new Cookies();
   	   var grpid = cookies.get('activegrp')
   	   var apidata = {}
   	   if(props.projectList.length > 0){
   	      apidata = props.projectList.filter(item => item.GY === parseInt(grpid))[0]
   	      if (typeof(apidata) !== "object" || apidata.length === 0){
   	         apidata = props.projectList[0]
   	      }
   	      cookies.set('activegrp', apidata.GY, { path: '/', maxAge: global.cookiesexpire });
   	   }

   	   setbasedata(apidata);
   	   // console.log("apidata", apidata);
		// eslint-disable-next-line react-hooks/exhaustive-deps
   	},[props.projectList]);
   
   	return (
      <>
         <div className="whiteBox projectFavIcon d-flex align-items-center justify-content-center">
            <SiteMark domain={basedata.DN} className="img-br" />
         </div>
      </>
   )
}

export default ProjectFavIcon;