import { Tsk } from "../../commonComponents/parts"
import { GoOverviewPageIcon } from "../../commonComponents/icons"
import { useEffect, useState } from "react"

function PropertyModel(props){
  const [data, setData] = useState([])
  const [account, setAccount] = useState("")
  useEffect(()=>{
    // setData(props.data)
    setData([])
    setAccount('')
  }, [props.data])
  // props.revokePrptyAcc()
  console.log(data, account)
    return (
        <div className="propertyMdlBxColor">
        {props.data?
        !account?
        <div id="slide" className="my-3 overflow-auto" style={{'maxHeight':'250px', 'color':'var(--accent)'}}>
        {props.data.hasOwnProperty('accountSummaries')?
          props.data.accountSummaries.map((item, index) => (
          <ul className="px-4" key={index}>
              <div className="py-3 propertyBrdrColor align-items-center cursorP px-3 d-flex justify-content-between rounded fM f16x" onClick={(e)=>{setAccount(item.displayName); setData(item)}}><span className="fM">Account: {item.displayName}</span><span className="propertySpArrow"><GoOverviewPageIcon/></span></div>
          </ul>
        ))
        :
        <div className="text-center" style={{color:'var(--ink-3)'}}>No Account</div>
        }
        </div>
        :
        <div className="propertyCount my-3 overflow-auto" style={{'maxHeight':'250px'}}>
          {account?
            data.propertySummaries.map((propertyItem, propertyIndex) => (
              <div key={propertyItem.property}>
              <ul className="px-4" key={propertyIndex}>
              <div onClick={()=>props.handlePropertySelect(propertyItem)} className="rounded cursorP propertyBrdrColor my-2 py-3 px-3 d-flex justify-content-between prBox f15x" key={propertyIndex}>
                <div className="text-truncate maxW250x">{propertyItem.displayName}</div>
                <div className="d-flex gap-3 align-items-center">
                  <span>{propertyItem.property}</span>
                </div>
              </div>
              </ul>
              </div>
            ))
            :<div className="rounded propertyBrdrColor my-2 py-3 px-3 d-flex justify-content-between">
              <div style={{color:'var(--ink-3)'}}>No Property</div>
            </div>
          }
          <div className="d-flex px-4 cursorP">
            <span className="propertySpArrow">
              <GoOverviewPageIcon className={'icon'}/>
            </span>
            <span className="lightTxtClr" onClick={(e)=>{setData([]); setAccount('')}}>Back to accounts</span>
          </div>
        </div>
        :
        <div className="my-4" style={{'minHeight':'250px'}}>
            <div className="loading" style={{position:'absolute', top:'160px', left:'250px'}}></div>
        </div>
        }
        </div>
    )
}
export default PropertyModel