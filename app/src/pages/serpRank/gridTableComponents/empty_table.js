import React from "react";
import {fstLtrCapitalfun} from "../../common_fun";   


function EmptyTable({ ...props }) {

   const label = fstLtrCapitalfun(props.grdtbltype);

   return (
      <section className="gd-table">
         <div className="gd-table-header">
            <div className="header d-flex justify-content-between align-items-start gap-3">
              <div className="gdHead__id">
                <div className="gdHead__label">{ label }</div>
                <div className="gdHead__name">No results</div>
                <div className="gdHead__count">0 keywords</div>
              </div>
            </div>
         </div>

         <div className="gd-table-empty text-center">
            <p className="ls-table-empty-body">Nothing matches this view. Try another search, or a different grouping.</p>
         </div>
      </section>
   )
}

export default EmptyTable;
