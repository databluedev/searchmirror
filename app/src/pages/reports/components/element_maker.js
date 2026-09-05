import React, { useEffect, useState } from "react"
import { AppIconButton, Input, Rsk } from "../../commonComponents/parts"
import Cookies from "universal-cookie"
import axios from "axios"
import { toast } from "react-toastify"

function ElementMaker(props){
  const [data, setData] = useState({
    text: '',
    show: false,
    updtEl: "",
    flag:0
  })

  const {text, show, updtEl, flag} = data

  // setState from a useMemo is a render-phase side effect; the same job
  // belongs in an effect.
  useEffect(()=>{
    setData(data=>({...data, text:props.value, updtEl:props.value}))
  }, [props.value])

  const handleSubmit=()=>{
    setData(data=>({...data, show:false, flag:0}))
    if (flag!==1){
      return
    }

    const cookies = new Cookies();
    const usertoken = cookies.get('session_token');
    const userid = cookies.get('session_userid');
    const grpid = cookies.get('activegrp');
    // The backend matches on the CURRENT stored name. props.value is the name
    // the parent last fetched, so a second rename in the same session sent the
    // original name and was refused with "Something went wrong". updtEl is what
    // this component knows is stored right now.
    const payload={'userid':userid, 'grpid':grpid, 'shtNmber':props.sheetNumber, 'shtNme':updtEl, 'updtShtNme':text}
    axios.post(global.apiurl + '/sheet_update', payload, {
      headers: {'Authorization':'Token '+usertoken}
    }).then(response=>{
      return response.data
    }).then(res=>{
      if (res.st===0){
        toast.error(res.dt || "The report could not be renamed.")
        setData(data=>({...data, text:updtEl}))
      }else{
        toast.success(res.dt || "Report renamed.")
        setData(data=>({...data, updtEl:text}))
      }
    }).catch(error=>{
      const status = error && error.response && error.response.status
      toast.error(status === 403
        ? "You do not have permission to rename reports."
        : "The report could not be renamed. Please try again.")
      setData(data=>({...data, text:updtEl}))
    })
  }

  const handleClose=(e)=>{
    setData(data=>({...data, text:updtEl, show:false}))
  }

  return(
    <>
    <span>
          {
            // Use JavaScript's ternary operator to specify <span>'s inner content
            show ? (
              <div className="d-flex">
              <Input 
              type='text'
              value={text}
              onchange={e=>setData(data=>({...data, text:e.target.value, show:true, flag:1}))}
              />
              <AppIconButton
                aria-label="Save report name"
                Icon={<svg fill="currentColor" xmlns="http://www.w3.org/2000/svg"  viewBox="0 0 30 30" width="20px" height="20px"><path d="M 26.980469 5.9902344 A 1.0001 1.0001 0 0 0 26.292969 6.2929688 L 11 21.585938 L 4.7070312 15.292969 A 1.0001 1.0001 0 1 0 3.2929688 16.707031 L 10.292969 23.707031 A 1.0001 1.0001 0 0 0 11.707031 23.707031 L 27.707031 7.7070312 A 1.0001 1.0001 0 0 0 26.980469 5.9902344 z"/></svg>}
                onclick={handleSubmit}
                class="border rounded bg-white m-l5 p-2"
              />
              <AppIconButton
                aria-label="Cancel rename"
                Icon={<svg fill="currentColor" xmlns="http://www.w3.org/2000/svg"  viewBox="0 0 50 50" width="20px" height="20px"><path d="M 7.71875 6.28125 L 6.28125 7.71875 L 23.5625 25 L 6.28125 42.28125 L 7.71875 43.71875 L 25 26.4375 L 42.28125 43.71875 L 43.71875 42.28125 L 26.4375 25 L 43.71875 7.71875 L 42.28125 6.28125 L 25 23.5625 Z"/></svg>}
                onclick={handleClose}
                class="border rounded bg-white m-l5 p-2"
              />

              </div>
            ) : (
              <>
              {text==='DEMO'?
              <Rsk width={200} height={30}/>
              :
              <>
              <span
                onDoubleClick={e=>setData(data=>({...data, show:true}))}
                style={{
                  display: "inline-block",
                  height: "25px",
                  // minWidth: "300px",
                }}
              >
                {text}
              </span>
                
            
              <button type="button" className="reportRenameBtn" aria-label={"Rename "+text} title="Rename report" onClick={()=>setData(data=>({...data, show:true}))}>
              <svg xmlns="http://www.w3.org/2000/svg"  viewBox="0 0 24 24" width="20px" height="20px" fill="currentColor">
              <path d="M 18.414062 2 C 18.158062 2 17.902031 2.0979687 17.707031 2.2929688 L 15.707031 4.2929688 L 14.292969 5.7070312 L 3 17 L 3 21 L 7 21 L 21.707031 6.2929688 C 22.098031 5.9019687 22.098031 5.2689063 21.707031 4.8789062 L 19.121094 2.2929688 C 18.926094 2.0979687 18.670063 2 18.414062 2 z M 18.414062 4.4140625 L 19.585938 5.5859375 L 18.292969 6.8789062 L 17.121094 5.7070312 L 18.414062 4.4140625 z M 15.707031 7.1210938 L 16.878906 8.2929688 L 6.171875 19 L 5 19 L 5 17.828125 L 15.707031 7.1210938 z"/>
              </svg>
              </button>
              </>
              }
              </>
            )
          }
    </span>
 </>
)}
export default React.memo(ElementMaker)