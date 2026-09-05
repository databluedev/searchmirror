import React from "react";

//SERP Rank
export function ViewIcon({...props }) {
   return (
      <svg 
        className={props.className}
        xmlns="http://www.w3.org/2000/svg" 
        width={ props.width || "16" }
        height={ props.height || "16.545"} 
        viewBox="0 0 14 9.545" 
      >
        <g id="_001-visibility" data-name="001-visibility" transform="translate(0 -74.667)">
          <g id="Group_5367" data-name="Group 5367" transform="translate(0 74.667)">
            <g id="Group_5366" data-name="Group 5366" transform="translate(0 0)">
              <path 
                id="Path_2485" 
                data-name="Path 2485" 
                d="M172.576,170.667a1.909,1.909,0,1,0,1.909,1.909A1.911,1.911,0,0,0,172.576,170.667Z" 
                transform="translate(-165.576 -167.803)" 
                fill={ props.color || "currentColor"}
              />
              <path 
                id="Path_2486" 
                data-name="Path 2486" 
                d="M7,74.667A7.526,7.526,0,0,0,0,79.44a7.52,7.52,0,0,0,14,0A7.523,7.523,0,0,0,7,74.667Zm0,7.955a3.182,3.182,0,1,1,3.182-3.182A3.183,3.183,0,0,1,7,82.622Z" 
                transform="translate(0 -74.667)" 
                fill={ props.color || "currentColor"}
              />
            </g>
          </g>
        </g>
      </svg> 
   );
}

export function DeleteIcon ({...props }) {
  return (
    <svg
      className={props.className} 
      xmlns="http://www.w3.org/2000/svg"
      width={ props.width || "15.2"}
      height={ props.height || "15"}
      viewBox="0 0 16.2 18"
      style={props.style}
    >
      <path
        id="Path_491"
        data-name="Path 491"
        d="M9.3,16.4a.9.9,0,0,0,.9-.9V10.1a.9.9,0,1,0-1.8,0v5.4A.9.9,0,0,0,9.3,16.4Zm9-10.8H14.7V4.7A2.7,2.7,0,0,0,12,2H10.2A2.7,2.7,0,0,0,7.5,4.7v.9H3.9a.9.9,0,1,0,0,1.8h.9v9.9A2.7,2.7,0,0,0,7.5,20h7.2a2.7,2.7,0,0,0,2.7-2.7V7.4h.9a.9.9,0,0,0,0-1.8Zm-9-.9a.9.9,0,0,1,.9-.9H12a.9.9,0,0,1,.9.9v.9H9.3Zm6.3,12.6a.9.9,0,0,1-.9.9H7.5a.9.9,0,0,1-.9-.9V7.4h9Zm-2.7-.9a.9.9,0,0,0,.9-.9V10.1a.9.9,0,1,0-1.8,0v5.4A.9.9,0,0,0,12.9,16.4Z"
        transform="translate(-3 -2)"
        fill={ props.color || "currentColor"} 
      />
    </svg>
  );
}